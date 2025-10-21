"""
Compare two rule revisions.
"""
# pylint: disable=bad-builtin  # input() is appropriate for CLI interaction

import argparse
import json
import os
from typing import Optional
from src.db.conn import get_db
from src.db.models import RuleRevision
from src.config import get_database_config
from src.lib.rule_manager import RuleDiffer


def compare_revisions(args: argparse.Namespace) -> None:
    """
    Compare two rule revisions.

    Args:
        args: Command-line arguments containing:
            - version_a: First version number (optional, interactive if not provided)
            - version_b: Second version number (optional, interactive if not provided)
            - section: Limit comparison to specific section
            - metrics_only: Only show metrics comparison
            - rules_only: Only show rules comparison
    """
    # Select revisions to compare
    if hasattr(args, "version_a") and hasattr(args, "version_b") and args.version_a and args.version_b:
        version_a = args.version_a
        version_b = args.version_b
    else:
        result = select_revisions_interactively()
        if not result:
            print("Operation cancelled.")
            return
        version_a, version_b = result

    # Get revisions from database
# Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        revision_a = (
            db.query(RuleRevision)
            .filter(RuleRevision.version_number == version_a)
            .first()
        )
        revision_b = (
            db.query(RuleRevision)
            .filter(RuleRevision.version_number == version_b)
            .first()
        )

        if not revision_a:
            print(f"Error: Revision v{version_a} not found.")
            return
        if not revision_b:
            print(f"Error: Revision v{version_b} not found.")
            return

    # Display comparison
    print("=" * 80)
    print(f"COMPARING REVISIONS: v{version_a} vs v{version_b}")
    print("=" * 80)
    print()

    # Determine what to show based on flags
    show_metrics = True
    show_rules = True

    if hasattr(args, "metrics_only") and args.metrics_only:
        show_rules = False
    if hasattr(args, "rules_only") and args.rules_only:
        show_metrics = False

    if show_metrics:
        compare_metrics(revision_a, revision_b)

    if show_rules:
        compare_rules(revision_a, revision_b, args)


def select_revisions_interactively() -> Optional[tuple[int, int]]:
    """Interactively select two revisions to compare."""
# Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        revisions = db.query(RuleRevision).order_by(RuleRevision.version_number.desc()).all()

        if len(revisions) < 2:
            print("Need at least 2 revisions to compare.")
            return None

        print("Available revisions:")
        for i, revision in enumerate(revisions, 1):
            print(
                f"{i}. v{revision.version_number} - {revision.revision_date.strftime('%Y-%m-%d')} "
                f"({revision.revision_summary})"
            )

        print()

        # Select first revision
        while True:
            try:
                choice = input("Select first revision (number or 'q' to quit): ").strip()
                if choice.lower() == "q":
                    return None

                choice_num = int(choice)
                if 1 <= choice_num <= len(revisions):
                    revision_a = revisions[choice_num - 1]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

        # Select second revision
        while True:
            try:
                choice = input("Select second revision (number or 'q' to quit): ").strip()
                if choice.lower() == "q":
                    return None

                choice_num = int(choice)
                if 1 <= choice_num <= len(revisions):
                    revision_b = revisions[choice_num - 1]
                    if revision_b.version_number == revision_a.version_number:
                        print("Please select a different revision.")
                        continue
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

        return (revision_a.version_number, revision_b.version_number)


def compare_metrics(revision_a: RuleRevision, revision_b: RuleRevision) -> None:
    """Compare weekly metrics between two revisions."""
    print("METRICS COMPARISON")
    print("-" * 80)
    print(f"{'Metric':<30} | {'v' + str(revision_a.version_number):<15} | {'v' + str(revision_b.version_number):<15} | Change")
    print("-" * 80)

    def show_metric(name: str, val_a, val_b, unit: str = ""):
        if val_a is None and val_b is None:
            return

        val_a_str = str(val_a) if val_a is not None else "N/A"
        val_b_str = str(val_b) if val_b is not None else "N/A"

        # Calculate change
        if val_a is not None and val_b is not None:
            try:
                change = val_b - val_a
                if isinstance(change, bool):
                    change_str = "same" if val_a == val_b else "changed"
                else:
                    sign = "+" if change > 0 else ""
                    change_str = f"{sign}{change}{unit}"
            except:
                change_str = "N/A"
        else:
            change_str = "N/A"

        print(f"{name:<30} | {val_a_str:<15} | {val_b_str:<15} | {change_str}")

    show_metric("Onsen visits", revision_a.onsen_visits_count, revision_b.onsen_visits_count)
    show_metric(
        "Total soaking hours",
        revision_a.total_soaking_hours,
        revision_b.total_soaking_hours,
        "h",
    )
    show_metric("Sauna sessions", revision_a.sauna_sessions_count, revision_b.sauna_sessions_count)
    show_metric(
        "Running distance",
        revision_a.running_distance_km,
        revision_b.running_distance_km,
        "km",
    )
    show_metric("Gym sessions", revision_a.gym_sessions_count, revision_b.gym_sessions_count)
    show_metric(
        "Long exercise session", revision_a.long_exercise_completed, revision_b.long_exercise_completed
    )
    show_metric("Rest days", revision_a.rest_days_count, revision_b.rest_days_count)
    show_metric("Energy level", revision_a.energy_level, revision_b.energy_level, "/10")
    show_metric("Sleep hours", revision_a.sleep_hours, revision_b.sleep_hours, "h")

    print()


