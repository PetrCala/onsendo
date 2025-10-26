"""
List all rule revisions.
"""

import argparse
import json
from src.db.conn import get_db
from src.db.models import RuleRevision
from src.config import get_database_config


def list_revisions(args: argparse.Namespace) -> None:
    """
    List all rule revisions in the database.

    Args:
        args: Command-line arguments containing:
            - verbose: Include full adjustment descriptions (default: False)
            - limit: Maximum number of revisions to show (default: all)
            - section: Filter by specific section number (default: None)
    """
# Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    with get_db(url=config.url) as db:
        query = db.query(RuleRevision).order_by(RuleRevision.version_number.desc())

        # Apply section filter if specified
        if hasattr(args, "section") and args.section:
            # Filter revisions that modified the specified section
            query = query.filter(
                RuleRevision.sections_modified.like(f'%"{args.section}"%')
            )

        # Apply limit if specified
        if hasattr(args, "limit") and args.limit and args.limit > 0:
            query = query.limit(args.limit)

        revisions = query.all()

        if not revisions:
            print("No rule revisions found in the database.")
            return

        print("=" * 100)
        print("RULE REVISIONS")
        print("=" * 100)
        print()

        for revision in revisions:
            # Parse sections modified from JSON
            try:
                sections_modified = json.loads(revision.sections_modified or "[]")
                sections_str = ", ".join(sections_modified)
            except json.JSONDecodeError:
                sections_str = "N/A"

            print(f"Version {revision.version_number}")
            print(f"  Date: {revision.revision_date.strftime('%Y-%m-%d')}")
            print(f"  Week: {revision.week_start_date} → {revision.week_end_date}")
            print(f"  Sections Modified: {sections_str}")
            print(f"  Summary: {revision.revision_summary or 'N/A'}")
            print(f"  Reason: {revision.adjustment_reason or 'N/A'}")

            if hasattr(args, "verbose") and args.verbose:
                print(f"  Description: {revision.adjustment_description or 'N/A'}")
                print(f"  Duration: {revision.expected_duration or 'N/A'}")
                if revision.health_safeguard_applied:
                    print(f"  Health Safeguard: {revision.health_safeguard_applied}")

            print()

        total_count = db.query(RuleRevision).count()
        print(f"Total revisions: {total_count}")
        if hasattr(args, "limit") and args.limit and args.limit < total_count:
            print(f"(Showing {min(args.limit, len(revisions))} of {total_count})")
        print()
