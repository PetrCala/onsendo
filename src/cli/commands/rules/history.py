"""
Show chronological history of all rule changes.
"""

import argparse
import json
from datetime import datetime
from src.db.conn import get_db_from_args
from src.db.models import RuleRevision


def show_history(args: argparse.Namespace) -> None:
    """
    Show chronological history of rule changes.

    Args:
        args: Command-line arguments containing:
            - section: Filter to specific section number (default: None)
            - date_range: Filter by date range "start,end" (default: None)
            - visual: Generate visual timeline chart (default: False)
    """
# Get database configuration
    with get_db_from_args(args) as db:
        query = db.query(RuleRevision).order_by(RuleRevision.revision_date.asc())

        # Apply section filter if specified
        if hasattr(args, "section") and args.section:
            query = query.filter(
                RuleRevision.sections_modified.like(f'%"{args.section}"%')
            )

        # Apply date range filter if specified
        if hasattr(args, "date_range") and args.date_range:
            try:
                start_str, end_str = args.date_range.split(",")
                start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d")
                end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d")
                query = query.filter(
                    RuleRevision.revision_date >= start_date,
                    RuleRevision.revision_date <= end_date,
                )
            except (ValueError, AttributeError) as e:
                print(f"Error: Invalid date range format. Use 'YYYY-MM-DD,YYYY-MM-DD'")
                print(f"Details: {e}")
                return

        revisions = query.all()

        if not revisions:
            print("No rule revisions found matching the criteria.")
            return

        if hasattr(args, "visual") and args.visual:
            # Generate visual timeline
            show_visual_timeline(revisions)
        else:
            # Show text-based timeline
            show_text_timeline(revisions)


def show_text_timeline(revisions: list) -> None:
    """
    Show text-based timeline of revisions.

    Args:
        revisions: List of RuleRevision objects
    """
    print("=" * 100)
    print("RULE HISTORY TIMELINE")
    print("=" * 100)
    print()

    for i, revision in enumerate(revisions, 1):
        # Parse sections modified
        try:
            sections_modified = json.loads(revision.sections_modified or "[]")
            sections_str = ", ".join(f"§{s}" for s in sections_modified)
        except json.JSONDecodeError:
            sections_str = "N/A"

        # Timeline marker
        marker = "├─" if i < len(revisions) else "└─"

        print(f"{marker} v{revision.version_number} │ {revision.revision_date.strftime('%Y-%m-%d')}")
        print(f"│  Week: {revision.week_start_date} → {revision.week_end_date}")
        print(f"│  Sections: {sections_str}")
        print(f"│  Reason: {revision.adjustment_reason}")
        print(f"│  Summary: {revision.revision_summary or 'N/A'}")

        # Show key metrics
        if revision.onsen_visits_count or revision.sauna_sessions_count:
            metrics = []
            if revision.onsen_visits_count:
                metrics.append(f"{revision.onsen_visits_count} onsen visits")
            if revision.sauna_sessions_count:
                metrics.append(f"{revision.sauna_sessions_count} sauna sessions")
            if revision.running_distance_km:
                metrics.append(f"{revision.running_distance_km}km running")
            if metrics:
                print(f"│  Metrics: {', '.join(metrics)}")

        print("│")

    print()
    print(f"Total revisions: {len(revisions)}")
    print()


def show_visual_timeline(revisions: list) -> None:
    """
    Generate a visual timeline chart of revisions.

    Args:
        revisions: List of RuleRevision objects
    """
    print("=" * 100)
    print("VISUAL TIMELINE")
    print("=" * 100)
    print()

    if not revisions:
        print("No data to display.")
        return

    # Calculate timeline span
    first_date = revisions[0].revision_date
    last_date = revisions[-1].revision_date
    total_days = (last_date - first_date).days

    print(f"Timeline: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
    print(f"Duration: {total_days} days")
    print()

    # Create a simple ASCII timeline
    timeline_width = 80
    timeline = [" "] * timeline_width

    # Map revisions to timeline positions
    for revision in revisions:
        days_from_start = (revision.revision_date - first_date).days
        if total_days > 0:
            position = int((days_from_start / total_days) * (timeline_width - 1))
        else:
            position = 0
        timeline[position] = "●"

    # Print timeline
    print("├" + "─" * (timeline_width - 2) + "┤")
    print("│" + "".join(timeline) + "│")
    print("├" + "─" * (timeline_width - 2) + "┤")
    print()

    # Print legend
    print("Revisions:")
    for revision in revisions:
        try:
            sections = json.loads(revision.sections_modified or "[]")
            sections_str = ", ".join(f"§{s}" for s in sections)
        except json.JSONDecodeError:
            sections_str = "N/A"

        print(
            f"  ● v{revision.version_number} - {revision.revision_date.strftime('%Y-%m-%d')} "
            f"({sections_str}): {revision.revision_summary or revision.adjustment_reason}"
        )

    print()