def compare_rules(revision_a: RuleRevision, revision_b: RuleRevision, args: argparse.Namespace) -> None:
    """Compare rule changes between two revisions."""
    print("RULES COMPARISON")
    print("-" * 80)

    # Parse sections modified from JSON
    try:
        sections_a = set(json.loads(revision_a.sections_modified or "[]"))
        sections_b = set(json.loads(revision_b.sections_modified or "[]"))
    except json.JSONDecodeError:
        print("Error parsing sections modified.")
        return

    # Filter by section if specified
    if hasattr(args, "section") and args.section:
        sections_a = {args.section} & sections_a
        sections_b = {args.section} & sections_b

    # Show which sections were modified in each
    print(f"v{revision_a.version_number} modified sections: {', '.join(f'§{s}' for s in sorted(sections_a)) or 'none'}")
    print(f"v{revision_b.version_number} modified sections: {', '.join(f'§{s}' for s in sorted(sections_b)) or 'none'}")
    print()

    # Show sections that differ
    unique_to_a = sections_a - sections_b
    unique_to_b = sections_b - sections_a
    common = sections_a & sections_b

    if unique_to_a:
        print(f"Only in v{revision_a.version_number}: {', '.join(f'§{s}' for s in sorted(unique_to_a))}")
    if unique_to_b:
        print(f"Only in v{revision_b.version_number}: {', '.join(f'§{s}' for s in sorted(unique_to_b))}")
    if common:
        print(f"Modified in both: {', '.join(f'§{s}' for s in sorted(common))}")

    print()

    # Show diff for markdown files if they exist
    if revision_a.markdown_file_path and revision_b.markdown_file_path:
        if os.path.exists(revision_a.markdown_file_path) and os.path.exists(
            revision_b.markdown_file_path
        ):
            print("UNIFIED DIFF")
            print("-" * 80)
            show_unified_diff(revision_a.markdown_file_path, revision_b.markdown_file_path)
            print()

            print("SIDE-BY-SIDE COMPARISON")
            print("-" * 80)
            show_side_by_side(revision_a, revision_b)
    else:
        print("Markdown files not available for detailed comparison.")

    print()


def show_unified_diff(file_a: str, file_b: str) -> None:
    """Show unified diff between two files."""
    with open(file_a, "r", encoding="utf-8") as f:
        content_a = f.read()
    with open(file_b, "r", encoding="utf-8") as f:
        content_b = f.read()

    differ = RuleDiffer()
    diff = differ.generate_unified_diff(content_a, content_b)

    # Print first 50 lines of diff
    diff_lines = diff.splitlines()
    for line in diff_lines[:50]:
        print(line)

    if len(diff_lines) > 50:
        print(f"\n... ({len(diff_lines) - 50} more lines)")


def show_side_by_side(revision_a: RuleRevision, revision_b: RuleRevision) -> None:
    """Show side-by-side comparison of key fields."""
    width = 35

    print(f"{'v' + str(revision_a.version_number):<{width}} | {'v' + str(revision_b.version_number):<{width}}")
    print("=" * (width * 2 + 3))

    # Dates
    print(f"{'Date: ' + revision_a.revision_date.strftime('%Y-%m-%d'):<{width}} | "
          f"{'Date: ' + revision_b.revision_date.strftime('%Y-%m-%d'):<{width}}")

    # Week period
    print(f"{revision_a.week_start_date + ' → ' + revision_a.week_end_date:<{width}} | "
          f"{revision_b.week_start_date + ' → ' + revision_b.week_end_date:<{width}}")

    print("-" * (width * 2 + 3))

    # Adjustment reason
    print(f"{'Reason: ' + (revision_a.adjustment_reason or 'N/A'):<{width}} | "
          f"{'Reason: ' + (revision_b.adjustment_reason or 'N/A'):<{width}}")

    # Duration
    print(f"{'Duration: ' + (revision_a.expected_duration or 'N/A'):<{width}} | "
          f"{'Duration: ' + (revision_b.expected_duration or 'N/A'):<{width}}")

    print("-" * (width * 2 + 3))

    # Key metrics
    def format_metric(label: str, value) -> str:
        if value is None:
            return f"{label}: N/A"
        return f"{label}: {value}"

    print(f"{format_metric('Onsen visits', revision_a.onsen_visits_count):<{width}} | "
          f"{format_metric('Onsen visits', revision_b.onsen_visits_count):<{width}}")

    print(f"{format_metric('Energy', revision_a.energy_level):<{width}} | "
          f"{format_metric('Energy', revision_b.energy_level):<{width}}")

    print()
