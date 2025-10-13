"""
Delete visit command with interactive support.
"""
# pylint: disable=bad-builtin  # input() is appropriate for CLI interaction

import argparse

from src.db.conn import get_db
from src.db.models import OnsenVisit, Onsen
from src.const import CONST


def delete_visit(args: argparse.Namespace) -> None:
    """Delete a visit from the database."""
    if not hasattr(args, "no_interactive") or not args.no_interactive:
        delete_visit_interactive()
        return

    with get_db(url=CONST.DATABASE_URL) as db:
        # Find visit by ID
        visit = db.query(OnsenVisit).filter(OnsenVisit.id == args.visit_id).first()
        if not visit:
            print(f"Error: Visit with ID {args.visit_id} not found.")
            return

        # Get onsen info for confirmation
        onsen = db.query(Onsen).filter(Onsen.id == visit.onsen_id).first()

        # Confirm deletion unless force flag is set
        if not hasattr(args, "force") or not args.force:
            confirm = input(
                f"Are you sure you want to delete visit to '{onsen.name}' on {visit.visit_time}? (y/N): "
            )
            if confirm.lower() not in ["y", "yes"]:
                print("Deletion cancelled.")
                return

        db.delete(visit)
        db.commit()
        print(f"Successfully deleted visit to '{onsen.name}' (Visit ID: {visit.id})")


def delete_visit_interactive() -> None:
    """Delete a visit using interactive prompts."""
    print("=== Delete Visit ===")

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
                    "\nEnter the number of the visit to delete (or 'q' to quit): "
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

        # Confirm deletion
        confirm = input(
            f"Are you sure you want to delete visit to '{selected_onsen.name}' on {selected_visit.visit_time}? (y/N): "
        )
        if confirm.lower() not in ["y", "yes"]:
            print("Deletion cancelled.")
            return

        # Delete the visit
        db.delete(selected_visit)
        db.commit()
        print(
            f"Successfully deleted visit to '{selected_onsen.name}' (Visit ID: {selected_visit.id})"
        )
