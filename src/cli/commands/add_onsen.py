"""
add_onsen.py

Add a new onsen to the database.
"""

import argparse
from loguru import logger
from src.db.conn import get_db
from src.db.models import Onsen
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
