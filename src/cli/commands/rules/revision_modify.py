"""
Modify an existing rule revision record (metadata only, not rules themselves).
"""
# pylint: disable=bad-builtin  # input() is appropriate for CLI interaction

import argparse
from typing import Optional
from src.db.conn import get_db
from src.db.models import RuleRevision
from src.const import CONST


def modify_revision(args: argparse.Namespace) -> None:
    """
    Modify an existing rule revision's metadata.

    Args:
        args: Command-line arguments containing:
            - version: Optional version number to modify
    """
    # Select revision
    if hasattr(args, "version") and args.version:
        revision = get_revision_by_version(args.version)
    else:
        revision = select_revision_interactively()

    if not revision:
        print("No revision selected.")
        return

    print("=" * 80)
    print(f"Modifying Revision v{revision.version_number}")
    print("=" * 80)
    print()
    print("You can modify the weekly review data and adjustment context.")
    print("Note: You cannot modify version numbers, dates, or the actual rule changes.")
    print()

    # Modify weekly metrics
    print("Current weekly metrics:")
    print(f"  Onsen visits: {revision.onsen_visits_count}")
    print(f"  Sauna sessions: {revision.sauna_sessions_count}")
    print(f"  Running distance: {revision.running_distance_km} km")
    print()

    modify_metrics = input("Modify metrics? (y/n): ").strip().lower()
    if modify_metrics == "y":
        modify_weekly_metrics(revision)

    # Modify health data
    print()
    print("Current health data:")
    print(f"  Energy level: {revision.energy_level}")
    print(f"  Sleep hours: {revision.sleep_hours}")
    print()

    modify_health = input("Modify health data? (y/n): ").strip().lower()
    if modify_health == "y":
        modify_health_data(revision)

    # Modify reflections
    print()
    modify_reflections_choice = input("Modify reflections? (y/n): ").strip().lower()
    if modify_reflections_choice == "y":
        modify_reflections(revision)

    # Modify adjustment context
    print()
    print("Current adjustment context:")
    print(f"  Reason: {revision.adjustment_reason}")
    print(f"  Description: {revision.adjustment_description[:100]}...")
    print()

    modify_adjustment = input("Modify adjustment context? (y/n): ").strip().lower()
    if modify_adjustment == "y":
        modify_adjustment_context(revision)

    # Save changes
    with get_db(url=CONST.DATABASE_URL) as db:
        db.merge(revision)
        db.commit()

    print()
    print(f"Revision v{revision.version_number} updated successfully!")


def get_revision_by_version(version_number: int) -> Optional[RuleRevision]:
    """Get a revision by version number."""
    with get_db(url=CONST.DATABASE_URL) as db:
        revision = (
            db.query(RuleRevision)
            .filter(RuleRevision.version_number == version_number)
            .first()
        )

        if not revision:
            print(f"Error: Revision v{version_number} not found.")
            return None

        return revision


def select_revision_interactively() -> Optional[RuleRevision]:
    """Interactively select a revision."""
    with get_db(url=CONST.DATABASE_URL) as db:
        revisions = db.query(RuleRevision).order_by(RuleRevision.version_number.desc()).all()

        if not revisions:
            print("No revisions found in the database.")
            return None

        print("Available revisions:")
        for i, revision in enumerate(revisions, 1):
            print(
                f"{i}. v{revision.version_number} - {revision.revision_date.strftime('%Y-%m-%d')}"
            )

        print()
        while True:
            try:
                choice = input("Select a revision (number or 'q' to quit): ").strip()
                if choice.lower() == "q":
                    return None

                choice_num = int(choice)
                if 1 <= choice_num <= len(revisions):
                    return revisions[choice_num - 1]
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")


