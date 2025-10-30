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

# pylint: disable=bad-builtin

# Field groups for selective modification
# Maps category name to list of (field_name, display_name) tuples
FIELD_GROUPS = {
    "Basic visit information": [
        ("entry_fee_yen", "Entry fee"),
        ("payment_method", "Payment method"),
        ("visit_date", "Visit date"),
        ("visit_time_str", "Visit time"),
        ("weather", "Weather"),
        ("time_of_day", "Time of day"),
        ("temperature_outside_celsius", "Temperature outside"),
        ("stay_length_minutes", "Stay length"),
    ],
    "Travel information": [
        ("visited_with", "Visited with"),
        ("travel_mode", "Travel mode"),
        ("travel_time_minutes", "Travel time"),
    ],
    "Facility ratings": [
        ("accessibility_rating", "Accessibility rating"),
        ("cleanliness_rating", "Cleanliness rating"),
        ("navigability_rating", "Navigability rating"),
        ("view_rating", "View rating"),
        ("atmosphere_rating", "Atmosphere rating"),
    ],
    "Main bath information": [
        ("main_bath_type", "Main bath type"),
        ("main_bath_temperature", "Main bath temperature"),
        ("water_color", "Water color"),
        ("smell_intensity_rating", "Smell intensity rating"),
    ],
    "Changing room and facilities": [
        ("changing_room_cleanliness_rating", "Changing room cleanliness"),
        ("locker_availability_rating", "Locker availability"),
        ("had_soap", "Soap available"),
    ],
    "Sauna information": [
        ("had_sauna", "Sauna at facility"),
        ("sauna_visited", "Used sauna"),
        ("sauna_duration_minutes", "Sauna duration"),
        ("sauna_temperature", "Sauna temperature"),
        ("sauna_steam", "Sauna has steam"),
        ("sauna_rating", "Sauna rating"),
    ],
    "Outdoor bath information": [
        ("had_outdoor_bath", "Outdoor bath at facility"),
        ("outdoor_bath_visited", "Used outdoor bath"),
        ("outdoor_bath_temperature", "Outdoor bath temperature"),
        ("outdoor_bath_rating", "Outdoor bath rating"),
    ],
    "Rest area and food": [
        ("had_rest_area", "Rest area available"),
        ("rest_area_used", "Used rest area"),
        ("rest_area_rating", "Rest area rating"),
        ("had_food_service", "Food service available"),
        ("food_service_used", "Used food service"),
        ("food_quality_rating", "Food quality rating"),
        ("massage_chair_available", "Massage chair available"),
    ],
    "Crowd and mood": [
        ("crowd_level", "Crowd level"),
        ("interacted_with_locals", "Interacted with locals"),
        ("local_interaction_quality_rating", "Local interaction quality"),
        ("pre_visit_mood", "Mood before visit"),
        ("post_visit_mood", "Mood after visit"),
    ],
    "Health and energy": [
        ("energy_level_change", "Energy level change"),
        ("hydration_level", "Hydration level"),
    ],
    "Multi-onsen day": [
        ("multi_onsen_day", "Multi-onsen day"),
        ("visit_order", "Visit order"),
        ("previous_location", "Previous visit ID"),
        ("next_location", "Next visit ID"),
    ],
    "Personal rating and notes": [
        ("personal_rating", "Personal rating"),
        ("notes", "Notes"),
    ],
}

# Shortcuts for common field groups
GROUP_SHORTCUTS = {
    "basic": "Basic visit information",
    "travel": "Travel information",
    "ratings": "Facility ratings",
    "bath": "Main bath information",
    "changing": "Changing room and facilities",
    "sauna": "Sauna information",
    "outdoor": "Outdoor bath information",
    "food": "Rest area and food",
    "mood": "Crowd and mood",
    "health": "Health and energy",
    "multi": "Multi-onsen day",
    "rating": "Personal rating and notes",
}


