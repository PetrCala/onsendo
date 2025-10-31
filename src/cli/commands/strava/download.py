"""
Download command for Strava integration.

Provides quick download of specific Strava activities in various formats.
"""

from pathlib import Path

from loguru import logger

from src.lib.strava_client import StravaClient
from src.lib.strava_converter import StravaFileExporter
from src.paths import PATHS
from src.types.strava import StravaSettings


def cmd_strava_download(args):
    """
    Download specific Strava activity by ID.

    Downloads activity in specified format(s). For importing activities,
    use 'strava sync' instead.

    Usage:
        poetry run onsendo strava download 12345678
        poetry run onsendo strava download 12345678 --format gpx

    Arguments:
        activity_id: Strava activity ID
        --format FORMAT: Output format (gpx, json, hr_csv, all) [default: all]

    Examples:
        # Download activity in all formats
        poetry run onsendo strava download 12345678

        # Download GPX only
        poetry run onsendo strava download 12345678 --format gpx

        # Download heart rate CSV
        poetry run onsendo strava download 12345678 --format hr_csv
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

    print("\n✓ Download complete")
    print("\nTo import activities into the database, use: poetry run onsendo strava sync")


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
