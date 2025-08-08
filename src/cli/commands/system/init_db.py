"""
init_db.py

Initialize the database.
"""

import argparse
import os
from loguru import logger
from sqlalchemy import create_engine
from src.db.models import Base
from src.const import CONST


def init_db(args: argparse.Namespace) -> None:
    """
    Initialize the database.
    """
    if not args.force and os.path.exists(CONST.DATABASE_URL):
        logger.error("Database already exists! Use --force to overwrite.")
        return

    data_dir = os.path.dirname(CONST.DATABASE_URL.replace("sqlite:///", ""))
    os.makedirs(data_dir, exist_ok=True)

    # Create engine and tables
    engine = create_engine(CONST.DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    logger.info(f"Database initialized at: {CONST.DATABASE_URL}")
    logger.info("Tables created successfully!")