def modify_weekly_metrics(revision: RuleRevision) -> None:
    """Modify weekly metrics."""
    print()
    print("Enter new values (press Enter to keep current value):")

    def get_int_input(prompt: str, current: Optional[int]) -> Optional[int]:
        value = input(f"{prompt} [{current}]: ").strip()
        if not value:
            return current
        try:
            return int(value)
        except ValueError:
            print("Invalid number, keeping current value.")
            return current

    def get_float_input(prompt: str, current: Optional[float]) -> Optional[float]:
        value = input(f"{prompt} [{current}]: ").strip()
        if not value:
            return current
        try:
            return float(value)
        except ValueError:
            print("Invalid number, keeping current value.")
            return current

    def get_bool_input(prompt: str, current: Optional[bool]) -> Optional[bool]:
        value = input(f"{prompt} [{current}] (y/n): ").strip().lower()
        if not value:
            return current
        return value in ["y", "yes", "true", "1"]

    revision.onsen_visits_count = get_int_input("Onsen visits", revision.onsen_visits_count)
    revision.total_soaking_hours = get_float_input(
        "Total soaking hours", revision.total_soaking_hours
    )
    revision.sauna_sessions_count = get_int_input("Sauna sessions", revision.sauna_sessions_count)
    revision.running_distance_km = get_float_input(
        "Running distance (km)", revision.running_distance_km
    )
    revision.gym_sessions_count = get_int_input("Gym sessions", revision.gym_sessions_count)
    revision.long_exercise_completed = get_bool_input(
        "Long exercise session completed (hike/long run)", revision.long_exercise_completed
    )
    revision.rest_days_count = get_int_input("Rest days", revision.rest_days_count)


def modify_health_data(revision: RuleRevision) -> None:
    """Modify health and wellbeing data."""
    print()
    print("Enter new values (press Enter to keep current value):")

    energy_input = input(f"Energy level (1-10) [{revision.energy_level}]: ").strip()
    if energy_input:
        try:
            revision.energy_level = int(energy_input)
        except ValueError:
            pass

    sleep_input = input(f"Sleep hours [{revision.sleep_hours}]: ").strip()
    if sleep_input:
        try:
            revision.sleep_hours = float(sleep_input)
        except ValueError:
            pass

    sleep_quality = input(
        f"Sleep quality [{revision.sleep_quality_rating}]: "
    ).strip()
    if sleep_quality:
        revision.sleep_quality_rating = sleep_quality

    soreness = input(f"Soreness notes [{revision.soreness_notes or 'none'}]: ").strip()
    if soreness:
        revision.soreness_notes = soreness

    hydration = input(
        f"Hydration/nutrition [{revision.hydration_nutrition_notes or 'none'}]: "
    ).strip()
    if hydration:
        revision.hydration_nutrition_notes = hydration

    mood = input(f"Mood [{revision.mood_mental_state or 'none'}]: ").strip()
    if mood:
        revision.mood_mental_state = mood


def modify_reflections(revision: RuleRevision) -> None:
    """Modify reflection data."""
    print()
    print("Enter new values (press Enter to keep current value):")

    positive = input(f"What went well: ").strip()
    if positive:
        revision.reflection_positive = positive

    patterns = input(f"Patterns: ").strip()
    if patterns:
        revision.reflection_patterns = patterns

    warnings = input(f"Warnings: ").strip()
    if warnings:
        revision.reflection_warnings = warnings

    standout = input(f"Standout onsens: ").strip()
    if standout:
        revision.reflection_standout_onsens = standout

    routine = input(f"Routine notes: ").strip()
    if routine:
        revision.reflection_routine_notes = routine


def modify_adjustment_context(revision: RuleRevision) -> None:
    """Modify adjustment context."""
    print()
    print("Enter new values (press Enter to keep current value):")

    reason = input(f"Reason [{revision.adjustment_reason}]: ").strip()
    if reason:
        revision.adjustment_reason = reason

    description = input(f"Description: ").strip()
    if description:
        revision.adjustment_description = description

    duration = input(f"Duration [{revision.expected_duration}]: ").strip()
    if duration:
        revision.expected_duration = duration

    safeguard = input(f"Health safeguard [{revision.health_safeguard_applied or 'none'}]: ").strip()
    if safeguard:
        revision.health_safeguard_applied = safeguard