def format_field_value(value) -> str:
    """Format a field value for display."""
    if value is None:
        return "(none)"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def select_fields_to_modify(visit: OnsenVisit, onsen: Onsen) -> list[str]:
    """
    Display a menu of fields and let user select which ones to modify.

    Args:
        visit: The visit to modify
        onsen: The onsen for this visit

    Returns:
        List of field names selected for modification
    """
    print("\n=== Select Fields to Modify ===")
    print(f"Visit: {onsen.name} on {visit.visit_time}")
    print(f"Current rating: {visit.personal_rating}/10\n")

    # Build field index
    field_index = {}
    current_number = 1

    print("Available fields to modify:\n")

    for group_name, fields in FIELD_GROUPS.items():
        print(f"{group_name}:")
        for field_name, display_name in fields:
            # Get current value
            if field_name == "visit_time_str":
                # Special handling for time
                current_value = (
                    visit.visit_time.strftime("%H:%M") if visit.visit_time else "(none)"
                )
            elif field_name == "visit_date":
                # Special handling for date
                current_value = (
                    visit.visit_time.strftime("%Y-%m-%d")
                    if visit.visit_time
                    else "(none)"
                )
            else:
                current_value = format_field_value(getattr(visit, field_name, None))

            print(f"  {current_number:2d}. {display_name:30s} ({current_value})")
            field_index[current_number] = field_name
            current_number += 1
        print()  # Blank line between groups

    # Show shortcuts
    print("Shortcuts:")
    for shortcut, group_name in GROUP_SHORTCUTS.items():
        print(f"  '{shortcut}' = {group_name}")
    print()

    # Get user selection
    while True:
        user_input = input(
            "Enter field numbers (comma-separated), shortcuts, or 'all' (or 'q' to cancel): "
        ).strip()

        if user_input.lower() == "q":
            return []

        if user_input.lower() == "all":
            # Return all field names
            return [
                field_name
                for _, fields in FIELD_GROUPS.items()
                for field_name, _ in fields
            ]

        # Parse selection
        selected_fields = set()

        for part in user_input.split(","):
            part = part.strip().lower()

            # Check if it's a shortcut
            if part in GROUP_SHORTCUTS:
                group_name = GROUP_SHORTCUTS[part]
                for field_name, _ in FIELD_GROUPS[group_name]:
                    selected_fields.add(field_name)
            else:
                # Try to parse as number
                try:
                    num = int(part)
                    if num in field_index:
                        selected_fields.add(field_index[num])
                    else:
                        print(f"Invalid field number: {num}")
                except ValueError:
                    print(f"Invalid input: {part}")

        if selected_fields:
            print(f"\nSelected {len(selected_fields)} field(s) to modify")
            return list(selected_fields)
        else:
            print("No valid fields selected. Please try again.")


def execute_selective_workflow(
    session: InteractiveSession,
    selected_fields: list[str],
    all_steps: list[dict],
) -> InteractiveSession:
    """
    Execute workflow for only the selected fields.

    Args:
        session: InteractiveSession with pre-populated visit_data
        selected_fields: List of field names to modify
        all_steps: Complete list of workflow steps

    Returns:
        Updated session
    """
    # Filter steps to only include selected fields
    filtered_steps = []

    # Track which conditional fields were selected
    has_conditional_selections = {}

    for step in all_steps:
        field_name = step["name"]

        # Include if explicitly selected
        if field_name in selected_fields:
            filtered_steps.append(step)

            # Track conditional parent fields
            # E.g., if sauna_rating is selected, we need had_sauna=True
            if "condition" in step:
                # Mark that this group has selections
                if "had_sauna" in str(step.get("condition", "")):
                    has_conditional_selections["had_sauna"] = True
                    has_conditional_selections["sauna_visited"] = True
                elif "had_outdoor_bath" in str(step.get("condition", "")):
                    has_conditional_selections["had_outdoor_bath"] = True
                    has_conditional_selections["outdoor_bath_visited"] = True
                elif "had_rest_area" in str(step.get("condition", "")):
                    has_conditional_selections["had_rest_area"] = True
                    has_conditional_selections["rest_area_used"] = True
                elif "had_food_service" in str(step.get("condition", "")):
                    has_conditional_selections["had_food_service"] = True
                    has_conditional_selections["food_service_used"] = True
                elif "multi_onsen_day" in str(step.get("condition", "")):
                    has_conditional_selections["multi_onsen_day"] = True
                elif "interacted_with_locals" in str(step.get("condition", "")):
                    has_conditional_selections["interacted_with_locals"] = True

    # Add conditional parent fields if their children were selected
    for step in all_steps:
        field_name = step["name"]
        if (
            field_name in has_conditional_selections
            and field_name not in selected_fields
        ):
            # Insert at appropriate position (before first child)
            filtered_steps.insert(0, step)

    # Execute filtered workflow (no db needed for modify)
    return execute_workflow(session, filtered_steps, db=None)


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

        # Let user select which fields to modify
        selected_fields = select_fields_to_modify(selected_visit, selected_onsen)

        if not selected_fields:
            print("No fields selected. Operation cancelled.")
            return

        print(
            "\n💡 Tip: Press Enter to keep current value, or type 'back' to navigate.\n"
        )

        # Create session and pre-populate with current visit data
        session = InteractiveSession()
        visit_dict = visit_to_dict(selected_visit)

        # Pre-populate session with existing values
        session.visit_data = visit_dict.copy()

        # Pre-populate history for navigation (only for selected fields)
        for field_name in selected_fields:
            if field_name in visit_dict:
                session.add_to_history(field_name, visit_dict[field_name], "")

        # Get all workflow steps (skip onsen selection)
        all_steps = get_visit_steps(skip_onsen_selection=True)

        # Execute selective workflow (only selected fields)
        session = execute_selective_workflow(session, selected_fields, all_steps)

        # Update the visit from the session data
        update_visit_from_dict(selected_visit, session.visit_data)

        # Save changes
        db.commit()
        print(
            f"\n✅ Successfully updated visit to '{selected_onsen.name}' (Visit ID: {selected_visit.id})"
        )
        print(f"Visit time: {selected_visit.visit_time}")
        print(f"Personal rating: {selected_visit.personal_rating}/10")
