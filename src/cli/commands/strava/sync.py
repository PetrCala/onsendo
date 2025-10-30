"""
Sync command for Strava integration - Unified Activity System.

Provides batch synchronization of recent Strava activities with interactive
tagging for onsen monitoring sessions.
"""

# pylint: disable=bad-builtin

from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from src.config import get_database_config
from src.db.conn import get_db
from src.lib.activity_manager import ActivityManager
from src.lib.strava_client import StravaClient
from src.lib.strava_converter import StravaToActivityConverter
from src.paths import PATHS
from src.types.strava import ActivityFilter, StravaSettings


def cmd_strava_sync(args):
    """
    Batch sync recent Strava activities using unified activity system.

    Downloads and imports Strava activities with optional interactive tagging
    for onsen monitoring sessions.

    Usage:
        poetry run onsendo strava sync
        poetry run onsendo strava sync --days 7
        poetry run onsendo strava sync --days 30 --interactive
        poetry run onsendo strava sync --type Run --days 30
        poetry run onsendo strava sync --dry-run
        poetry run onsendo strava sync --auto-tag-pattern "onsen"

    Arguments:
        --days N: Sync activities from last N days (default: 7)
        --type TYPE: Only sync specific activity type (Run, Ride, etc.)
        --interactive: Prompt to tag activities as onsen monitoring
        --auto-tag-pattern PATTERN: Auto-tag activities with name matching pattern
        --auto-link: Automatically link tagged activities to nearby visits
        --dry-run: Show what would be synced without importing
        --skip-existing: Skip activities that already exist in database

    Examples:
        # Sync last 7 days (import all, no tagging)
        poetry run onsendo strava sync

        # Sync with interactive tagging
        poetry run onsendo strava sync --days 30 --interactive

        # Auto-tag activities with "onsen" in name
        poetry run onsendo strava sync --days 14 --auto-tag-pattern "onsen"

        # Sync only running activities
        poetry run onsendo strava sync --type Run --days 14

        # Dry run to see what would be synced
        poetry run onsendo strava sync --days 30 --dry-run
    """
    # Load settings
    try:
        settings = StravaSettings.from_env()
    except Exception as e:
        print(f"Error loading Strava settings: {e}")
        print("\nPlease ensure your .env file is configured:")
        print("  STRAVA_CLIENT_ID=your_client_id")
        print("  STRAVA_CLIENT_SECRET=your_client_secret")
        return

    # Initialize client
    try:
        client = StravaClient(settings.credentials, settings.token_path)

        if not client.is_authenticated():
            print("You are not authenticated with Strava.")
            print("Please run: poetry run onsendo strava auth")
            return

    except Exception as e:
        print(f"Error initializing Strava client: {e}")
        return

    # Parse arguments
    days = args.days if hasattr(args, "days") and args.days else 7
    activity_type = args.type if hasattr(args, "type") and args.type else None
    interactive = args.interactive if hasattr(args, "interactive") else False
    auto_tag_pattern = (
        args.auto_tag_pattern if hasattr(args, "auto_tag_pattern") else None
    )
    auto_link = args.auto_link if hasattr(args, "auto_link") else False
    dry_run = args.dry_run if hasattr(args, "dry_run") else False
    skip_existing = args.skip_existing if hasattr(args, "skip_existing") else False

    # Build filter
    date_from = datetime.now() - timedelta(days=days)
    activity_filter = ActivityFilter(
        date_from=date_from,
        activity_type=activity_type,
        page_size=200,  # Max per page
    )

    # Fetch activities
    print(f"Fetching activities from last {days} days...")
    if activity_type:
        print(f"Filter: {activity_type} only")

    try:
        activities = client.list_activities(activity_filter)
    except Exception as e:
        logger.exception("Failed to fetch activities")
        print(f"Error fetching activities: {e}")
        return

    if not activities:
        print("No activities found matching criteria")
        return

    print(f"Found {len(activities)} activities")

    # Dry run mode
    if dry_run:
        print("\n--- Dry Run Mode ---")
        print("The following activities would be synced:\n")
        for i, activity in enumerate(activities, 1):
            print(f"{i:3d}. {activity.name}")
            print(f"     Type: {activity.activity_type}")
            print(f"     Date: {activity.start_date.strftime('%Y-%m-%d %H:%M:%S')}")
            if activity.distance_km:
                print(f"     Distance: {activity.distance_km:.2f} km")
            if activity.average_heartrate:
                print(f"     HR: {activity.average_heartrate:.0f} bpm")
            print()

        print(f"Total: {len(activities)} activities")
        print("\nRun without --dry-run to actually sync")
        return

    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    # Process each activity
    print(f"\n--- Syncing {len(activities)} Activities ---")

    success_count = 0
    skip_count = 0
    tagged_count = 0
    link_count = 0
    error_count = 0

    # Use database session for imports
    with get_db(url=config.url) as db:
        manager = ActivityManager(db)

        for i, activity_summary in enumerate(activities, 1):
            print(f"\n[{i}/{len(activities)}] {activity_summary.name}")
            print(f"  Type: {activity_summary.activity_type}")
            print(f"  Date: {activity_summary.start_date.strftime('%Y-%m-%d %H:%M')}")

            # Check if already exists
            strava_id = str(activity_summary.id)
            if skip_existing and manager.get_by_strava_id(strava_id):
                print(f"  ⊘ Already exists in database (Strava ID: {strava_id})")
                skip_count += 1
                continue

            # Fetch full activity data with streams
            try:
                activity = client.get_activity(activity_summary.id)
                streams = client.get_activity_streams(activity_summary.id)
            except Exception as e:
                logger.exception(f"Failed to fetch activity {activity_summary.id}")
                print(f"  ✗ Fetch failed: {e}")
                error_count += 1
                continue

            # Convert to ActivityData
            try:
                activity_data = StravaToActivityConverter.convert(activity, streams)
            except Exception as e:
                logger.exception(f"Failed to convert activity {activity_summary.id}")
                print(f"  ✗ Conversion failed: {e}")
                error_count += 1
                continue

            # Determine if this is an onsen monitoring session
            is_onsen_monitoring = False
            visit_id = None

            # Auto-tag based on pattern
            if auto_tag_pattern and auto_tag_pattern.lower() in activity.name.lower():
                is_onsen_monitoring = True
                tagged_count += 1
                print(f"  🏷️  Auto-tagged as onsen monitoring (pattern: '{auto_tag_pattern}')")

            # Interactive tagging
            elif interactive:
                response = input("  ❓ Is this an onsen monitoring session? (y/n): ").lower()
                if response == "y":
                    is_onsen_monitoring = True
                    tagged_count += 1

                    # Ask if they want to link to a visit
                    if auto_link:
                        # Search for nearby visits based on activity end time
                        from src.db.models import OnsenVisit
                        search_window = timedelta(hours=2)
                        search_start = activity.start_date_local - search_window
                        search_end = activity.start_date_local + search_window

                        nearby_visits = (
                            db.query(OnsenVisit)
                            .filter(
                                OnsenVisit.visit_time >= search_start,
                                OnsenVisit.visit_time <= search_end,
                            )
                            .all()
                        )

                        if nearby_visits:
                            print("\n  Nearby visits:")
                            suggestions = []
                            for visit in nearby_visits:
                                time_diff = abs(
                                    (visit.visit_time - activity.start_date_local).total_seconds()
                                    / 60
                                )
                                onsen_name = visit.onsen.name if visit.onsen else "Unknown"
                                desc = f"{visit.visit_time.strftime('%Y-%m-%d %H:%M')} - {onsen_name}"
                                suggestions.append((visit.id, desc, int(time_diff)))

                            # Sort by proximity
                            suggestions.sort(key=lambda x: x[2])

                            for j, (vid, desc, mins) in enumerate(suggestions[:5], 1):
                                print(f"    {j}. {desc} ({mins} min away)")
                            print(f"    {len(suggestions) + 1}. Skip linking")

                            link_choice = input(f"  Link to visit (1-{len(suggestions) + 1})?: ")
                            try:
                                choice_idx = int(link_choice) - 1
                                if 0 <= choice_idx < len(suggestions):
                                    visit_id = suggestions[choice_idx][0]
                            except (ValueError, IndexError):
                                pass

            # Store activity
            try:
                stored = manager.store_activity(
                    activity_data,
                    is_onsen_monitoring=is_onsen_monitoring,
                    visit_id=visit_id,
                )
                success_count += 1
                print(f"  ✓ Imported (ID: {stored.id}, Strava: {strava_id})")

                if is_onsen_monitoring:
                    print(f"  🏷️  Tagged as onsen monitoring")
                if visit_id:
                    print(f"  🔗 Linked to visit {visit_id}")
                    link_count += 1

            except ValueError as e:
                # Activity already exists
                if "already exists" in str(e):
                    print(f"  ⊘ Already exists: {e}")
                    skip_count += 1
                else:
                    logger.exception(f"Failed to store activity {activity_summary.id}")
                    print(f"  ✗ Storage failed: {e}")
                    error_count += 1
            except Exception as e:
                logger.exception(f"Failed to store activity {activity_summary.id}")
                print(f"  ✗ Storage failed: {e}")
                error_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("Sync Complete")
    print("=" * 60)
    print(f"Total activities: {len(activities)}")
    print(f"Successfully imported: {success_count}")
    print(f"Skipped (already exists): {skip_count}")
    print(f"Errors: {error_count}")
    if tagged_count:
        print(f"Tagged as onsen monitoring: {tagged_count}")
    if link_count:
        print(f"Linked to visits: {link_count}")
    print("=" * 60)


def configure_args(parser):
    """Configure argument parser for sync command."""
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Sync activities from last N days (default: 7)",
    )
    parser.add_argument(
        "--type",
        type=str,
        help="Only sync specific activity type (Run, Ride, Hike, etc.)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt to tag activities as onsen monitoring",
    )
    parser.add_argument(
        "--auto-tag-pattern",
        type=str,
        help="Auto-tag activities with name matching pattern (case-insensitive)",
    )
    parser.add_argument(
        "--auto-link",
        action="store_true",
        help="Suggest linking tagged activities to nearby visits",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without importing",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip activities that already exist in database",
    )
