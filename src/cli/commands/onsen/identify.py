"""
identify.py

Identify an onsen based on various input parameters (name, location, address, etc.).
"""

import argparse
from typing import Optional

from loguru import logger

from src.db.conn import get_db_from_args
from src.lib.onsen_identifier import identify_onsen, OnsenMatch
from src.cli.commands.onsen.print_summary import print_summary


def _print_match_list(matches: list[OnsenMatch]) -> None:
    """
    Print a formatted list of onsen matches.

    Args:
        matches: List of OnsenMatch objects to display
    """
    if not matches:
        print("\nNo matches found.")
        return

    print(f"\nFound {len(matches)} match(es):\n")
    print("=" * 80)

    for idx, match in enumerate(matches, 1):
        onsen = match.onsen
        print(f"\n{idx}. {onsen.name}")
        print(f"   ID / BAN        : {onsen.id} / {onsen.ban_number}")
        if onsen.region:
            print(f"   Region          : {onsen.region}")
        if onsen.address:
            print(f"   Address         : {onsen.address}")
        if onsen.latitude is not None and onsen.longitude is not None:
            print(f"   Coordinates     : {onsen.latitude:.6f}, {onsen.longitude:.6f}")
        print(f"   Confidence      : {match.confidence:.1%}")
        print(f"   Match Type      : {match.match_type}")
        print(f"   Match Details   : {match.match_details}")
        print("-" * 80)


def _get_user_confirmation(prompt: str) -> bool:
    """
    Get yes/no confirmation from user.

    Args:
        prompt: The prompt to display to the user

    Returns:
        True if user confirms, False otherwise
    """
    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            return False
        print("Please enter 'y' or 'n'")


def identify(args: argparse.Namespace) -> None:
    """
    Identify an onsen based on various input parameters.

    Supports identification by:
    - Name (fuzzy matching)
    - Coordinates (geographical proximity)
    - Address (fuzzy matching)
    - Region (fuzzy matching)

    Multiple criteria can be combined for better accuracy.
    """
    # Extract arguments
    name: Optional[str] = getattr(args, "name", None)
    latitude: Optional[float] = getattr(args, "latitude", None)
    longitude: Optional[float] = getattr(args, "longitude", None)
    address: Optional[str] = getattr(args, "address", None)
    region: Optional[str] = getattr(args, "region", None)
    max_distance_km: Optional[float] = getattr(args, "max_distance", None)
    limit: int = getattr(args, "limit", 5)
    auto_print: bool = getattr(args, "auto_print", False)
    name_threshold: float = getattr(args, "name_threshold", 0.6)
    address_threshold: float = getattr(args, "address_threshold", 0.5)
    region_threshold: float = getattr(args, "region_threshold", 0.6)

    # Validate that at least one search criterion is provided
    has_coords = latitude is not None and longitude is not None
    if not any([name, has_coords, address, region]):
        logger.error(
            "At least one search criterion must be provided: "
            "--name, --latitude/--longitude, --address, or --region"
        )
        return

    # Validate coordinates if partially provided
    if (latitude is None) != (longitude is None):
        logger.error("Both --latitude and --longitude must be provided together")
        return

    # Perform identification
# Get database configuration
    with get_db_from_args(args) as db:
        logger.info("Searching for matching onsens...")

        matches = identify_onsen(
            db_session=db,
            name=name,
            latitude=latitude,
            longitude=longitude,
            address=address,
            region=region,
            max_distance_km=max_distance_km,
            name_threshold=name_threshold,
            address_threshold=address_threshold,
            region_threshold=region_threshold,
            limit=limit,
        )

        if not matches:
            logger.warning("No onsens matched the provided criteria.")
            return

        # Display matches
        _print_match_list(matches)

        # Handle automatic printing of the best match
        if auto_print and matches:
            best_match = matches[0]
            logger.info(
                f"Auto-printing summary for best match: {best_match.onsen.name} "
                f"(confidence: {best_match.confidence:.1%})"
            )
            # Create a mock args object for print_summary
            summary_args = argparse.Namespace(
                onsen_id=best_match.onsen.id, ban_number=None, name=None
            )
            print_summary(summary_args)
            return

        # Interactive mode: ask user if they want to see full summary
        if len(matches) == 1:
            if _get_user_confirmation(
                f"\nShow full summary for '{matches[0].onsen.name}'?"
            ):
                summary_args = argparse.Namespace(
                    onsen_id=matches[0].onsen.id, ban_number=None, name=None
                )
                print_summary(summary_args)
        else:
            # Multiple matches: let user choose
            print(
                "\nEnter the number of the onsen to see full summary, "
                "or press Enter to skip:"
            )
            try:
                choice = input("> ").strip()
                if choice:
                    idx = int(choice)
                    if 1 <= idx <= len(matches):
                        selected = matches[idx - 1]
                        summary_args = argparse.Namespace(
                            onsen_id=selected.onsen.id, ban_number=None, name=None
                        )
                        print_summary(summary_args)
                    else:
                        logger.warning(f"Invalid choice: {idx}")
            except ValueError:
                logger.warning("Invalid input. Skipping summary display.")
