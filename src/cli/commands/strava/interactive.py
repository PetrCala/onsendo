"""
Interactive browser command for Strava integration.

Provides a full-featured terminal UI for browsing, downloading, importing,
and linking Strava activities.
"""

# pylint: disable=bad-builtin

from src.lib.strava_browser import StravaActivityBrowser
from src.lib.strava_client import StravaClient
from src.types.strava import StravaSettings


def cmd_strava_interactive(args, db_session):
    """
    Launch interactive Strava activity browser.

    The interactive browser provides a terminal UI for:
    - Browsing your Strava activities with filters
    - Viewing detailed activity information
    - Downloading activities in multiple formats (GPX, JSON, CSV)
    - Importing activities as exercise sessions or heart rate data
    - Linking activities to onsen visits

    Usage:
        poetry run onsendo strava interactive

    Commands in browser:
        [s]elect   - Select activities for batch actions
        [d]etails  - View detailed information about an activity
        [a]ctions  - Perform actions on selected activities
        [n]ext     - Navigate to next page
        [p]rev     - Navigate to previous page
        [f]ilter   - Change filter criteria
        [c]lear    - Clear current selection
        [q]uit     - Exit browser

    Actions available:
        1. Download only - Save activity files locally
        2. Download + Import as Exercise - Import workout data
        3. Download + Import as Heart Rate - Import HR data only
        4. Download + Import + Auto-link - Suggest visits based on time
        5. Download + Import + Manual link - Choose visit to link

    Examples:
        # Launch browser (will prompt for filters)
        poetry run onsendo strava interactive

        # Common workflow:
        1. Set filters (e.g., last 7 days, running only)
        2. Browse activities
        3. Press 'd' and enter number to view details
        4. Press 's' and enter numbers to select (e.g., "1,3,5")
        5. Press 'a' to perform actions on selected activities
        6. Choose download + import + auto-link option
        7. System will suggest matching visits to link

    Requirements:
        - You must authenticate first: poetry run onsendo strava auth
        - For linking, you need existing onsen visits in database
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

        # Check authentication
        if not client.is_authenticated():
            print("You are not authenticated with Strava.")
            print("Please run: poetry run onsendo strava auth")
            return

    except Exception as e:
        print(f"Error initializing Strava client: {e}")
        return

    # Launch browser
    try:
        browser = StravaActivityBrowser(client, db_session)
        browser.run()
    except KeyboardInterrupt:
        print("\n\nBrowser interrupted by user.")
    except Exception as e:
        print(f"\nError in browser: {e}")
        import traceback

        traceback.print_exc()


def configure_args(parser):
    """Configure argument parser for interactive command."""
    # No additional arguments needed - all configuration is interactive
    parser.description = "Launch interactive Strava activity browser"
