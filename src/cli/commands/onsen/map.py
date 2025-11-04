"""
Generate interactive map of all onsens in the database.
"""

import argparse
import webbrowser
from pathlib import Path

from src.config import get_database_config
from src.db.conn import get_db
from src.db.models import Onsen
from src.lib.map_generator import generate_all_onsens_map
from src.lib.onsen_filter import filter_onsens_by_keyword, format_onsen_summary_table


def map_onsens(args: argparse.Namespace) -> None:
    """Generate an interactive map showing all onsens in the database."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        # Check if filtering is requested
        filter_keywords = getattr(args, 'filter', None)
        filter_fields = getattr(args, 'field', None)
        list_matches = getattr(args, 'list_matches', False)

        # Get onsens (filtered or all)
        if filter_keywords:
            onsens = filter_onsens_by_keyword(db, filter_keywords, filter_fields)
            filter_info = f" (filtered by: {', '.join(filter_keywords)})"
        else:
            onsens = db.query(Onsen).all()
            filter_info = ""

        if not onsens:
            if filter_keywords:
                print(f"No onsens found matching: {', '.join(filter_keywords)}")
            else:
                print("No onsens found in the database.")
            return

        # Display filtered list if requested
        if list_matches and filter_keywords:
            print(f"\nFound {len(onsens)} onsen(s) matching: {', '.join(filter_keywords)}")
            print(format_onsen_summary_table(onsens))
            print()

        print(f"Generating map with {len(onsens)} onsen(s){filter_info}...")

        try:
            # Generate the map with visit status and locations
            show_locations = not getattr(args, "no_show_locations", False)
            map_path = generate_all_onsens_map(onsens, db, show_locations=show_locations)

            print("=" * 60)
            print("Interactive Onsen Map Generated!")
            print(f"\nMap saved to: {map_path}")

            # Default to auto-open unless explicitly disabled with --no_open_map
            auto_open = not getattr(args, "no_open_map", False)
            if auto_open:
                print("\nOpening map in browser...")
                webbrowser.open(Path(map_path).as_uri())
            else:
                print("\nTo open in browser, click the link below:")
                print(f"{Path(map_path).as_uri()}")
                print(f"\nOr run: open '{map_path}'")
            print("=" * 60)

        except (OSError, ValueError) as e:
            print(f"Error generating map: {e}")
