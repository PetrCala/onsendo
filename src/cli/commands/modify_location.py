"""
Modify location command.
"""

import argparse
from src.db.conn import get_db
from src.db.models import Location
from src.const import CONST


def modify_location(args: argparse.Namespace) -> None:
    """Modify a location in the database."""
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

        # Update fields if provided
        if args.name is not None:
            # Check if new name conflicts with existing location
            if args.name != location.name:
                existing = db.query(Location).filter(Location.name == args.name).first()
                if existing:
                    print(f"Error: Location name '{args.name}' already exists.")
                    return
            location.name = args.name

        if args.latitude is not None:
            location.latitude = args.latitude

        if args.longitude is not None:
            location.longitude = args.longitude

        if args.description is not None:
            location.description = args.description

        db.commit()

        print(f"Successfully updated location '{location.name}' (ID: {location.id})")
        print(f"  Coordinates: {location.latitude}, {location.longitude}")
        if location.description:
            print(f"  Description: {location.description}")


def modify_location_interactive() -> None:
    """Modify a location using interactive prompts."""
    print("=== Modify Location ===")

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
        identifier = input("Enter location ID or name to modify: ").strip()
        if identifier:
            break
        print("Location identifier is required.")

    # Find the location
    with get_db(url=CONST.DATABASE_URL) as db:
        location = None

        # Try to parse as ID first
        try:
            location_id = int(identifier)
            location = db.query(Location).filter(Location.id == location_id).first()
        except ValueError:
            pass

        # If not found by ID, try by name
        if not location:
            location = db.query(Location).filter(Location.name == identifier).first()

        if not location:
            print(f"Error: Location '{identifier}' not found.")
            return

        print(f"\nCurrent location details:")
        print(f"  Name: {location.name}")
        print(f"  Coordinates: {location.latitude}, {location.longitude}")
        print(f"  Description: {location.description or '(none)'}")
        print()

    # Get new values (press Enter to keep current value)
    print("Enter new values (press Enter to keep current value):")

    new_name = input(f"Name [{location.name}]: ").strip()
    if not new_name:
        new_name = None

    while True:
        lat_str = input(f"Latitude [{location.latitude}]: ").strip()
        if not lat_str:
            new_latitude = None
            break
        try:
            new_latitude = float(lat_str)
            break
        except ValueError:
            print("Please enter a valid decimal number for latitude.")

    while True:
        lon_str = input(f"Longitude [{location.longitude}]: ").strip()
        if not lon_str:
            new_longitude = None
            break
        try:
            new_longitude = float(lon_str)
            break
        except ValueError:
            print("Please enter a valid decimal number for longitude.")

    new_description = input(
        f"Description [{location.description or '(none)'}]: "
    ).strip()
    if not new_description:
        new_description = None

    # Create args object for the main function
    class Args:
        pass

    args = Args()
    args.identifier = identifier
    args.name = new_name
    args.latitude = new_latitude
    args.longitude = new_longitude
    args.description = new_description

    modify_location(args)
