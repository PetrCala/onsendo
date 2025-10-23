"""
Strava authentication command.

Handles OAuth2 authentication flow with Strava API.
"""

# pylint: disable=bad-builtin

from datetime import datetime

from loguru import logger

from src.lib.strava_client import StravaClient
from src.types.strava import StravaAuthenticationError, StravaSettings


def cmd_strava_auth(args, db_session):
    """
    Authenticate with Strava API.

    Opens browser for OAuth2 authorization flow.
    Saves access token for future use.

    Usage:
        poetry run onsendo strava auth
        poetry run onsendo strava auth --reauth  # Force re-authentication

    Arguments:
        --reauth: Force re-authentication even if already authenticated
    """
    logger.info("Strava authentication command")

    print("\n" + "=" * 60)
    print("Strava Authentication")
    print("=" * 60)

    # Load settings from environment
    try:
        settings = StravaSettings.from_env()
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}\n")
        print("Setup Instructions:")
        print("1. Go to https://www.strava.com/settings/api")
        print("2. Create an application (if you don't have one)")
        print("3. Add to your .env file:")
        print("   STRAVA_CLIENT_ID=your_client_id")
        print("   STRAVA_CLIENT_SECRET=your_client_secret")
        print("")
        return 1

    # Create client
    client = StravaClient(
        credentials=settings.credentials, token_path=settings.token_path
    )

    # Check if already authenticated (unless --reauth flag is set)
    if hasattr(args, "reauth") and args.reauth:
        print("\n🔄 Re-authentication requested")
    elif client.is_authenticated():
        token_info = client.get_token_info()
        expires_at = datetime.fromisoformat(token_info["expires_at"])

        print("\n✓ Already authenticated!")
        print(f"Token expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nTo force re-authentication, use:")
        print("  poetry run onsendo strava auth --reauth")
        print("")
        return 0

    # Show information
    print("\nThis will open your browser to authorize Onsendo to access")
    print("your Strava activities.")
    print("\nRequired permissions:")
    print("  • Read your activity data")
    print("  • Read your profile information")
    print("\nYour credentials will be stored securely in:")
    print(f"  {settings.token_path}")
    print("")

    # Prompt for confirmation
    response = input("Press Enter to continue or Ctrl+C to cancel... ")

    # Perform authentication
    try:
        success = client.authenticate()

        if success:
            token_info = client.get_token_info()
            expires_at = datetime.fromisoformat(token_info["expires_at"])

            print("\n" + "=" * 60)
            print("✓ Authorization successful!")
            print("=" * 60)
            print(f"✓ Token saved to {settings.token_path}")
            print(f"✓ Token expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print("\nYou can now use Strava commands:")
            print("  • poetry run onsendo strava browse")
            print("  • poetry run onsendo strava sync --days 7")
            print("  • poetry run onsendo strava status")
            print("")
            return 0
        else:
            print("\n❌ Authentication failed")
            return 1

    except StravaAuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check that your Client ID and Secret are correct")
        print("2. Verify the redirect URI in your Strava app settings:")
        print(f"   {settings.redirect_uri}")
        print("3. Make sure you approved the authorization in the browser")
        print("")
        return 1

    except KeyboardInterrupt:
        print("\n\n❌ Authentication cancelled by user")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        print(f"\n❌ Unexpected error: {e}")
        return 1
