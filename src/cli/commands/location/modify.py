"""
Modify location command with interactive support.
"""

import argparse
from src.db.conn import get_db_from_args
from src.db.models import Location
from src.lib.cli_display import show_database_banner, confirm_destructive_operation


def modify_location(args: argparse.Namespace) -> None:
    """Modify an existing location."""
    if not hasattr(args, "no_interactive") or args.no_interactive is False:
        modify_location_interactive(args)
        return

    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Modify location")

    # Confirm production operation
    force = getattr(args, "force", False)
    try:
        confirm_destructive_operation(config, "modify location", force=force)
    except ValueError as e:
        print(str(e))
        return

    with get_db(url=config.url) as db:
        # Find location by ID or name
        location = None
        try:
            # Try as ID first
            location_id = int(args.identifier)
            location = db.query(Location).filter(Location.id == location_id).first()
        except ValueError:
            # Try as name
            location = (
                db.query(Location).filter(Location.name == args.identifier).first()
            )

        if not location:
            print(f"Error: Location '{args.identifier}' not found.")
            return

        # Update fields if provided
        if hasattr(args, "name") and args.name is not None:
            location.name = args.name
        if hasattr(args, "latitude") and args.latitude is not None:
            location.latitude = args.latitude
        if hasattr(args, "longitude") and args.longitude is not None:
            location.longitude = args.longitude
        if hasattr(args, "description") and args.description is not None:
            location.description = args.description

        db.commit()
        print(f"Successfully updated location '{location.name}' (ID: {location.id})")


def modify_location_interactive(args: argparse.Namespace) -> None:
    """Modify a location using interactive prompts."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Modify location")

    # Confirm production operation
    force = getattr(args, "force", False)
    try:
        confirm_destructive_operation(config, "modify location", force=force)
    except ValueError as e:
        print(str(e))
        return

    print("=== Modify Location ===")

    with get_db(url=config.url) as db:
        # List available locations
        locations = db.query(Location).order_by(Location.name).all()

        if not locations:
            print("No locations found in the database.")
            return

        print("Available locations:")
        for i, location in enumerate(locations, 1):
            print(f"{i}. {location.name} (ID: {location.id})")

        # Get user selection
        while True:
            try:
                choice = input(
                    "\nEnter the number of the location to modify (or 'q' to quit): "
                ).strip()
                if choice.lower() == "q":
                    print("Operation cancelled.")
                    return

                choice_num = int(choice)
                if 1 <= choice_num <= len(locations):
                    selected_location = locations[choice_num - 1]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

        print(
            f"\nModifying location: {selected_location.name} (ID: {selected_location.id})"
        )
        print("Current values:")
        print(f"  Name: {selected_location.name}")
        print(f"  Latitude: {selected_location.latitude}")
        print(f"  Longitude: {selected_location.longitude}")
        print(f"  Description: {selected_location.description or '(none)'}")

        # Get new values
        print("\nEnter new values (press Enter to keep current value):")

        # Name
        new_name = input(f"Name [{selected_location.name}]: ").strip()
        if new_name:
            selected_location.name = new_name

        # Latitude
        while True:
            lat_input = input(f"Latitude [{selected_location.latitude}]: ").strip()
            if not lat_input:
                break
            try:
                new_lat = float(lat_input)
                selected_location.latitude = new_lat
                break
            except ValueError:
                print("Please enter a valid decimal number for latitude.")

        # Longitude
        while True:
            lon_input = input(f"Longitude [{selected_location.longitude}]: ").strip()
            if not lon_input:
                break
            try:
                new_lon = float(lon_input)
                selected_location.longitude = new_lon
                break
            except ValueError:
                print("Please enter a valid decimal number for longitude.")

        # Description
        new_desc = input(
            f"Description [{selected_location.description or '(none)'}]: "
        ).strip()
        if new_desc:
            selected_location.description = new_desc

        # Save changes
        db.commit()
        print(
            f"\nSuccessfully updated location '{selected_location.name}' (ID: {selected_location.id})"
        )
