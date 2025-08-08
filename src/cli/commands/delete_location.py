"""
Delete location command.
"""

import argparse
from src.db.conn import get_db
from src.db.models import Location
from src.const import CONST


def delete_location(args: argparse.Namespace) -> None:
    """Delete a location from the database."""
    with get_db(url=CONST.DATABASE_URL) as db:
        # Try to find the location
        location = None

        # Try to parse as ID first
        try:
            location_id = int(args.identifier)
            location = db.query(Location).filter(Location.id == location_id).first()
        except ValueError:
            pass

        # If not found by ID, try by name
        if not location:
            location = (
                db.query(Location).filter(Location.name == args.identifier).first()
            )

        if not location:
            print(f"Error: Location '{args.identifier}' not found.")
            return

        # Confirm deletion
        if not args.force:
            print(
                f"Are you sure you want to delete location '{location.name}' (ID: {location.id})?"
            )
            confirm = input("Type 'yes' to confirm: ").strip().lower()
            if confirm != "yes":
                print("Deletion cancelled.")
                return

        # Delete the location
        db.delete(location)
        db.commit()

        print(f"Successfully deleted location '{location.name}' (ID: {location.id})")


def delete_location_interactive() -> None:
    """Delete a location using interactive prompts."""
    print("=== Delete Location ===")

    # List available locations first
    with get_db(url=CONST.DATABASE_URL) as db:
        locations = db.query(Location).order_by(Location.name).all()

        if not locations:
            print("No locations found in the database.")
            return

        print("Available locations:")
        for location in locations:
            print(f"  {location.id}: {location.name}")
        print()

    # Get location identifier
    while True:
        identifier = input("Enter location ID or name to delete: ").strip()
        if identifier:
            break
        print("Location identifier is required.")

    # Create args object for the main function
    class Args:
        pass

    args = Args()
    args.identifier = identifier
    args.force = False

    delete_location(args)
