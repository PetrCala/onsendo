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

    backup_folder = args.backup_folder
    if not backup_folder and not args.no_interactive:
        user_input = input(
            "Enter backup folder path, or type 'browse' to open folder selection dialog: "
        ).strip()

        if user_input.lower() in ["browse", "select", "dialog", "gui"]:
            logger.info("Opening folder selection dialog...")
            backup_folder = open_folder_dialog()
            if not backup_folder:
                logger.info("No folder selected or dialog cancelled.")
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
