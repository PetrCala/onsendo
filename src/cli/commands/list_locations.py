"""
List locations command.
"""

import argparse
from src.db.conn import get_db
from src.db.models import Location
from src.const import CONST


def list_locations(args: argparse.Namespace) -> None:
    """List all locations in the database."""
    with get_db(url=CONST.DATABASE_URL) as db:
        locations = db.query(Location).order_by(Location.name).all()

        if not locations:
            print("No locations found in the database.")
            return

        print(f"Found {len(locations)} location(s):")
        print()

        for location in locations:
            print(f"ID: {location.id}")
            print(f"Name: {location.name}")
            print(f"Coordinates: {location.latitude}, {location.longitude}")
            if location.description:
                print(f"Description: {location.description}")
            print("-" * 40)
