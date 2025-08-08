"""
Add location command with interactive support.
"""

import argparse
from src.db.conn import get_db
from src.db.models import Location
from src.const import CONST


def add_location(args: argparse.Namespace) -> None:
    """Add a new location to the database."""
    if not hasattr(args, "no_interactive") or not args.no_interactive:
        add_location_interactive()
        return

    with get_db(url=CONST.DATABASE_URL) as db:
        # Check if location with this name already exists
        existing = db.query(Location).filter(Location.name == args.name).first()
        if existing:
            print(f"Error: Location '{args.name}' already exists.")
            return

        # Create new location
        location = Location(
            name=args.name,
            latitude=args.latitude,
            longitude=args.longitude,
            description=args.description or "",
        )

        db.add(location)
        db.commit()

        print(f"Successfully added location '{args.name}' (ID: {location.id})")
        print(f"  Coordinates: {args.latitude}, {args.longitude}")
        if args.description:
            print(f"  Description: {args.description}")


def add_location_interactive() -> None:
    """Add a new location using interactive prompts."""
    print("=== Add New Location ===")

    # Get location name
    while True:
        name = input("Location name: ").strip()
        if name:
            break
        print("Location name is required.")

    # Get coordinates
    while True:
        try:
            lat_str = input("Latitude (decimal degrees, e.g., 33.2794): ").strip()
            latitude = float(lat_str)
            break
        except ValueError:
            print("Please enter a valid decimal number for latitude.")

    while True:
        try:
            lon_str = input("Longitude (decimal degrees, e.g., 131.5011): ").strip()
            longitude = float(lon_str)
            break
        except ValueError:
            print("Please enter a valid decimal number for longitude.")

    # Get optional description
    description = input("Description (optional): ").strip()

    # Create args object for the main function
    class Args:
        pass

    args = Args()
    args.name = name
    args.latitude = latitude
    args.longitude = longitude
    args.description = description if description else None
    args.no_interactive = True  # Prevent recursion

    add_location(args)
