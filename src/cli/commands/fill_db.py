"""
fill_db.py

Scrape onsen data from the web and fill the database.
"""

import argparse
import os
from loguru import logger
from src.db.conn import get_db
from src.db.import_data import import_onsen_data


def fill_db(args: argparse.Namespace) -> None:
    """
    Scrape onsen data from the web and fill the database.
    """
    file_path = os.path.join(args.database_folder, args.database_name)
    database_url = f"sqlite:///{file_path}"

    if not os.path.exists(file_path):
        logger.error(f"Database file {file_path} does not exist!")
        return

    logger.info(f"Scraping onsen data and filling database at {database_url}...")
    with get_db(url=database_url) as db:
        import_onsen_data(db)
