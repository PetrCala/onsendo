"""
backup.py

Backup the current database to a specified location.
"""

import argparse
import os
import shutil
from datetime import datetime
from loguru import logger
from src.lib.utils import open_folder_dialog
from src.const import CONST
from src.paths import PATHS


def backup_db(args: argparse.Namespace) -> None:
    """
    Backup the current database to the specified folder.

    By default, this command will prompt for a backup location. You can:
    - Enter a folder path directly
    - Type 'browse' to open a folder selection dialog
    - Type 'artifact' to backup to the latest artifact path (artifacts/db/onsen_latest.db)

    Use --to-latest-artifact (-a) to skip the prompt and backup directly to the artifact.
    """
    database_path = CONST.DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(database_path):
        logger.error(
            f"Database file {database_path} does not exist! Run `database init` first to create it."
        )
        return

    # Check if user wants to backup to latest artifact path
    if args.to_latest_artifact:
        backup_path = PATHS.ONSEN_LATEST_ARTIFACT
        backup_dir = os.path.dirname(backup_path)

        # Create artifacts directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)

        try:
            # Copy the database file directly to the artifact path
            shutil.copy2(database_path, backup_path)
            logger.info(
                f"Database backed up successfully to latest artifact: {backup_path}"
            )

            # Show backup size
            backup_size = os.path.getsize(backup_path)
            backup_size_mb = backup_size / (1024 * 1024)
            logger.info(f"Backup size: {backup_size_mb:.2f} MB")
            logger.info("Latest artifact has been updated!")

        except Exception as e:
            logger.error(f"Failed to backup database to latest artifact: {e}")
            return

        return

    backup_folder = args.backup_folder
    if not backup_folder and not args.no_interactive:
        print("\nBackup options:")
        print("  - Enter a folder path directly")
        print("  - Type 'browse' to open folder selection dialog")
        print("  - Type 'artifact' to backup to latest artifact (recommended)")
        print()
        user_input = input(
            "Enter backup folder path, type 'browse' to open folder selection dialog, or type 'artifact' to backup to latest artifact: "
        ).strip()

        if user_input.lower() in ["browse", "select", "dialog", "gui"]:
            logger.info("Opening folder selection dialog...")
            backup_folder = open_folder_dialog()
            if not backup_folder:
                logger.info("No folder selected or dialog cancelled.")
                return
        elif user_input.lower() in ["artifact", "artifacts", "latest"]:
            # Backup to latest artifact path
            backup_path = PATHS.ONSEN_LATEST_ARTIFACT
            backup_dir = os.path.dirname(backup_path)

            # Create artifacts directory if it doesn't exist
            os.makedirs(backup_dir, exist_ok=True)

            try:
                # Copy the database file directly to the artifact path
                shutil.copy2(database_path, backup_path)
                logger.info(
                    f"Database backed up successfully to latest artifact: {backup_path}"
                )

                # Show backup size
                backup_size = os.path.getsize(backup_path)
                backup_size_mb = backup_size / (1024 * 1024)
                logger.info(f"Backup size: {backup_size_mb:.2f} MB")
                logger.info("Latest artifact has been updated!")

            except Exception as e:
                logger.error(f"Failed to backup database to latest artifact: {e}")
                return

            return
        else:
            backup_folder = user_input

        if not backup_folder:
            logger.error("Backup folder path is required.")
            return

    if not backup_folder:
        logger.error("Backup folder path is required.")
        return

    # Create backup folder if it doesn't exist
    if not os.path.isabs(backup_folder):
        backup_folder = os.path.abspath(backup_folder)

    os.makedirs(backup_folder, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    database_name = os.path.basename(database_path)
    backup_filename = f"{database_name}.backup_{timestamp}"
    backup_path = os.path.join(backup_folder, backup_filename)

    try:
        # Copy the database file
        shutil.copy2(database_path, backup_path)
        logger.info(f"Database backed up successfully to: {backup_path}")

        # Show backup size
        backup_size = os.path.getsize(backup_path)
        backup_size_mb = backup_size / (1024 * 1024)
        logger.info(f"Backup size: {backup_size_mb:.2f} MB")

    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return
