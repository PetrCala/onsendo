"""
Modify visit command with interactive support.
"""

import argparse
from src.db.conn import get_db
from src.db.models import OnsenVisit, Onsen
from src.config import get_database_config
from src.lib.cli_display import show_database_banner, confirm_destructive_operation
from src.cli.commands.visit.interactive import (
    InteractiveSession,
    visit_to_dict,
    update_visit_from_dict,
    get_visit_steps,
    execute_workflow,
)


def modify_visit(args: argparse.Namespace) -> None:
    if not hasattr(args, "no_interactive") or not args.no_interactive:
        modify_visit_interactive(args)
        return

    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Modify visit")

    # Confirm production operation
    force = getattr(args, "force", False)
    try:
        confirm_destructive_operation(config, "modify visit", force=force)
    except ValueError as e:
        print(str(e))
        return

    with get_db(url=config.url) as db:
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


def modify_visit_interactive(args: argparse.Namespace) -> None:
    """
    Modify a visit using interactive prompts with full workflow access.
    Uses the same comprehensive workflow as add_visit but with pre-populated current values.
    """
    print("=== Modify Visit ===")

    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Modify visit")

    # Confirm production operation
    try:
        confirm_destructive_operation(config, "modify visit", force=False)
    except ValueError as e:
        print(str(e))
        return

    with get_db(url=config.url) as db:
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
        print(
            "Note: Onsen selection cannot be changed. All other fields can be edited."
        )
        print(
            "💡 Tip: Press Enter to keep current value, or type 'back' to navigate.\n"
        )

        # Import shared workflow functions
        from src.cli.commands.visit.interactive import (
            InteractiveSession,
            visit_to_dict,
            update_visit_from_dict,
            get_visit_steps,
            execute_workflow,
        )

        # Create session and pre-populate with current visit data
        session = InteractiveSession()
        visit_dict = visit_to_dict(selected_visit)

        # Pre-populate session with existing values
        session.visit_data = visit_dict.copy()

        # Pre-populate history for navigation
        for field_name, value in visit_dict.items():
            if field_name not in ("id", "onsen_id"):  # Skip non-editable fields
                session.add_to_history(field_name, value, "")

        # Get workflow steps (skip onsen selection since we can't change it)
        steps = get_visit_steps(skip_onsen_selection=True)

        # Execute the complete workflow
        session = execute_workflow(session, steps, db=None)

        # Update the visit from the session data
        update_visit_from_dict(selected_visit, session.visit_data)

        # Save changes
        db.commit()
        print(
            f"\n✅ Successfully updated visit to '{selected_onsen.name}' (Visit ID: {selected_visit.id})"
        )
        print(f"Visit time: {selected_visit.visit_time}")
        print(f"Personal rating: {selected_visit.personal_rating}/10")
