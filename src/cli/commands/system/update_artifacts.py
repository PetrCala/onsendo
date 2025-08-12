"""
update_artifacts.py

Update database artifacts in the artifacts/db folder.
These are static files for presentation to users of this project.
"""

import argparse
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict
from loguru import logger
from src.db.conn import get_db
from src.db.import_data import import_onsen_data
from src.const import CONST
from src.paths import PATHS


class ArtifactGenerator:
    """Handles generation of database artifacts without affecting the current database."""

    def __init__(self):
        self.artifacts_dir = Path(PATHS.ARTIFACTS_DB_DIR)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _backup_current_db(self) -> str:
        """Create a backup of the current database if it exists."""
        current_db_path = CONST.DATABASE_URL.replace("sqlite:///", "")
        if not os.path.exists(current_db_path):
            return ""

        backup_path = tempfile.mktemp(suffix=".db")
        shutil.copy2(current_db_path, backup_path)
        logger.info(f"Backed up current database to: {backup_path}")
        return backup_path

    def _restore_current_db(self, backup_path: str) -> None:
        """Restore the current database from backup."""
        if not backup_path or not os.path.exists(backup_path):
            return

        current_db_path = CONST.DATABASE_URL.replace("sqlite:///", "")
        shutil.copy2(backup_path, current_db_path)
        os.unlink(backup_path)
        logger.info("Restored current database from backup")

    def _create_empty_database(self, target_path: str) -> None:
        """Create an empty database with all tables at the specified path."""
        from sqlalchemy import create_engine
        from src.db.models import Base

        # Create engine for the target path
        target_url = f"sqlite:///{target_path}"
        engine = create_engine(target_url)
        Base.metadata.create_all(bind=engine)
        logger.info(f"Created empty database at: {target_path}")

    def _fill_database_with_scraped_data(
        self, target_path: str, json_path: str
    ) -> None:
        """Fill a database with scraped onsen data."""
        target_url = f"sqlite:///{target_path}"

        with get_db(url=target_url) as db:
            summary = import_onsen_data(db, json_path)
            logger.info(
                f"Filled database with scraped data. "
                f"Inserted={summary['inserted']}, "
                f"Updated={summary['updated']}, "
                f"Skipped={summary['skipped']}"
            )

    def _add_locations_from_artifact(self, target_path: str) -> None:
        """Add locations from a locations artifact file to the database."""
        import json
        from sqlalchemy import create_engine
        from src.db.models import Location

        locations_file = Path(PATHS.ARTIFACTS_DIR) / "locations" / "locations.json"

        if not locations_file.exists():
            logger.warning(
                "No locations artifact file found, skipping location addition"
            )
            return

        try:
            with open(locations_file, "r", encoding="utf-8") as f:
                locations_data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read locations file: {e}")
            return

        locations = locations_data.get("locations", [])
        if not locations:
            logger.info("No locations found in artifact file")
            return

        target_url = f"sqlite:///{target_path}"
        engine = create_engine(target_url)

        added_count = 0
        with engine.connect() as conn:
            for location_data in locations:
                try:
                    # Check if location already exists by name
                    existing = conn.execute(
                        Location.__table__.select().where(
                            Location.name == location_data["name"]
                        )
                    ).first()

                    if existing:
                        logger.debug(
                            f"Location '{location_data['name']}' already exists, skipping"
                        )
                        continue

                    # Insert new location
                    conn.execute(
                        Location.__table__.insert(),
                        {
                            "name": location_data["name"],
                            "latitude": location_data["latitude"],
                            "longitude": location_data["longitude"],
                            "description": location_data.get("description", ""),
                        },
                    )
                    added_count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to add location '{location_data.get('name', 'Unknown')}': {e}"
                    )
                    continue

            conn.commit()

        logger.info(f"Added {added_count} locations from artifact file")

    def _find_latest_scraped_data(self) -> str:
        """Find the latest scraped onsen data file."""
        scraping_dir = Path(PATHS.ARTIFACTS_DIR) / "scraping"

        if not scraping_dir.exists():
            raise FileNotFoundError("No artifacts/scraping directory found")

        # Search for files containing 'scraped_onsen_data' in their name
        pattern = "**/*scraped_onsen_data*"
        matching_files = list(scraping_dir.glob(pattern))

        # Filter to only include JSON files and sort by modification time (newest first)
        json_files = [f for f in matching_files if f.suffix.lower() == ".json"]
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        if not json_files:
            raise FileNotFoundError(
                "No scraped data files found in artifacts/scraping folder"
            )

        return str(json_files[0])

    def generate_onsen_empty_db(self) -> str:
        """Generate onsen_empty.db artifact."""
        artifact_path = Path(PATHS.ARTIFACTS_DB_DIR) / "onsen_empty.db"

        # Remove existing artifact if it exists
        if artifact_path.exists():
            artifact_path.unlink()

        # Create empty database
        self._create_empty_database(str(artifact_path))
        logger.info(f"Generated artifact: {artifact_path}")

        return str(artifact_path)

    def generate_onsen_no_visits_no_locations_db(self) -> str:
        """Generate onsen_no_visits_no_locations.db artifact."""
        artifact_path = Path(PATHS.ARTIFACTS_DB_DIR) / "onsen_no_visits_no_locations.db"

        # Remove existing artifact if it exists
        if artifact_path.exists():
            artifact_path.unlink()

        # Create empty database
        self._create_empty_database(str(artifact_path))

        # Find and use latest scraped data
        try:
            json_path = self._find_latest_scraped_data()
            self._fill_database_with_scraped_data(str(artifact_path), json_path)
            logger.info(f"Generated artifact: {artifact_path}")
        except FileNotFoundError as e:
            logger.warning(f"Could not fill database with scraped data: {e}")
            logger.info("Created empty database artifact instead")

        return str(artifact_path)

    def generate_onsen_with_locations_db(self) -> str:
        """Generate onsen_with_locations.db artifact - database with onsens and locations."""
        artifact_path = Path(PATHS.ARTIFACTS_DB_DIR) / "onsen_with_locations.db"

        # Remove existing artifact if it exists
        if artifact_path.exists():
            artifact_path.unlink()

        # Create empty database
        self._create_empty_database(str(artifact_path))

        # Fill with scraped data
        try:
            json_path = self._find_latest_scraped_data()
            self._fill_database_with_scraped_data(str(artifact_path), json_path)

            # Add locations from artifact (placeholder functionality)
            self._add_locations_from_artifact(str(artifact_path))

            logger.info(f"Generated artifact: {artifact_path}")
        except FileNotFoundError as e:
            logger.warning(f"Could not fill database with scraped data: {e}")
            logger.info("Created empty database artifact instead")

        return str(artifact_path)

    def generate_onsen_latest_db(self) -> str:
        """Generate onsen_latest.db artifact - copy of current database state."""
        artifact_path = Path(PATHS.ONSEN_LATEST_ARTIFACT)
        current_db_path = CONST.DATABASE_URL.replace("sqlite:///", "")

        # Remove existing artifact if it exists
        if artifact_path.exists():
            artifact_path.unlink()

        if os.path.exists(current_db_path):
            # Copy current database state
            shutil.copy2(current_db_path, str(artifact_path))
            logger.info(
                f"Generated artifact: {artifact_path} (copy of current database)"
            )
        else:
            # Create empty database if current doesn't exist
            self._create_empty_database(str(artifact_path))
            logger.info(
                f"Generated artifact: {artifact_path} (empty - no current database)"
            )

        return str(artifact_path)

    def generate_all_artifacts(self) -> Dict[str, str]:
        """Generate all database artifacts."""
        logger.info("Starting artifact generation...")

        # Backup current database
        backup_path = self._backup_current_db()

        try:
            artifacts = {}

            # Generate onsen_empty.db
            artifacts["onsen_empty.db"] = self.generate_onsen_empty_db()

            # Generate onsen_no_visits_no_locations.db
            artifacts["onsen_no_visits_no_locations.db"] = (
                self.generate_onsen_no_visits_no_locations_db()
            )

            # Generate onsen_with_locations.db
            artifacts["onsen_with_locations.db"] = (
                self.generate_onsen_with_locations_db()
            )

            # Generate onsen_latest.db
            artifacts["onsen_latest.db"] = self.generate_onsen_latest_db()

            logger.info("All artifacts generated successfully!")
            return artifacts

        finally:
            # Always restore the current database
            self._restore_current_db(backup_path)


def update_artifacts(args: argparse.Namespace) -> None:
    """
    Update database artifacts in the artifacts/db folder.
    """
    generator = ArtifactGenerator()

    try:
        artifacts = generator.generate_all_artifacts()

        logger.info("\nGenerated artifacts:")
        for name, path in artifacts.items():
            size_mb = os.path.getsize(path) / (1024 * 1024)
            logger.info(f"  {name}: {path} ({size_mb:.2f} MB)")

    except Exception as e:
        logger.error(f"Failed to generate artifacts: {e}")
        raise
