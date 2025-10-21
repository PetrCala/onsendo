"""migrate_to_envs.py

One-time migration utility to convert single-database setup to multi-environment setup.

This command copies the current onsen.db to both onsen.prod.db and onsen.dev.db,
allowing users to transition from the legacy single-database structure to the
new environment-based system.
"""

import argparse
import os
import shutil
from datetime import datetime
from loguru import logger

from src.paths import PATHS
from src.config import get_database_path, DatabaseEnvironment


def create_backup(source_path: str) -> str:
    """Create a timestamped backup of the source database.

    Args:
        source_path: Path to database file to backup

    Returns:
        Path to backup file

    Raises:
        FileNotFoundError: If source database doesn't exist
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source database not found: {source_path}")

    # Create backup directory
    backup_dir = PATHS.ARTIFACTS_DB_BACKUPS_DIR
    os.makedirs(backup_dir, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"onsen_pre_migration_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    # Copy database
    shutil.copy2(source_path, backup_path)
    logger.info(f"Created backup: {backup_path}")

    return backup_path


def verify_database(path: str) -> bool:
    """Verify database file integrity.

    Args:
        path: Path to database file

    Returns:
        True if database appears valid
    """
    if not os.path.exists(path):
        return False

    # Check file size (should be non-zero)
    size = os.path.getsize(path)
    if size == 0:
        logger.error(f"Database file is empty: {path}")
        return False

    # Check SQLite header (first 16 bytes should be "SQLite format 3\x00")
    with open(path, "rb") as f:
        header = f.read(16)
        if not header.startswith(b"SQLite format 3"):
            logger.error(f"Invalid SQLite header in: {path}")
            return False

    logger.debug(f"Database verification passed: {path} ({size} bytes)")
    return True


def migrate_to_environments(args: argparse.Namespace) -> None:
    """Migrate from single database to multi-environment setup.

    Copies the current onsen.db to both onsen.prod.db and onsen.dev.db.

    Args:
        args: Command-line arguments with optional --force flag
    """
    print("\n" + "=" * 70)
    print("DATABASE ENVIRONMENT MIGRATION")
    print("=" * 70)
    print("\nThis command will migrate your single database to the new environment system.")
    print("\nCurrent setup:")
    print(f"  • Single database: {PATHS.DB_PATH}")
    print("\nNew setup:")
    print(f"  • Production database: {get_database_path(DatabaseEnvironment.PROD)}")
    print(f"  • Development database: {get_database_path(DatabaseEnvironment.DEV)}")
    print("\nThis migration will:")
    print("  1. Create a backup of your current database")
    print("  2. Copy your database → onsen.prod.db (production)")
    print("  3. Copy your database → onsen.dev.db (development)")
    print("  4. Verify integrity of both copies")
    print("\n⚠️  Your original database will NOT be deleted.")
    print("=" * 70)

    # Check if source database exists
    source_db = PATHS.DB_PATH
    if not os.path.exists(source_db):
        logger.error(f"Source database not found: {source_db}")
        logger.info("Nothing to migrate. You can initialize new environments with:")
        logger.info("  poetry run onsendo system init-db")
        return

    # Check if target databases already exist
    prod_db = get_database_path(DatabaseEnvironment.PROD)
    dev_db = get_database_path(DatabaseEnvironment.DEV)

    if os.path.exists(prod_db) or os.path.exists(dev_db):
        if not hasattr(args, "force") or not args.force:
            logger.error("\nTarget database(s) already exist:")
            if os.path.exists(prod_db):
                logger.error(f"  • {prod_db}")
            if os.path.exists(dev_db):
                logger.error(f"  • {dev_db}")
            logger.error("\nUse --force to overwrite existing databases.")
            return

        logger.warning("--force flag set, will overwrite existing databases")

    # Get user confirmation
    if not hasattr(args, "yes") or not args.yes:
        response = input("\nProceed with migration? [yes/no]: ")  # pylint: disable=bad-builtin
        if response.strip().lower() != "yes":
            logger.info("Migration cancelled by user")
            return

    print("\n" + "-" * 70)
    print("STEP 1: Creating backup...")
    print("-" * 70)

    try:
        backup_path = create_backup(source_db)
        print(f"✓ Backup created: {backup_path}")
    except Exception as exc:
        logger.error(f"Failed to create backup: {exc}")
        return

    print("\n" + "-" * 70)
    print("STEP 2: Copying to production database...")
    print("-" * 70)

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(prod_db), exist_ok=True)

        # Copy to production
        shutil.copy2(source_db, prod_db)
        print(f"✓ Copied to: {prod_db}")

        # Verify
        if not verify_database(prod_db):
            raise ValueError("Production database verification failed")
        print("✓ Production database verified")
    except Exception as exc:
        logger.error(f"Failed to create production database: {exc}")
        return

    print("\n" + "-" * 70)
    print("STEP 3: Copying to development database...")
    print("-" * 70)

    try:
        # Copy to development
        shutil.copy2(source_db, dev_db)
        print(f"✓ Copied to: {dev_db}")

        # Verify
        if not verify_database(dev_db):
            raise ValueError("Development database verification failed")
        print("✓ Development database verified")
    except Exception as exc:
        logger.error(f"Failed to create development database: {exc}")
        return

    # Success!
    print("\n" + "=" * 70)
    print("✓ MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nYour databases:")
    print(f"  • Production: {prod_db}")
    print(f"  • Development: {dev_db}")
    print(f"  • Backup: {backup_path}")
    print(f"  • Original: {source_db} (unchanged)")
    print("\nNext steps:")
    print("  • Development database is now the default for all commands")
    print("  • Use --env prod flag to access production database")
    print("  • Set ONSENDO_ENV=prod for session-scoped production access")
    print("\nExamples:")
    print("  poetry run onsendo visit list              # Uses dev")
    print("  poetry run onsendo visit list --env prod   # Uses prod")
    print("=" * 70)

    logger.success("Database migration completed successfully!")
