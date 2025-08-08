"""
Add visit command with interactive support.
"""

import argparse
from loguru import logger
from src.db.conn import get_db
from src.db.models import Onsen, OnsenVisit
from src.const import CONST
from .interactive import add_visit_interactive


def add_visit(args: argparse.Namespace) -> None:
    """
    Add a new onsen visit to the database.
    """
    if not hasattr(args, "no_interactive") or not args.no_interactive:
        add_visit_interactive()
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
        args_dict.pop("no_interactive", None)  # Not a model field

        # Create the visit with dynamic arguments
        visit = OnsenVisit(onsen_id=onsen.id, **args_dict)
        db.add(visit)
        db.commit()
        logger.info(f"Added a visit to onsen {onsen.name} (id={onsen.id})")
