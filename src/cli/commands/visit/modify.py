"""
Modify visit command with interactive support.
"""

import argparse
from src.db.conn import get_db
from src.db.models import OnsenVisit, Onsen
from src.const import CONST


def modify_visit(args: argparse.Namespace) -> None:
    if not hasattr(args, "no_interactive") or not args.no_interactive:
        modify_visit_interactive()
        return

    with get_db(url=CONST.DATABASE_URL) as db:
        # Find visit by ID
        visit = db.query(OnsenVisit).filter(OnsenVisit.id == args.visit_id).first()
        if not visit:
            print(f"Error: Visit with ID {args.visit_id} not found.")
            return

        # Update fields if provided
        if hasattr(args, "entry_fee_yen") and args.entry_fee_yen is not None:
            visit.entry_fee_yen = args.entry_fee_yen
        if (
            hasattr(args, "stay_length_minutes")
            and args.stay_length_minutes is not None
        ):
            visit.stay_length_minutes = args.stay_length_minutes
        if hasattr(args, "personal_rating") and args.personal_rating is not None:
            visit.personal_rating = args.personal_rating
        if hasattr(args, "weather") and args.weather is not None:
            visit.weather = args.weather
        if hasattr(args, "travel_mode") and args.travel_mode is not None:
            visit.travel_mode = args.travel_mode
        if hasattr(args, "notes") and args.notes is not None:
            visit.notes = args.notes

        db.commit()
        onsen = db.query(Onsen).filter(Onsen.id == visit.onsen_id).first()
        print(f"Successfully updated visit to '{onsen.name}' (Visit ID: {visit.id})")


def modify_visit_interactive() -> None:
    """Modify a visit using interactive prompts."""
    print("=== Modify Visit ===")

    with get_db(url=CONST.DATABASE_URL) as db:
        # List available visits
        visits = (
            db.query(OnsenVisit, Onsen)
            .join(Onsen)
            .order_by(OnsenVisit.visit_time.desc())
            .all()
        )

        if not visits:
            print("No visits found in the database.")
            return

        print("Available visits:")
        for i, (visit, onsen) in enumerate(visits, 1):
            print(f"{i}. {onsen.name} - {visit.visit_time} (Visit ID: {visit.id})")

        # Get user selection
        while True:
            try:
                choice = input(
                    "\nEnter the number of the visit to modify (or 'q' to quit): "
                ).strip()
                if choice.lower() == "q":
                    print("Operation cancelled.")
                    return

                choice_num = int(choice)
                if 1 <= choice_num <= len(visits):
                    selected_visit, selected_onsen = visits[choice_num - 1]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

        print(
            f"\nModifying visit to: {selected_onsen.name} (Visit ID: {selected_visit.id})"
        )
        print("Current values:")
        print(f"  Entry fee: {selected_visit.entry_fee_yen} yen")
        print(f"  Stay length: {selected_visit.stay_length_minutes} minutes")
        print(f"  Personal rating: {selected_visit.personal_rating}/10")
        print(f"  Weather: {selected_visit.weather or '(none)'}")
        print(f"  Travel mode: {selected_visit.travel_mode or '(none)'}")
        print(f"  Notes: {selected_visit.notes or '(none)'}")

        # Get new values
        print("\nEnter new values (press Enter to keep current value):")

        # Entry fee
        fee_input = input(f"Entry fee (yen) [{selected_visit.entry_fee_yen}]: ").strip()
        if fee_input:
            try:
                selected_visit.entry_fee_yen = int(fee_input)
            except ValueError:
                print("Invalid number for entry fee. Keeping current value.")

        # Stay length
        stay_input = input(
            f"Stay length (minutes) [{selected_visit.stay_length_minutes}]: "
        ).strip()
        if stay_input:
            try:
                selected_visit.stay_length_minutes = int(stay_input)
            except ValueError:
                print("Invalid number for stay length. Keeping current value.")

        # Personal rating
        rating_input = input(
            f"Personal rating (1-10) [{selected_visit.personal_rating}]: "
        ).strip()
        if rating_input:
            try:
                rating = int(rating_input)
                if 1 <= rating <= 10:
                    selected_visit.personal_rating = rating
                else:
                    print("Rating must be between 1 and 10. Keeping current value.")
            except ValueError:
                print("Invalid number for rating. Keeping current value.")

        # Weather
        weather_input = input(
            f"Weather [{selected_visit.weather or '(none)'}]: "
        ).strip()
        if weather_input:
            selected_visit.weather = weather_input

        # Travel mode
        travel_input = input(
            f"Travel mode [{selected_visit.travel_mode or '(none)'}]: "
        ).strip()
        if travel_input:
            selected_visit.travel_mode = travel_input

        # Notes
        notes_input = input(
            f"Notes [{selected_visit.notes or '(none)'}]: "
        ).strip()
        if notes_input:
            selected_visit.notes = notes_input

        # Save changes
        db.commit()
        print(
            f"\nSuccessfully updated visit to '{selected_onsen.name}' (Visit ID: {selected_visit.id})"
        )
