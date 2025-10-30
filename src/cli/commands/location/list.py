"""
List locations command.
"""

import argparse
from src.db.conn import get_db
from src.db.models import Location
from src.config import get_database_config


def list_locations(args: argparse.Namespace) -> None:
    """List all locations in the database."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        query = db.query(Location).order_by(Location.name)

        # Apply limit if specified
        if hasattr(args, 'limit') and args.limit is not None:
            query = query.limit(args.limit)

        locations = query.all()

        if not locations:
            print("No locations found in the database.")
            return

        print(f"Found {len(locations)} location(s):")
        print("-" * 80)

        for location in locations:
            print(f"ID: {location.id}")
            print(f"Name: {location.name}")
            print(f"Coordinates: {location.latitude}, {location.longitude}")
            if location.description:
                print(f"Description: {location.description}")
            print("-" * 80)
