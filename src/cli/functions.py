"""
functions.py

Functions for the CLI commands.
"""

import argparse
from loguru import logger
from src.db.conn import get_db
from src.db.models import Onsen, OnsenVisit
from src.const import CONST


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
    with get_db(url=CONST.DATABASE_URL) as db:
        # fetch the onsen
        onsen = db.query(Onsen).filter(Onsen.id == args.onsen_id).first()
        if not onsen:
            logger.error(f"No onsen with id={args.onsen_id} found!")
            return

        args_dict = vars(args)
        args_dict.pop("onsen_id", None)
        args_dict.pop("func", None)  # Not a model field

        # Create the visit with dynamic arguments
        visit = OnsenVisit(onsen_id=onsen.id, **args_dict)
        db.add(visit)
        db.commit()
        logger.info(f"Added a visit to onsen {onsen.name} (id={onsen.id})")
