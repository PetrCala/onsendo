"""
Download command for Strava integration.

Provides quick download of specific Strava activities with optional import and linking.
"""

from pathlib import Path

from loguru import logger

from src.config import get_database_config
from src.db.conn import get_db
from src.lib.exercise_manager import ExerciseDataManager
from src.lib.heart_rate_manager import HeartRateDataManager
from src.lib.strava_client import StravaClient
from src.lib.strava_converter import (
    StravaFileExporter,
    StravaToExerciseConverter,
    StravaToHeartRateConverter,
)
from src.paths import PATHS
from src.types.strava import StravaSettings


def cmd_strava_download(args):
    """
    Download specific Strava activity by ID.

    Downloads activity in specified format(s) and optionally imports
    and links to onsen visits.

    Usage:
        poetry run onsendo strava download 12345678
        poetry run onsendo strava download 12345678 --format gpx
        poetry run onsendo strava download 12345678 --format json --import
        poetry run onsendo strava download 12345678 --import --link-visit 42
        poetry run onsendo strava download 12345678 --import --auto-link

    Arguments:
        activity_id: Strava activity ID
        --format FORMAT: Output format (gpx, json, hr_csv, all) [default: all]
        --import: Import after downloading as exercise session
        --import-hr: Import after downloading as heart rate data
        --link-visit ID: Link to specific visit after import
        --auto-link: Auto-link to nearby visit based on timestamp

    Examples:
        # Download activity in all formats
        poetry run onsendo strava download 12345678

        # Download GPX only
        poetry run onsendo strava download 12345678 --format gpx

        # Download and import as exercise
        poetry run onsendo strava download 12345678 --import

        # Download, import, and link to specific visit
        poetry run onsendo strava download 12345678 --import --link-visit 42

        # Download, import, and auto-link to nearby visit
        poetry run onsendo strava download 12345678 --import --auto-link
    """
    activity_id = args.activity_id

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

    # Fetch activity and streams first
    print(f"Fetching activity {activity_id}...")
    try:
        activity = client.get_activity(activity_id)
        streams = client.get_activity_streams(activity_id)
    except Exception as e:
        logger.exception("Failed to fetch activity")
        print(f"Error fetching activity: {e}")
        return

    print(f"\nActivity: {activity.name}")
    print(f"Type: {activity.activity_type}")
    print(f"Date: {activity.start_date_local.strftime('%Y-%m-%d %H:%M:%S')}")

    # Determine requested formats
    format_arg = args.format if hasattr(args, "format") and args.format else "all"
    if format_arg == "all":
        requested_formats = ["gpx", "json", "hr_csv"]
    else:
        requested_formats = [format_arg]

    # Smart format selection based on available data
    exportable_formats, skipped_formats = StravaFileExporter.recommend_formats(
        streams, requested_formats
    )

    # Inform user about format selection
    print(f"\nExporting in formats: {', '.join(exportable_formats)}")
    if skipped_formats:
        for fmt, reason in skipped_formats:
            print(f"  ⊘ Skipping {fmt.upper()}: {reason}")

    # Prepare output directory and filename
    output_dir = PATHS.STRAVA_ACTIVITY_DIR.value
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    safe_name = "".join(
        c if c.isalnum() or c in (" ", "_", "-") else "_" for c in activity.name
    )
    safe_name = safe_name.strip()[:50]
    timestamp = activity.start_date_local.strftime("%Y%m%d_%H%M%S")
    base_filename = f"{timestamp}_{safe_name}_{activity_id}"

    file_paths = {}

    # Export in recommended formats
    try:
        if "gpx" in exportable_formats:
            gpx_path = Path(output_dir) / f"{base_filename}.gpx"
            StravaFileExporter.export_to_gpx(activity, streams, gpx_path)
            file_paths["gpx"] = str(gpx_path)
            print(f"  ✓ GPX: {gpx_path}")

        if "json" in exportable_formats:
            json_path = Path(output_dir) / f"{base_filename}.json"
            StravaFileExporter.export_to_json(activity, streams, json_path)
            file_paths["json"] = str(json_path)
            print(f"  ✓ JSON: {json_path}")

        if "hr_csv" in exportable_formats:
            csv_path = Path(output_dir) / f"{base_filename}_hr.csv"
            StravaFileExporter.export_hr_to_csv(
                activity, streams["heartrate"], streams.get("time"), csv_path
            )
            file_paths["hr_csv"] = str(csv_path)
            print(f"  ✓ HR CSV: {csv_path}")

    except Exception as e:
        logger.exception("Failed to export files")
        print(f"\nError exporting files: {e}")
        return

    # Import if requested
    import_exercise = args.import_flag if hasattr(args, "import_flag") else False
    import_hr = args.import_hr if hasattr(args, "import_hr") else False

    exercise_id = None
    hr_id = None

    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Use database session for imports and linking
    with get_db(url=config.url) as db:
        if import_exercise:
            print("\nImporting as exercise session...")
            try:
                session = StravaToExerciseConverter.convert(activity, streams)
                manager = ExerciseDataManager(db)
                stored = manager.store_session(session)
                exercise_id = stored.id
                print(f"  ✓ Imported exercise session (ID: {exercise_id})")
            except Exception as e:
                logger.exception("Failed to import as exercise")
                print(f"  ✗ Import failed: {e}")
                return

        if import_hr:
            if "heartrate" in streams:
                print("\nImporting as heart rate data...")
                try:
                    hr_session = StravaToHeartRateConverter.convert(
                        activity, streams["heartrate"]
                    )
                    hr_manager = HeartRateDataManager(db)
                    stored_hr = hr_manager.store_session(hr_session)
                    hr_id = stored_hr.id
                    print(f"  ✓ Imported heart rate data (ID: {hr_id})")
                except Exception as e:
                    logger.exception("Failed to import as heart rate")
                    print(f"  ✗ Import failed: {e}")
            else:
                print("\n  ⚠ Activity does not have heart rate data")

        # Link if requested
        link_visit = (
            args.link_visit if hasattr(args, "link_visit") and args.link_visit else None
        )
        auto_link = args.auto_link if hasattr(args, "auto_link") else False

        if exercise_id and (link_visit or auto_link):
            print("\nLinking to visit...")

            if auto_link:
                # Auto-suggest visits
                from src.db.models import OnsenVisit
                from datetime import timedelta

                search_start = activity.start_date_local - timedelta(hours=2)
                search_end = activity.start_date_local + timedelta(hours=2)

                visits = (
                    db.query(OnsenVisit)
                    .filter(OnsenVisit.visit_date >= search_start.date())
                    .filter(OnsenVisit.visit_date <= search_end.date())
                    .order_by(
                        OnsenVisit.visit_date.desc(), OnsenVisit.visit_time.desc()
                    )
                    .limit(5)
                    .all()
                )

                if visits:
                    print("  Suggested visits:")
                    for i, visit in enumerate(visits, 1):
                        from datetime import datetime

                        visit_datetime = datetime.combine(
                            visit.visit_date, visit.visit_time or datetime.min.time()
                        )
                        time_diff = abs(
                            (visit_datetime - activity.start_date_local).total_seconds()
                            / 60
                        )
                        print(
                            f"    {i}. [ID: {visit.id}] {visit.visit_date} "
                            f"at {visit.visit_time or 'N/A'} ({time_diff:.0f} min from activity)"
                        )

                    # Use first suggestion
                    link_visit = visits[0].id
                    print(f"  Using suggestion: Visit ID {link_visit}")
                else:
                    print("  No nearby visits found (±2 hours)")
                    return

            # Link exercise to visit
            if link_visit:
                try:
                    manager = ExerciseDataManager(db)
                    manager.link_to_visit(exercise_id, link_visit)
                    print(f"  ✓ Linked exercise {exercise_id} to visit {link_visit}")
                except Exception as e:
                    logger.exception("Failed to link to visit")
                    print(f"  ✗ Link failed: {e}")

    print("\n✓ Download complete")


def configure_args(parser):
    """Configure argument parser for download command."""
    parser.add_argument(
        "activity_id",
        type=int,
        help="Strava activity ID to download",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["gpx", "json", "hr_csv", "all"],
        default="all",
        help="Output format (default: all)",
    )
    parser.add_argument(
        "--import",
        dest="import_flag",
        action="store_true",
        help="Import as exercise session after downloading",
    )
    parser.add_argument(
        "--import-hr",
        action="store_true",
        help="Import as heart rate data after downloading",
    )
    parser.add_argument(
        "--link-visit",
        type=int,
        help="Link to specific visit ID after import",
    )
    parser.add_argument(
        "--auto-link",
        action="store_true",
        help="Auto-link to nearby visit based on timestamp",
    )
