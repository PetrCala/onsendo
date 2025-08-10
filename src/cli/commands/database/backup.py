"""
backup.py

Backup the current database to a specified location.
"""

import argparse
import os
import shutil
from datetime import datetime
from loguru import logger
from src.const import CONST


def backup_db(args: argparse.Namespace) -> None:
    """
    Backup the current database to the specified folder.
    """
    database_path = CONST.DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(database_path):
        logger.error(
            f"Database file {database_path} does not exist! Run `database init` first to create it."
        )
        return

    # Create backup folder if it doesn't exist
    backup_folder = args.backup_folder
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
