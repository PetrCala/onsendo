"""
Strava browse command.

Browse and list Strava activities with filtering and pagination.
"""

# pylint: disable=bad-builtin

from datetime import datetime, timedelta

from loguru import logger

from src.lib.strava_client import StravaClient
from src.types.strava import ActivityFilter, StravaSettings


def cmd_strava_browse(args):
    """
    Browse Strava activities with filtering.

    Displays a formatted list of activities with optional filtering
    by date range, activity type, and other criteria.

    Usage:
        poetry run onsendo strava browse
        poetry run onsendo strava browse --days 30
        poetry run onsendo strava browse --type running
        poetry run onsendo strava browse --date-from 2025-10-01
        poetry run onsendo strava browse --has-hr
        poetry run onsendo strava browse --min-distance 5

    Arguments:
        --days N: Show activities from last N days
        --type TYPE: Filter by activity type (Run, Ride, Hike, etc.)
        --date-from DATE: Start date (YYYY-MM-DD)
        --date-to DATE: End date (YYYY-MM-DD)
        --has-hr: Only show activities with heart rate data
        --min-distance KM: Minimum distance in kilometers
        --page N: Page number (default: 1)
        --page-size N: Activities per page (default: 30, max: 200)
    """
    logger.info("Strava browse command")

    print("\n" + "=" * 70)
    print("Strava Activities")
    print("=" * 70)

    # Load settings
    try:
        settings = StravaSettings.from_env()
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease run: poetry run onsendo strava auth")
        print("")
        return 1

    # Create client
    client = StravaClient(
        credentials=settings.credentials, token_path=settings.token_path
    )

    # Check authentication
    if not client.is_authenticated():
        print("\n❌ Not authenticated")
        print("\nPlease run: poetry run onsendo strava auth")
        print("")
        return 1

    # Build filter from arguments
    activity_filter = _build_filter_from_args(args)

    # Display filter settings
    _display_filter_settings(activity_filter)

    # Fetch activities
    print("\nFetching activities...")

    try:
        activities = client.list_activities(activity_filter)

        if not activities:
            print("\n❌ No activities found matching your filters.")
            print("\nTry:")
            print("  • Expanding date range (--days 30)")
            print("  • Removing filters")
            print("  • Check your Strava account has activities")
            print("")
            return 0

        # Display activities
        _display_activities(activities, activity_filter.page, activity_filter.page_size)

        # Show pagination info
        if len(activities) == activity_filter.page_size:
            print(f"\n💡 Showing page {activity_filter.page}")
            print(f"   To see more: --page {activity_filter.page + 1}")

        print("")
        return 0

    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        print(f"\n❌ Error: {e}")
        print("")
        return 1


def _build_filter_from_args(args) -> ActivityFilter:
    """
    Build ActivityFilter from command-line arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        ActivityFilter instance
    """
    # Date range
    date_from = None
    date_to = None

    # Handle --days flag (takes precedence)
    if hasattr(args, "days") and args.days:
        date_from = datetime.now() - timedelta(days=args.days)
        date_to = datetime.now()

    # Handle explicit date-from/date-to
    if hasattr(args, "date_from") and args.date_from:
        date_from = datetime.strptime(args.date_from, "%Y-%m-%d")

    if hasattr(args, "date_to") and args.date_to:
        date_to = datetime.strptime(args.date_to, "%Y-%m-%d")

    # Activity type
    activity_type = None
    if hasattr(args, "type") and args.type:
        # Capitalize first letter (Run, Ride, Hike, etc.)
        activity_type = args.type.capitalize()

    # Heart rate filter
    has_heartrate = None
    if hasattr(args, "has_hr") and args.has_hr:
        has_heartrate = True

    # Minimum distance
    min_distance_km = None
    if hasattr(args, "min_distance") and args.min_distance:
        min_distance_km = float(args.min_distance)

    # Pagination
    page = getattr(args, "page", 1)
    page_size = getattr(args, "page_size", 30)

    return ActivityFilter(
        date_from=date_from,
        date_to=date_to,
        activity_type=activity_type,
        has_heartrate=has_heartrate,
        min_distance_km=min_distance_km,
        page=page,
        page_size=page_size,
    )


def _display_filter_settings(activity_filter: ActivityFilter) -> None:
    """Display current filter settings."""
    print("\nFilter Settings:")
    print("-" * 70)

    # Date range
    if activity_filter.date_from or activity_filter.date_to:
        from_str = (
            activity_filter.date_from.strftime("%Y-%m-%d")
            if activity_filter.date_from
            else "earliest"
        )
        to_str = (
            activity_filter.date_to.strftime("%Y-%m-%d")
            if activity_filter.date_to
            else "latest"
        )
        print(f"  Date range: {from_str} to {to_str}")
    else:
        print("  Date range: All time")

    # Activity type
    if activity_filter.activity_type:
        print(f"  Activity type: {activity_filter.activity_type}")
    else:
        print("  Activity type: All")

    # Heart rate
    if activity_filter.has_heartrate:
        print("  Heart rate: Required")

    # Minimum distance
    if activity_filter.min_distance_km:
        print(f"  Minimum distance: {activity_filter.min_distance_km}km")

    print("-" * 70)


def _display_activities(activities: list, page: int, page_size: int) -> None:
    """
    Display formatted activity list.

    Args:
        activities: List of StravaActivitySummary objects
        page: Current page number
        page_size: Activities per page
    """
    print(f"\n✓ Found {len(activities)} activities (Page {page})")
    print("=" * 70)

    for i, activity in enumerate(activities, 1):
        # Format activity details
        date_str = activity.start_date.strftime("%Y-%m-%d")
        time_str = activity.start_date.strftime("%H:%M")

        # Distance
        if activity.distance_km:
            dist_str = f"{activity.distance_km:.1f}km"
        else:
            dist_str = "--"

        # Duration
        duration_mins = activity.moving_time_minutes
        if duration_mins >= 60:
            hours = duration_mins // 60
            mins = duration_mins % 60
            duration_str = f"{hours}h{mins:02d}m"
        else:
            duration_str = f"{duration_mins}m"

        # Heart rate
        hr_str = ""
        if activity.has_heartrate and activity.average_heartrate:
            hr_str = f"♥ {int(activity.average_heartrate)}bpm"

        # Elevation
        elev_str = ""
        if activity.total_elevation_gain_m:
            elev_str = f"▲ {int(activity.total_elevation_gain_m)}m"

        # Display line 1: Index, name, date, distance, HR
        print(f"  {i:2}. {activity.name:<35} {date_str}  {dist_str:>8}  {hr_str}")

        # Display line 2: Time, duration, elevation
        time_info = f"{time_str} ({duration_str})"
        print(f"      {activity.activity_type:<35} {time_info:<20} {elev_str}")

        # Blank line between activities
        if i < len(activities):
            print()

    print("=" * 70)
