"""
Add onsen command.
"""

import argparse
from src.db.conn import get_db
from src.db.models import Onsen
from src.const import CONST


def add_onsen(args: argparse.Namespace) -> None:
    """Add a new onsen to the database."""
    with get_db(url=CONST.DATABASE_URL) as db:
        # Check if onsen with this BAN number already exists
        existing = db.query(Onsen).filter(Onsen.ban_number == args.ban_number).first()
        if existing:
            print(f"Error: Onsen with BAN number '{args.ban_number}' already exists.")
            return

        # Create new onsen
        onsen = Onsen(
            ban_number=args.ban_number,
            name=args.name,
            address=args.address or "",
        )

        db.add(onsen)
        db.commit()

        print(
            f"Successfully added onsen '{args.name}' (ID: {onsen.id}, BAN: {args.ban_number})"
        )
        if args.address:
            print(f"  Address: {args.address}")
