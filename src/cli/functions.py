"""
functions.py

Functions for the CLI commands.
"""

import argparse
import os
from sqlalchemy import create_engine
from src.db.models import Base
from loguru import logger
from src.db.conn import get_db
from src.db.models import Onsen, OnsenVisit
from src.db.import_data import import_onsen_data
from src.const import CONST
from src.cli.interactive import interactive_add_visit


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


def add_onsen(args: argparse.Namespace) -> None:
    """
    Add a new onsen to the database.
    """
    with get_db(url=CONST.DATABASE_URL) as db:
        args_dict = vars(args)
        args_dict.pop("func", None)

        onsen = Onsen(**args_dict)
        db.add(onsen)
        db.commit()
        logger.info(f"Added onsen {onsen.name}")


def add_visit(args: argparse.Namespace) -> None:
    """
    Add a new onsen visit to the database.
    """
    # Check if interactive mode is requested
    if hasattr(args, "interactive") and args.interactive:
        interactive_add_visit()
        return

    with get_db(url=CONST.DATABASE_URL) as db:
        if not hasattr(args, "onsen_id") or args.onsen_id is None:
            logger.error("onsen_id is required!")
            return

        onsen = db.query(Onsen).filter(Onsen.id == args.onsen_id).first()
        if not onsen:
            logger.error(f"No onsen with id={args.onsen_id} found!")
            return

        args_dict = vars(args)
        args_dict.pop("onsen_id", None)
        args_dict.pop("func", None)  # Not a model field
        args_dict.pop("interactive", None)  # Not a model field

        # Create the visit with dynamic arguments
        visit = OnsenVisit(onsen_id=onsen.id, **args_dict)
        db.add(visit)
        db.commit()
        logger.info(f"Added a visit to onsen {onsen.name} (id={onsen.id})")
