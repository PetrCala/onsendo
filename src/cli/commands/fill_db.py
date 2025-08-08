"""
fill_db.py

Scrape onsen data from the web and fill the database.
"""

import argparse
import os
from loguru import logger
from src.db.conn import get_db
from src.db.import_data import import_onsen_data
from src.const import CONST


def fill_db(args: argparse.Namespace) -> None:
    """
    Scrape onsen data from the web and fill the database.
    """
    database_path = CONST.DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(database_path):
        logger.error(
            f"Database file {database_path} does not exist! Run `init-db` first to create it."
        )
        return

    database_url = CONST.DATABASE_URL
    with get_db(url=database_url) as db:
        json_path = args.json_path
        if not os.path.isabs(json_path):
            json_path = os.path.abspath(json_path)
        if not os.path.exists(json_path):
            logger.error(f"JSON file not found: {json_path}")
            return
        logger.info(
            f"Importing onsen data from JSON at {json_path} into {database_url}..."
        )
        summary = import_onsen_data(db, json_path)
        logger.info(
            f"Import finished. Inserted={summary['inserted']}, Updated={summary['updated']}, Skipped={summary['skipped']}"
        )
