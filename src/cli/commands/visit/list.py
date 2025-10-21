"""
List visits command.
"""

import argparse
from src.db.conn import get_db
from src.db.models import OnsenVisit, Onsen
from src.config import get_database_config


def list_visits(args: argparse.Namespace) -> None:
    """List all visits in the database."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        # Get visits with onsen information
        visits = (
            db.query(OnsenVisit, Onsen)
            .join(Onsen)
            .order_by(OnsenVisit.visit_time.desc())
            .all()
        )

        if not visits:
            print("No visits found in the database.")
            return

        print(f"Found {len(visits)} visit(s):")
        print("-" * 100)

        for visit, onsen in visits:
            print(f"Visit ID: {visit.id}")
            print(f"Onsen: {onsen.name} (ID: {onsen.id})")
            print(f"Visit time: {visit.visit_time}")
            print(f"Entry fee: {visit.entry_fee_yen} yen")
            print(f"Stay length: {visit.stay_length_minutes} minutes")
            print(f"Personal rating: {visit.personal_rating}/10")
            if visit.weather:
                print(f"Weather: {visit.weather}")
            if visit.travel_mode:
                print(f"Travel mode: {visit.travel_mode}")
            if visit.notes:
                print(f"Notes: {visit.notes}")
            print("-" * 100)
