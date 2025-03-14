"""
cli.py

A simple CLI to demonstrate how you might add or update onsen data
or add onsen visits. You could use argparse or click for a nicer interface.
"""

import argparse
from loguru import logger
from sqlalchemy.orm import Session
from src.db.conn import SessionLocal
from src.db.models import Onsen, OnsenVisit

def add_onsen(args):
    with SessionLocal() as db:
        onsen = Onsen(
            ban_number=args.ban_number,
            name=args.name,
            address=args.address,
            # ...
        )
        db.add(onsen)
        db.commit()
        logger.info(f"Added onsen {onsen.name}")

def add_visit(args):
    with SessionLocal() as db:
        # fetch the onsen
        onsen = db.query(Onsen).filter(Onsen.id == args.onsen_id).first()
        if not onsen:
            logger.error(f"No onsen with id={args.onsen_id} found!")
            return
        
        visit = OnsenVisit(
            onsen_id=onsen.id,
            visit_time=args.visit_time,
            length_minutes=args.length_minutes,
            rating=args.rating,
            sauna_visited=args.sauna_visited
        )
        db.add(visit)
        db.commit()
        logger.info(f"Added a visit to onsen {onsen.name} (id={onsen.id})")


def main():
    parser = argparse.ArgumentParser(description="Onsen CLI")
    subparsers = parser.add_subparsers(help="Sub-commands")

    # Sub-command: add_onsen
    parser_add_onsen = subparsers.add_parser("add-onsen", help="Add a new onsen.")
    parser_add_onsen.add_argument("--ban_number", required=True)
    parser_add_onsen.add_argument("--name", required=True)
    parser_add_onsen.add_argument("--address", default="")
    # ... add more fields as necessary
    parser_add_onsen.set_defaults(func=add_onsen)

    # Sub-command: add_visit
    parser_add_visit = subparsers.add_parser("add-visit", help="Add a new onsen visit.")
    parser_add_visit.add_argument("--onsen_id", type=int, required=True)
    parser_add_visit.add_argument("--visit_time", help="YYYY-MM-DD HH:MM", default=None)
    parser_add_visit.add_argument("--length_minutes", type=int, default=0)
    parser_add_visit.add_argument("--rating", type=int, default=0)
    parser_add_visit.add_argument("--sauna_visited", action="store_true")
    parser_add_visit.set_defaults(func=add_visit)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

# Example usage:

# poetry run python -m onsen_manager.cli add-onsen \
#     --ban_number 1 \
#     --name "Takegawara Onsen" \
#     --address "Oita Prefecture, Beppu City, Motomachi 16-23"

# poetry run python -m onsen_manager.cli add-visit \
#     --onsen_id 1 \
#     --length_minutes 60 \
#     --rating 5 \
#     --sauna_visited