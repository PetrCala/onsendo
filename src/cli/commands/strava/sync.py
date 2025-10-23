"""
Sync command for Strava integration.

Provides batch synchronization of recent Strava activities with optional
auto-import and auto-linking.
"""

from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from src.db.conn import get_db

from src.db.models import OnsenVisit
from src.lib.exercise_manager import ExerciseDataManager
from src.lib.strava_client import StravaClient
from src.lib.strava_converter import StravaFileExporter, StravaToExerciseConverter
from src.paths import PATHS
from src.types.strava import ActivityFilter, StravaSettings


def cmd_strava_sync(args):
    """
    Batch sync recent Strava activities.

    Downloads and optionally imports multiple activities from a specified
    time period.

    Usage:
        poetry run onsendo strava sync
        poetry run onsendo strava sync --days 7
        poetry run onsendo strava sync --auto-import
        poetry run onsendo strava sync --auto-import --auto-link
        poetry run onsendo strava sync --type Run --days 30
        poetry run onsendo strava sync --dry-run

    Arguments:
        --days N: Sync activities from last N days (default: 7)
        --type TYPE: Only sync specific activity type (Run, Ride, etc.)
        --auto-import: Automatically import downloaded activities
        --auto-link: Automatically link to nearby visits
        --dry-run: Show what would be synced without downloading
        --format FORMAT: Download format (gpx, json, hr_csv, all) [default: gpx]

    Examples:
        # Sync last 7 days (download only)
        poetry run onsendo strava sync

        # Sync last 30 days, auto-import and link
        poetry run onsendo strava sync --days 30 --auto-import --auto-link

        # Sync only running activities from last 14 days
        poetry run onsendo strava sync --type Run --days 14 --auto-import

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
    auto_import = args.auto_import if hasattr(args, "auto_import") else False
    auto_link = args.auto_link if hasattr(args, "auto_link") else False
    dry_run = args.dry_run if hasattr(args, "dry_run") else False
    format_arg = args.format if hasattr(args, "format") and args.format else "gpx"

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
        if auto_import:
            print("Would auto-import: YES")
        if auto_link:
            print("Would auto-link: YES")
        print("\nRun without --dry-run to actually sync")
        return

    # Determine format
    if format_arg == "all":
        formats = ["gpx", "json", "hr_csv"]
    else:
        formats = [format_arg]

    # Process each activity
    print(f"\n--- Syncing {len(activities)} Activities ---")
    output_dir = PATHS.STRAVA_ACTIVITY_DIR.value
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    success_count = 0
    import_count = 0
    link_count = 0
    skip_count = 0

    # Use database session for imports and linking
    with get_db() as db:
        for i, activity_summary in enumerate(activities, 1):
            print(f"\n[{i}/{len(activities)}] {activity_summary.name}")

            # Check if already exists (simple check based on filename)
            timestamp = activity_summary.start_date.strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(
                c if c.isalnum() or c in (" ", "_", "-") else "_"
                for c in activity_summary.name
            )
            safe_name = safe_name.strip()[:50]
            base_filename = f"{timestamp}_{safe_name}_{activity_summary.id}"

            # Check if GPX file already exists
            gpx_path = Path(output_dir) / f"{base_filename}.gpx"
            if gpx_path.exists() and not auto_import:
                print(f"  ⊘ Already downloaded: {gpx_path.name}")
                skip_count += 1
                continue

            # Fetch full activity data
            try:
                activity = client.get_activity(activity_summary.id)
                streams = client.get_activity_streams(activity_summary.id)
            except Exception as e:
                logger.exception(f"Failed to fetch activity {activity_summary.id}")
                print(f"  ✗ Fetch failed: {e}")
                continue

            # Download files
            try:
                file_paths = {}

                if "gpx" in formats:
                    StravaFileExporter.export_to_gpx(activity, streams, gpx_path)
                    file_paths["gpx"] = str(gpx_path)
                    print(f"  ✓ Downloaded: {gpx_path.name}")

                if "json" in formats:
                    json_path = Path(output_dir) / f"{base_filename}.json"
                    StravaFileExporter.export_to_json(activity, streams, json_path)
                    file_paths["json"] = str(json_path)
                    print(f"  ✓ Downloaded: {json_path.name}")

                if "hr_csv" in formats and streams.get("heartrate"):
                    csv_path = Path(output_dir) / f"{base_filename}_hr.csv"
                    StravaFileExporter.export_hr_to_csv(
                        activity, streams["heartrate"], streams.get("time"), csv_path
                    )
                    file_paths["hr_csv"] = str(csv_path)
                    print(f"  ✓ Downloaded: {csv_path.name}")

                success_count += 1

            except Exception as e:
                logger.exception(f"Failed to export activity {activity_summary.id}")
                print(f"  ✗ Export failed: {e}")
                continue

            # Auto-import if requested
            exercise_id = None
            if auto_import:
                try:
                    session = StravaToExerciseConverter.convert(activity, streams)
                    manager = ExerciseDataManager(db)
                    stored = manager.store_session(session)
                    exercise_id = stored.id
                    print(f"  ✓ Imported (ID: {exercise_id})")
                    import_count += 1
                except Exception as e:
                    logger.exception(f"Failed to import activity {activity_summary.id}")
                    print(f"  ✗ Import failed: {e}")
                    continue

            # Auto-link if requested
            if auto_link and exercise_id:
                # Find nearby visits
                search_start = activity.start_date_local - timedelta(hours=2)
                search_end = activity.start_date_local + timedelta(hours=2)

                visits = (
                    db.query(OnsenVisit)
                    .filter(OnsenVisit.visit_date >= search_start.date())
                    .filter(OnsenVisit.visit_date <= search_end.date())
                    .order_by(OnsenVisit.visit_date.desc(), OnsenVisit.visit_time.desc())
                    .limit(1)
                    .all()
                )

                if visits:
                    visit = visits[0]
                    visit_datetime = datetime.combine(
                        visit.visit_date, visit.visit_time or datetime.min.time()
                    )
                    time_diff = abs(
                        (visit_datetime - activity.start_date_local).total_seconds() / 60
                    )

                    try:
                        manager = ExerciseDataManager(db)
                        manager.link_to_visit(exercise_id, visit.id)
                        print(
                            f"  ✓ Linked to visit {visit.id} "
                            f"({time_diff:.0f} min from activity)"
                        )
                        link_count += 1
                    except Exception as e:
                        logger.exception(f"Failed to link activity {activity_summary.id}")
                        print(f"  ✗ Link failed: {e}")

        # Summary
        print("\n" + "=" * 60)
        print("Sync Complete")
        print("=" * 60)
        print(f"Total activities: {len(activities)}")
        print(f"Downloaded: {success_count}")
        print(f"Skipped (already exists): {skip_count}")
        if auto_import:
            print(f"Imported: {import_count}")
        if auto_link:
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
        "--auto-import",
        action="store_true",
        help="Automatically import downloaded activities",
    )
    parser.add_argument(
        "--auto-link",
        action="store_true",
        help="Automatically link imported activities to nearby visits",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without downloading",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["gpx", "json", "hr_csv", "all"],
        default="gpx",
        help="Download format (default: gpx)",
    )
