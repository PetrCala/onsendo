"""
Add onsen command.
"""

import argparse
from src.db.conn import get_db_from_args
from src.db.models import Onsen
from src.lib.cli_display import show_database_banner


def add_onsen(args: argparse.Namespace) -> None:
    """Add a new onsen to the database."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Add onsen")

    with get_db(url=config.url) as db:
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
