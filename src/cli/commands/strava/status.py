"""
Strava status command.

Check Strava API connection status and credentials.
"""

from datetime import datetime

from loguru import logger

from src.lib.strava_client import StravaClient
from src.types.strava import StravaSettings


def cmd_strava_status(args):
    """
    Check Strava API connection status.

    Displays:
    - Authentication status
    - Token expiration
    - Rate limit usage
    - Configuration

    Usage:
        poetry run onsendo strava status
        poetry run onsendo strava status --verbose

    Arguments:
        --verbose: Show detailed configuration and rate limit info
    """
    logger.info("Strava status command")

    verbose = hasattr(args, "verbose") and args.verbose

    print("\n" + "=" * 60)
    print("Strava Integration Status")
    print("=" * 60)

    # Load settings
    try:
        settings = StravaSettings.from_env()
        print("\n✓ Configuration loaded")

        if verbose:
            print(f"  Client ID: {settings.client_id[:10]}...")
            print(f"  Redirect URI: {settings.redirect_uri}")
            print(f"  Token path: {settings.token_path}")
            print(f"  Activity directory: {settings.activity_dir}")

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nSetup required:")
        print("  poetry run onsendo strava auth")
        print("")
        return 1

    # Create client and check authentication
    client = StravaClient(
        credentials=settings.credentials, token_path=settings.token_path
    )

    if not client.is_authenticated():
        print("\n❌ Not authenticated")
        print("\nTo authenticate, run:")
        print("  poetry run onsendo strava auth")
        print("")
        return 1

    # Show authentication status
    token_info = client.get_token_info()
    expires_at = datetime.fromisoformat(token_info["expires_at"])
    expires_in = token_info["expires_in_seconds"]

    print("\n✓ Authenticated")
    print(f"  Token expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")

    if expires_in > 3600:
        hours = expires_in // 3600
        print(f"  Time remaining: {hours} hours")
    elif expires_in > 0:
        mins = expires_in // 60
        print(f"  Time remaining: {mins} minutes")
    else:
        print("  Status: ⚠️  Expired (will auto-refresh on next API call)")

    # Show rate limit status
    if verbose:
        rate_status = client.get_rate_limit_status()

        print("\n📊 Rate Limit Status:")
        print(f"  15-minute window:")
        print(
            f"    Used: {rate_status['15min']['used']} / {rate_status['15min']['limit']}"
        )
        print(f"    Remaining: {rate_status['15min']['remaining']}")

        print(f"  Daily limit:")
        print(
            f"    Used: {rate_status['daily']['used']} / {rate_status['daily']['limit']}"
        )
        print(f"    Remaining: {rate_status['daily']['remaining']}")

    # Show available commands
    print("\n📋 Available Commands:")
    print("  • poetry run onsendo strava browse       - Browse activities")
    print("  • poetry run onsendo strava sync         - Sync recent activities")
    print("  • poetry run onsendo strava download     - Download activity by ID")

    print("")
    return 0
