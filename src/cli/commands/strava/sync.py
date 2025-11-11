"""
Sync command for Strava integration - Unified Activity System.

Provides batch synchronization of recent Strava activities with automatic
detection and interactive review of onsen monitoring sessions.
"""

# pylint: disable=bad-builtin

from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from src.config import get_database_config
from src.db.conn import get_db
from src.db.models import Activity
from src.lib.activity_manager import ActivityManager
from src.lib.activity_visit_pairer import PairingConfig, pair_activities_to_visits
from src.lib.strava_client import StravaClient
from src.lib.strava_converter import StravaToActivityConverter
from src.paths import PATHS
from src.types.exercise import ExerciseType
from src.types.strava import ActivityFilter, StravaSettings


def cmd_strava_sync(args):
    """
    Batch sync recent Strava activities using unified activity system.

    Downloads and imports Strava activities with automatic detection of onsen
    monitoring sessions. Optionally review and correct auto-detected activities.

    Usage:
        poetry run onsendo strava sync
        poetry run onsendo strava sync --days 7
        poetry run onsendo strava sync --days 30 --interactive
        poetry run onsendo strava sync --type Run --days 30
        poetry run onsendo strava sync --dry-run

    Arguments:
        --days N: Sync activities from last N days (default: 7)
        --type TYPE: Only sync specific activity type (Run, Ride, etc.)
        --interactive: Enable post-sync review of auto-detected onsen monitoring activities
        --auto-link: Enable visit linking during interactive review
        --no-auto-pair: Disable automatic activity-visit pairing (enabled by default)
        --pairing-threshold: Confidence threshold for auto-pairing (default: 0.8)
        --dry-run: Show what would be synced without importing
        --skip-existing: Skip activities that already exist in database

    Auto-Detection:
        Activities are automatically detected as onsen monitoring if:
        - Activity name contains "onsendo" (case-insensitive) AND "88"
        - Route data shows stationary HR monitoring (no movement, has HR)

    Examples:
        # Sync last 7 days with auto-detection
        poetry run onsendo strava sync

        # Sync with interactive review of detected activities
        poetry run onsendo strava sync --days 30 --interactive

        # Sync with interactive review and visit linking
        poetry run onsendo strava sync --days 14 --interactive --auto-link

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
    auto_link = args.auto_link if hasattr(args, "auto_link") else False
    auto_pair = not (args.no_auto_pair if hasattr(args, "no_auto_pair") else False)
    pairing_threshold = args.pairing_threshold if args.pairing_threshold is not None else 0.8
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
    onsen_monitoring_count = 0
    link_count = 0
    error_count = 0
    imported_activity_ids = []

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

                # Skip stream fetching for manual activities (they don't have streams)
                if activity.manual:
                    print(f"  ℹ Manual activity - skipping stream data")
                    streams = None
                else:
                    streams = client.get_activity_streams(activity_summary.id)
            except Exception as e:
                logger.exception(f"Failed to fetch activity {activity_summary.id}")
                print(f"  ✗ Fetch failed: {e}")
                error_count += 1
                continue

            # Convert to ActivityData (auto-detection happens here)
            try:
                activity_data = StravaToActivityConverter.convert(activity, streams)
            except Exception as e:
                logger.exception(f"Failed to convert activity {activity_summary.id}")
                print(f"  ✗ Conversion failed: {e}")
                error_count += 1
                continue

            # Check if auto-detected as onsen monitoring
            is_onsen = activity_data.activity_type == ExerciseType.ONSEN_MONITORING.value
            if is_onsen:
                onsen_monitoring_count += 1
                print(f"  🔍 Auto-detected as onsen monitoring")

            # Store activity
            try:
                stored = manager.store_activity(activity_data)
                success_count += 1
                imported_activity_ids.append(stored.id)
                print(f"  ✓ Imported (ID: {stored.id}, Strava: {strava_id})")

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

        # Auto-pair onsen monitoring activities to visits
        if auto_pair and onsen_monitoring_count > 0:
            print("\n" + "=" * 60)
            print("Auto-Pairing Activities to Visits")
            print("=" * 60)

            # Get IDs of newly imported onsen monitoring activities
            onsen_activity_ids = (
                db.query(Activity.id)
                .filter(
                    Activity.id.in_(imported_activity_ids),
                    Activity.activity_type == ExerciseType.ONSEN_MONITORING.value,
                    Activity.visit_id.is_(None)  # Only unlinked activities
                )
                .all()
            )
            onsen_activity_ids = [aid[0] for aid in onsen_activity_ids]

            if onsen_activity_ids:
                print(f"Attempting to pair {len(onsen_activity_ids)} onsen monitoring activities...")

                # Configure pairing
                pairing_config = PairingConfig(
                    auto_link_threshold=pairing_threshold,
                    review_threshold=0.6,
                    time_window_hours=4,
                )

                # Run pairing
                pairing_results = pair_activities_to_visits(db, onsen_activity_ids, pairing_config)

                # Apply auto-links
                for activity, visit, confidence in pairing_results.auto_linked:
                    try:
                        manager.link_to_visit(activity.id, visit.id)
                        onsen_name = visit.onsen.name if visit.onsen else "Unknown"
                        print(f"  ✓ Linked: Activity '{activity.activity_name}' → Visit '{onsen_name}' (confidence: {confidence:.1%})")
                        link_count += 1
                    except Exception as e:
                        logger.exception(f"Failed to link activity {activity.id} to visit {visit.id}")
                        print(f"  ✗ Link failed: {e}")

                # Show manual review needed
                if pairing_results.manual_review:
                    print(f"\n  ⚠ {len(pairing_results.manual_review)} activities need manual review (confidence 60-{int(pairing_threshold*100)}%)")
                    for activity, candidates in pairing_results.manual_review:
                        if candidates:
                            best = candidates[0]
                            print(f"    - '{activity.activity_name}': Best match '{best.onsen_name}' ({best.combined_score:.1%})")

                # Show no match
                if pairing_results.no_match:
                    print(f"\n  ⚠ {len(pairing_results.no_match)} activities could not be paired:")
                    for activity in pairing_results.no_match:
                        print(f"    - '{activity.activity_name}'")

                print(f"\nPairing summary: {len(pairing_results.auto_linked)} auto-linked, "
                      f"{len(pairing_results.manual_review)} need review, "
                      f"{len(pairing_results.no_match)} no match")

        # Post-sync review for onsen monitoring activities
        if onsen_monitoring_count > 0 and interactive:
            print("\n" + "=" * 60)
            print(f"Review Auto-Detected Onsen Monitoring Activities ({onsen_monitoring_count})")
            print("=" * 60)

            # Query newly imported onsen monitoring activities
            onsen_activities = (
                db.query(Activity)
                .filter(
                    Activity.id.in_(imported_activity_ids),
                    Activity.activity_type == ExerciseType.ONSEN_MONITORING.value
                )
                .order_by(Activity.start_time)
                .all()
            )

            if onsen_activities:
                review = input(f"\nWould you like to review these {len(onsen_activities)} activity/activities? (Y/n): ").lower()
                if review != "n":
                    for activity in onsen_activities:
                        print(f"\n--- Activity #{activity.id} ---")
                        print(f"Name: {activity.activity_name}")
                        print(f"Date: {activity.start_time.strftime('%Y-%m-%d %H:%M')}")
                        print(f"Type: {activity.activity_type}")
                        if activity.avg_heart_rate:
                            print(f"Avg HR: {activity.avg_heart_rate:.0f} bpm")

                        action = input("Action - (K)eep as onsen monitoring, (C)hange type, (L)ink to visit, (S)kip: ").lower()

                        if action == "c":
                            # Show available types
                            print("\nAvailable types:")
                            for i, ex_type in enumerate(ExerciseType, 1):
                                print(f"  {i}. {ex_type.value}")

                            try:
                                type_choice = input(f"Select type (1-{len(ExerciseType)}): ")
                                type_idx = int(type_choice) - 1
                                types_list = list(ExerciseType)
                                if 0 <= type_idx < len(types_list):
                                    new_type = types_list[type_idx]
                                    activity.activity_type = new_type.value
                                    db.commit()
                                    print(f"  ✓ Changed to {new_type.value}")
                            except (ValueError, IndexError):
                                print("  ✗ Invalid selection, skipping")

                        elif action == "l":
                            # Link to visit
                            if auto_link:
                                from src.db.models import OnsenVisit
                                search_window = timedelta(hours=2)
                                search_start = activity.start_time - search_window
                                search_end = activity.start_time + search_window

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
                                    for j, visit in enumerate(nearby_visits[:5], 1):
                                        onsen_name = visit.onsen.name if visit.onsen else "Unknown"
                                        time_diff = abs((visit.visit_time - activity.start_time).total_seconds() / 60)
                                        print(f"    {j}. {visit.visit_time.strftime('%Y-%m-%d %H:%M')} - {onsen_name} ({int(time_diff)} min away)")

                                    link_choice = input(f"  Select visit (1-{len(nearby_visits[:5])}), or enter to skip: ")
                                    try:
                                        if link_choice.strip():
                                            choice_idx = int(link_choice) - 1
                                            if 0 <= choice_idx < len(nearby_visits[:5]):
                                                visit_id = nearby_visits[choice_idx].id
                                                manager.link_to_visit(activity.id, visit_id)
                                                print(f"  ✓ Linked to visit {visit_id}")
                                                link_count += 1
                                    except (ValueError, IndexError):
                                        print("  ✗ Invalid selection, skipping")
                                else:
                                    print("  No nearby visits found")
                            else:
                                print("  --auto-link flag not set, skipping link")

                        elif action == "k" or action == "s":
                            continue  # Keep as is or skip

    # Summary
    print("\n" + "=" * 60)
    print("Sync Complete")
    print("=" * 60)
    print(f"Total activities: {len(activities)}")
    print(f"Successfully imported: {success_count}")
    print(f"Skipped (already exists): {skip_count}")
    print(f"Errors: {error_count}")
    if onsen_monitoring_count:
        print(f"Auto-detected onsen monitoring: {onsen_monitoring_count}")
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
        help="Enable post-sync review of auto-detected onsen monitoring activities",
    )
    parser.add_argument(
        "--auto-link",
        action="store_true",
        help="Enable visit linking during interactive review",
    )
    parser.add_argument(
        "--no-auto-pair",
        action="store_true",
        help="Disable automatic activity-visit pairing (enabled by default)",
    )
    parser.add_argument(
        "--pairing-threshold",
        type=float,
        default=0.8,
        help="Confidence threshold for auto-pairing (default: 0.8 = 80%%)",
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
