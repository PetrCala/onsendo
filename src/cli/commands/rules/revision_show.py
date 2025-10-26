"""
Show detailed information about a specific rule revision.
"""
# pylint: disable=bad-builtin  # input() is appropriate for CLI interaction

import argparse
import json
import os
import subprocess
from typing import Optional
from src.db.conn import get_db
from src.db.models import RuleRevision
from src.config import get_database_config


def show_revision(args: argparse.Namespace) -> None:
    """
    Show detailed information about a specific rule revision.

    Args:
        args: Command-line arguments containing:
            - version: Optional version number (if not provided, interactive selection)
            - date: Optional date filter (YYYY-MM-DD)
            - format: Output format (text, json, markdown)
            - open_file: Open the revision markdown file in default editor
    """
    # Determine which revision to show
    if hasattr(args, "version") and args.version:
        revision = get_revision_by_version(args.version)
    elif hasattr(args, "date") and args.date:
        revision = get_revision_by_date(args.date)
    else:
        # Interactive selection
        revision = select_revision_interactively()

    if not revision:
        print("No revision selected or found.")
        return

    # Determine output format
    output_format = "text"
    if hasattr(args, "format") and args.format:
        output_format = args.format.lower()

    # Display revision
    if output_format == "json":
        display_revision_json(revision)
    elif output_format == "markdown":
        display_revision_markdown(revision)
    else:
        display_revision_text(revision)

    # Open file if requested
    if hasattr(args, "open_file") and args.open_file:
        open_revision_file(revision)


def get_revision_by_version(version_number: int) -> Optional[RuleRevision]:
    """Get a revision by version number."""
# Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        revision = (
            db.query(RuleRevision)
            .filter(RuleRevision.version_number == version_number)
            .first()
        )

        if not revision:
            print(f"Error: Revision v{version_number} not found.")
            return None

        return revision


def get_revision_by_date(date_str: str) -> Optional[RuleRevision]:
    """Get a revision by date."""
    from datetime import datetime

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"Error: Invalid date format '{date_str}'. Use YYYY-MM-DD.")
        return None

# Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        # Find revision closest to the target date
        revision = (
            db.query(RuleRevision)
            .filter(RuleRevision.revision_date >= target_date)
            .order_by(RuleRevision.revision_date.asc())
            .first()
        )

        if not revision:
            # Try finding before the date
            revision = (
                db.query(RuleRevision)
                .filter(RuleRevision.revision_date <= target_date)
                .order_by(RuleRevision.revision_date.desc())
                .first()
            )

        if not revision:
            print(f"Error: No revision found near {date_str}.")
            return None

        return revision


def select_revision_interactively() -> Optional[RuleRevision]:
    """Interactively select a revision from a list."""
# Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        revisions = db.query(RuleRevision).order_by(RuleRevision.version_number.desc()).all()

        if not revisions:
            print("No revisions found in the database.")
            return None

        print("Available revisions:")
        for i, revision in enumerate(revisions, 1):
            print(
                f"{i}. v{revision.version_number} - {revision.revision_date.strftime('%Y-%m-%d')} "
                f"({revision.revision_summary})"
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


def display_revision_text(revision: RuleRevision) -> None:
    """Display revision in formatted text mode."""
    print("=" * 80)
    print(f"RULE REVISION v{revision.version_number}")
    print("=" * 80)
    print()

    print(f"Revision Date: {revision.revision_date.strftime('%Y-%m-%d')}")
    print(f"Effective Date: {revision.effective_date.strftime('%Y-%m-%d')}")
    print(f"Week Period: {revision.week_start_date} → {revision.week_end_date}")
    print()

    # Summary Metrics
    print("SUMMARY METRICS")
    print("-" * 80)
    if revision.onsen_visits_count is not None:
        print(f"Onsen visits: {revision.onsen_visits_count}")
    if revision.total_soaking_hours is not None:
        print(f"Total soaking time: {revision.total_soaking_hours} hours")
    if revision.sauna_sessions_count is not None:
        print(f"Sauna sessions: {revision.sauna_sessions_count}")
    if revision.running_distance_km is not None:
        print(f"Running distance: {revision.running_distance_km} km")
    if revision.gym_sessions_count is not None:
        print(f"Gym sessions: {revision.gym_sessions_count}")
    if revision.long_exercise_completed is not None:
        print(f"Long exercise session completed: {'Yes' if revision.long_exercise_completed else 'No'}")
    if revision.rest_days_count is not None:
        print(f"Rest days: {revision.rest_days_count}")
    print()

    # Health and Wellbeing
    print("HEALTH AND WELLBEING")
    print("-" * 80)
    if revision.energy_level is not None:
        print(f"Energy level: {revision.energy_level}/10")
    if revision.sleep_hours is not None:
        print(f"Sleep: {revision.sleep_hours} hours")
    if revision.sleep_quality_rating:
        print(f"Sleep quality: {revision.sleep_quality_rating}")
    if revision.soreness_notes:
        print(f"Soreness/Pain: {revision.soreness_notes}")
    if revision.hydration_nutrition_notes:
        print(f"Hydration/Nutrition: {revision.hydration_nutrition_notes}")
    if revision.mood_mental_state:
        print(f"Mood: {revision.mood_mental_state}")
    print()

    # Reflections
    print("REFLECTIONS")
    print("-" * 80)
    if revision.reflection_positive:
        print(f"What went well: {revision.reflection_positive}")
    if revision.reflection_patterns:
        print(f"Patterns: {revision.reflection_patterns}")
    if revision.reflection_warnings:
        print(f"Warnings: {revision.reflection_warnings}")
    if revision.reflection_standout_onsens:
        print(f"Standout onsens: {revision.reflection_standout_onsens}")
    if revision.reflection_routine_notes:
        print(f"Routine notes: {revision.reflection_routine_notes}")
    print()

    # Rule Adjustment
    print("RULE ADJUSTMENT")
    print("-" * 80)
    print(f"Reason: {revision.adjustment_reason}")
    print(f"Description: {revision.adjustment_description}")
    print(f"Duration: {revision.expected_duration}")
    if revision.health_safeguard_applied:
        print(f"Health safeguard: {revision.health_safeguard_applied}")
    print()

    # Sections Modified
    try:
        sections_modified = json.loads(revision.sections_modified or "[]")
        if sections_modified:
            print("SECTIONS MODIFIED")
            print("-" * 80)
            print(", ".join(f"§{s}" for s in sections_modified))
            print()
    except json.JSONDecodeError:
        pass

    # Next Week Plans
    print("NEXT WEEK PLANS")
    print("-" * 80)
    if revision.next_week_focus:
        print(f"Focus: {revision.next_week_focus}")
    if revision.next_week_goals:
        print(f"Goals: {revision.next_week_goals}")
    if revision.next_week_sauna_limit is not None:
        print(f"Sauna limit: {revision.next_week_sauna_limit}")
    if revision.next_week_run_volume is not None:
        print(f"Run volume: {revision.next_week_run_volume} km")
    if revision.next_week_hike_destination:
        print(f"Hike destination: {revision.next_week_hike_destination}")
    print()

    # File path
    if revision.markdown_file_path:
        print(f"Revision file: {revision.markdown_file_path}")
        print()


def display_revision_json(revision: RuleRevision) -> None:
    """Display revision in JSON format."""
    import json

    revision_dict = {
        "version_number": revision.version_number,
        "revision_date": revision.revision_date.strftime("%Y-%m-%d"),
        "effective_date": revision.effective_date.strftime("%Y-%m-%d"),
        "week_start_date": revision.week_start_date,
        "week_end_date": revision.week_end_date,
        "metrics": {
            "onsen_visits_count": revision.onsen_visits_count,
            "total_soaking_hours": revision.total_soaking_hours,
            "sauna_sessions_count": revision.sauna_sessions_count,
            "running_distance_km": revision.running_distance_km,
            "gym_sessions_count": revision.gym_sessions_count,
            "long_exercise_completed": revision.long_exercise_completed,
            "rest_days_count": revision.rest_days_count,
        },
        "health": {
            "energy_level": revision.energy_level,
            "sleep_hours": revision.sleep_hours,
            "sleep_quality_rating": revision.sleep_quality_rating,
            "soreness_notes": revision.soreness_notes,
            "hydration_nutrition_notes": revision.hydration_nutrition_notes,
            "mood_mental_state": revision.mood_mental_state,
        },
        "reflections": {
            "reflection_positive": revision.reflection_positive,
            "reflection_patterns": revision.reflection_patterns,
            "reflection_warnings": revision.reflection_warnings,
            "reflection_standout_onsens": revision.reflection_standout_onsens,
            "reflection_routine_notes": revision.reflection_routine_notes,
        },
        "adjustment": {
            "reason": revision.adjustment_reason,
            "description": revision.adjustment_description,
            "duration": revision.expected_duration,
            "health_safeguard": revision.health_safeguard_applied,
        },
        "next_week": {
            "focus": revision.next_week_focus,
            "goals": revision.next_week_goals,
            "sauna_limit": revision.next_week_sauna_limit,
            "run_volume": revision.next_week_run_volume,
            "hike_destination": revision.next_week_hike_destination,
        },
        "sections_modified": json.loads(revision.sections_modified or "[]"),
        "revision_summary": revision.revision_summary,
        "markdown_file_path": revision.markdown_file_path,
    }

    print(json.dumps(revision_dict, indent=2))


def display_revision_markdown(revision: RuleRevision) -> None:
    """Display the revision markdown file content."""
    if not revision.markdown_file_path or not os.path.exists(revision.markdown_file_path):
        print(f"Error: Markdown file not found for v{revision.version_number}")
        return

    with open(revision.markdown_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(content)


def open_revision_file(revision: RuleRevision) -> None:
    """Open the revision markdown file in the default editor."""
    if not revision.markdown_file_path or not os.path.exists(revision.markdown_file_path):
        print(f"Error: Markdown file not found for v{revision.version_number}")
        return

    try:
        # Use the system's default editor
        if os.name == "posix":  # macOS/Linux
            subprocess.run(["open", revision.markdown_file_path], check=True)
        elif os.name == "nt":  # Windows
            os.startfile(revision.markdown_file_path)
        else:
            print(f"Cannot open file automatically. File path: {revision.markdown_file_path}")
    except Exception as e:
        print(f"Error opening file: {e}")
        print(f"File path: {revision.markdown_file_path}")
