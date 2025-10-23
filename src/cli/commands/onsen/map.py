"""
Generate interactive map of all onsens in the database.
"""

import argparse
import webbrowser
from pathlib import Path
from src.db.conn import get_db_from_args
from src.db.models import Onsen
from src.lib.map_generator import generate_all_onsens_map


def map_onsens(args: argparse.Namespace) -> None:
    """Generate an interactive map showing all onsens in the database."""
# Get database configuration
    with get_db_from_args(args) as db:
        # Get all onsens from the database
        onsens = db.query(Onsen).all()

        if not onsens:
            print("No onsens found in the database.")
            return

        print(f"Generating map with {len(onsens)} onsen(s)...")

        try:
            # Generate the map with visit status
            map_path = generate_all_onsens_map(onsens, db)

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
