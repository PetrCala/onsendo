"""
Pair Activities Command - Standalone Activity-Visit Pairing.

Provides batch pairing of onsen monitoring activities to visits based on
name similarity and time proximity. Can be used to pair historical activities
or re-pair activities after adjusting thresholds.
"""

# pylint: disable=bad-builtin

from datetime import datetime

from loguru import logger

from src.config import get_database_config
from src.db.conn import get_db
from src.db.models import Activity
from src.lib.activity_manager import ActivityManager
from src.lib.activity_visit_pairer import PairingConfig, pair_activities_to_visits
from src.types.exercise import ExerciseType


def cmd_strava_pair_activities(args):
    """
    Pair onsen monitoring activities to visits based on name and time.

    This command finds unlinked onsen monitoring activities and attempts to pair
    them with existing visits using fuzzy name matching and time proximity. Activities
    with high confidence matches (≥auto_threshold) are auto-linked, while medium
    confidence matches (≥review_threshold) can be reviewed interactively.

    Usage:
        poetry run onsendo strava pair-activities
        poetry run onsendo strava pair-activities --dry-run
        poetry run onsendo strava pair-activities --since 2025-10-01
        poetry run onsendo strava pair-activities --interactive
        poetry run onsendo strava pair-activities --auto-threshold 0.85

    Arguments:
        --since DATE: Only pair activities after this date (YYYY-MM-DD)
        --dry-run: Preview pairings without saving to database
        --auto-threshold FLOAT: Confidence threshold for auto-linking (default: 0.8)
        --review-threshold FLOAT: Minimum confidence for review (default: 0.6)
        --time-window HOURS: Search window in hours (default: 4)
        --interactive: Enable interactive review for medium-confidence matches
        --no-interactive: Disable interactive review (default)

    Examples:
        # Pair all unlinked activities with dry-run
        poetry run onsendo strava pair-activities --dry-run

        # Pair activities from last month
        poetry run onsendo strava pair-activities --since 2025-10-01

        # Interactive review for medium-confidence matches
        poetry run onsendo strava pair-activities --interactive

        # Adjust thresholds for more/less strict pairing
        poetry run onsendo strava pair-activities --auto-threshold 0.85 --review-threshold 0.7
    """
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    # Parse arguments
    since_date = None
    if hasattr(args, "since") and args.since:
        try:
            since_date = datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format '{args.since}'. Use YYYY-MM-DD")
            return

    dry_run = args.dry_run if hasattr(args, "dry_run") else False
    interactive = args.interactive if hasattr(args, "interactive") else False
    auto_threshold = args.auto_threshold if args.auto_threshold is not None else 0.8
    review_threshold = args.review_threshold if args.review_threshold is not None else 0.6
    time_window = args.time_window if args.time_window is not None else 4

    # Validate thresholds
    if not 0.0 <= auto_threshold <= 1.0:
        print(f"Error: auto-threshold must be between 0.0 and 1.0 (got {auto_threshold})")
        return
    if not 0.0 <= review_threshold <= 1.0:
        print(f"Error: review-threshold must be between 0.0 and 1.0 (got {review_threshold})")
        return
    if auto_threshold < review_threshold:
        print(f"Error: auto-threshold ({auto_threshold}) must be >= review-threshold ({review_threshold})")
        return

    print("=" * 60)
    print("Activity-Visit Pairing")
    print("=" * 60)

    with get_db(url=config.url) as db:
        manager = ActivityManager(db)

        # Query unlinked onsen monitoring activities
        query = db.query(Activity).filter(
            Activity.activity_type == ExerciseType.ONSEN_MONITORING.value,
            Activity.visit_id.is_(None),
        )

        if since_date:
            query = query.filter(Activity.recording_start >= since_date)
            print(f"Filtering: Activities since {since_date.strftime('%Y-%m-%d')}")

        unlinked_activities = query.order_by(Activity.recording_start.desc()).all()

        if not unlinked_activities:
            print("\nNo unlinked onsen monitoring activities found.")
            return

        print(f"\nFound {len(unlinked_activities)} unlinked onsen monitoring activities")
        print(f"Configuration:")
        print(f"  Auto-link threshold: {auto_threshold:.0%}")
        print(f"  Review threshold: {review_threshold:.0%}")
        print(f"  Time window: ±{time_window} hours")

        if dry_run:
            print(f"  Mode: DRY RUN (no changes will be saved)")
        print()

        # Configure pairing
        pairing_config = PairingConfig(
            auto_link_threshold=auto_threshold,
            review_threshold=review_threshold,
            time_window_hours=time_window,
        )

        # Get activity IDs
        activity_ids = [a.id for a in unlinked_activities]

        # Run pairing
        print("Analyzing activities and finding candidates...")
        pairing_results = pair_activities_to_visits(db, activity_ids, pairing_config)

        # Display results
        print("\n" + "=" * 60)
        print("Pairing Results")
        print("=" * 60)

        # Auto-linked activities
        if pairing_results.auto_linked:
            print(f"\n✓ High-Confidence Matches ({len(pairing_results.auto_linked)}):")
            print(f"  Confidence ≥ {auto_threshold:.0%} - Auto-link\n")

            for activity, visit, confidence in pairing_results.auto_linked:
                onsen_name = visit.onsen.name if visit.onsen else "Unknown"
                time_diff = abs((visit.visit_time - activity.recording_start).total_seconds() / 60)
                print(f"  [{confidence:.1%}] '{activity.activity_name}'")
                print(f"         → Visit: {onsen_name} ({visit.visit_time.strftime('%Y-%m-%d %H:%M')})")
                print(f"         Time diff: {int(time_diff)} minutes")
                print()

        # Manual review needed
        if pairing_results.manual_review:
            print(f"\n⚠ Medium-Confidence Matches ({len(pairing_results.manual_review)}):")
            print(f"  Confidence {review_threshold:.0%}-{auto_threshold:.0%} - Review needed\n")

            for activity, candidates in pairing_results.manual_review:
                print(f"  Activity: '{activity.activity_name}'")
                print(f"           {activity.recording_start.strftime('%Y-%m-%d %H:%M')}")
                print(f"  Top candidates:")
                for i, candidate in enumerate(candidates[:3], 1):
                    time_diff = int(candidate.time_diff_minutes)
                    print(f"    {i}. [{candidate.combined_score:.1%}] {candidate.onsen_name}")
                    print(f"       {candidate.visit.visit_time.strftime('%Y-%m-%d %H:%M')} ({time_diff} min away)")
                    print(f"       Name: {candidate.name_similarity:.0%}, Time: {time_diff} min")
                print()

        # No match found
        if pairing_results.no_match:
            print(f"\n✗ No Match Found ({len(pairing_results.no_match)}):")
            print(f"  No candidates above {review_threshold:.0%} threshold\n")

            for activity in pairing_results.no_match:
                print(f"  - '{activity.activity_name}'")
                print(f"    {activity.recording_start.strftime('%Y-%m-%d %H:%M')}")

        # Summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        stats = pairing_results.summary_stats()
        print(f"Total activities analyzed: {stats['total']}")
        print(f"Auto-linked (≥{auto_threshold:.0%}): {stats['auto_linked']}")
        print(f"Need review ({review_threshold:.0%}-{auto_threshold:.0%}): {stats['manual_review']}")
        print(f"No match (<{review_threshold:.0%}): {stats['no_match']}")

        # Apply auto-links (unless dry-run)
        if pairing_results.auto_linked and not dry_run:
            print("\n" + "=" * 60)
            print("Applying Auto-Links")
            print("=" * 60)

            success_count = 0
            error_count = 0

            for activity, visit, confidence in pairing_results.auto_linked:
                try:
                    manager.link_to_visit(activity.id, visit.id)
                    success_count += 1
                    onsen_name = visit.onsen.name if visit.onsen else "Unknown"
                    print(f"  ✓ Linked activity {activity.id} → visit {visit.id} ({onsen_name})")
                except Exception as e:
                    error_count += 1
                    logger.exception(f"Failed to link activity {activity.id} to visit {visit.id}")
                    print(f"  ✗ Failed to link activity {activity.id}: {e}")

            print(f"\nApplied {success_count}/{len(pairing_results.auto_linked)} auto-links")
            if error_count:
                print(f"Errors: {error_count}")

        # Interactive review
        if pairing_results.manual_review and interactive and not dry_run:
            print("\n" + "=" * 60)
            print("Interactive Review")
            print("=" * 60)

            review_linked = 0

            for activity, candidates in pairing_results.manual_review:
                print(f"\nActivity: '{activity.activity_name}'")
                print(f"         {activity.recording_start.strftime('%Y-%m-%d %H:%M')}")
                print("\nCandidates:")

                for i, candidate in enumerate(candidates[:5], 1):
                    time_diff = int(candidate.time_diff_minutes)
                    print(f"  [{i}] {candidate.onsen_name} ({candidate.combined_score:.1%})")
                    print(f"      Visit: {candidate.visit.visit_time.strftime('%Y-%m-%d %H:%M')} ({time_diff} min away)")

                choice = input(f"\nSelect visit [1-{min(5, len(candidates))}], or [s]kip: ").strip().lower()

                if choice == "s":
                    print("  Skipped")
                    continue

                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < min(5, len(candidates)):
                        selected_candidate = candidates[choice_idx]
                        manager.link_to_visit(activity.id, selected_candidate.visit.id)
                        review_linked += 1
                        print(f"  ✓ Linked to {selected_candidate.onsen_name}")
                    else:
                        print("  Invalid selection, skipping")
                except ValueError:
                    print("  Invalid input, skipping")

            if review_linked:
                print(f"\nManual review: Linked {review_linked} activities")

        # Final message
        if dry_run:
            print("\n" + "=" * 60)
            print("DRY RUN - No changes were saved")
            print("Run without --dry-run to apply pairings")
            print("=" * 60)


def configure_args(parser):
    """Configure argument parser for pair-activities command."""
    parser.add_argument(
        "--since",
        type=str,
        help="Only pair activities after this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview pairings without saving to database",
    )
    parser.add_argument(
        "--auto-threshold",
        type=float,
        default=0.8,
        help="Confidence threshold for auto-linking (default: 0.8 = 80%%)",
    )
    parser.add_argument(
        "--review-threshold",
        type=float,
        default=0.6,
        help="Minimum confidence for review (default: 0.6 = 60%%)",
    )
    parser.add_argument(
        "--time-window",
        type=int,
        default=4,
        help="Search window in hours for finding visits (default: 4)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive review for medium-confidence matches",
    )
