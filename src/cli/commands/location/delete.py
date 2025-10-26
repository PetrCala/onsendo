"""
Delete location command with interactive support.
"""

import argparse
from src.db.conn import get_db
from src.db.models import Location
from src.config import get_database_config
from src.lib.cli_display import show_database_banner, confirm_destructive_operation


def delete_location(args: argparse.Namespace) -> None:
    """Delete a location from the database."""
    if not hasattr(args, "no_interactive") or args.no_interactive is False:
        delete_location_interactive(args)
        return

    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Delete location")

    # Confirm production operation
    force = getattr(args, "force", False)
    try:
        confirm_destructive_operation(config, "delete location", force=force)
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

        # Confirm deletion unless force flag is set
        if not hasattr(args, "force") or not args.force:
            confirm = input(
                f"Are you sure you want to delete location '{location.name}' (ID: {location.id})? (y/N): "
            )
            if confirm.lower() not in ["y", "yes"]:
                print("Deletion cancelled.")
                return

        db.delete(location)
        db.commit()
        print(f"Successfully deleted location '{location.name}' (ID: {location.id})")


def delete_location_interactive(args: argparse.Namespace) -> None:
    """Delete a location using interactive prompts."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Delete location")

    # Confirm production operation
    force = getattr(args, "force", False)
    try:
        confirm_destructive_operation(config, "delete location", force=force)
    except ValueError as e:
        print(str(e))
        return

    print("=== Delete Location ===")

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
                    "\nEnter the number of the location to delete (or 'q' to quit): "
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

        # Confirm deletion
        confirm = input(
            f"Are you sure you want to delete location '{selected_location.name}' (ID: {selected_location.id})? (y/N): "
        )
        if confirm.lower() not in ["y", "yes"]:
            print("Deletion cancelled.")
            return

        # Delete the location
        db.delete(selected_location)
        db.commit()
        print(
            f"Successfully deleted location '{selected_location.name}' (ID: {selected_location.id})"
        )
