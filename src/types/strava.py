"""
Strava integration type definitions.

This module defines all Strava-related types, enums, and data structures
used throughout the Onsendo Strava integration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Optional


class StravaError(Exception):
    """Base exception for Strava integration."""


class StravaAuthenticationError(StravaError):
    """Authentication or authorization failed."""


class StravaRateLimitError(StravaError):
    """API rate limit exceeded."""


class StravaNetworkError(StravaError):
    """Network connection or timeout error."""


class StravaConversionError(StravaError):
    """Data conversion failed."""


class StravaFileError(StravaError):
    """File system operation failed."""


class StravaActivityNotFoundError(StravaError):
    """Activity ID not found."""


@dataclass
class StravaCredentials:
    """
    Strava OAuth2 credentials.

    These are obtained from https://www.strava.com/settings/api
    after creating an application.
    """

    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8080/strava/callback"

    def validate(self) -> None:
        """
        Validate credentials are present.

        Raises:
            ValueError: If client_id or client_secret is empty
        """
        if not self.client_id:
            raise ValueError("Strava client_id is required")
        if not self.client_secret:
            raise ValueError("Strava client_secret is required")


@dataclass
class StravaToken:
    """
    Strava access token with refresh capability.

    Tokens expire after 6 hours but can be refreshed using the refresh_token.
    """

    access_token: str
    refresh_token: str
    expires_at: int  # Unix timestamp
    token_type: str = "Bearer"

    @property
    def is_expired(self) -> bool:
        """
        Check if token is expired.

        Returns:
            True if token has expired, False otherwise
        """
        current_timestamp = int(datetime.now().timestamp())
        # Add 60 second buffer to refresh before actual expiration
        return current_timestamp >= (self.expires_at - 60)

    @property
    def expires_in_seconds(self) -> int:
        """
        Get seconds until token expiration.

        Returns:
            Number of seconds until expiration (negative if already expired)
        """
        current_timestamp = int(datetime.now().timestamp())
        return self.expires_at - current_timestamp

    def to_dict(self) -> dict:
        """
        Serialize token to dictionary for storage.

        Returns:
            Dictionary representation of token
        """
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "token_type": self.token_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StravaToken":
        """
        Deserialize token from dictionary.

        Args:
            data: Dictionary with token data

        Returns:
            StravaToken instance
        """
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=data["expires_at"],
            token_type=data.get("token_type", "Bearer"),
        )


@dataclass
class StravaSettings:
    """
    Strava integration settings loaded from environment.

    All settings can be customized via environment variables.
    """

    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8080/strava/callback"
    token_path: str = "local/strava/token.json"
    default_sync_days: int = 7
    default_download_format: str = "all"
    activity_dir: str = "data/strava/activities"

    @property
    def credentials(self) -> StravaCredentials:
        """
        Get credentials object from settings.

        Returns:
            StravaCredentials instance
        """
        return StravaCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
        )

    def validate(self) -> None:
        """
        Validate settings.

        Raises:
            ValueError: If required settings are missing
        """
        if not self.client_id:
            raise ValueError(
                "STRAVA_CLIENT_ID not set. "
                "Please set it in your .env file. "
                "Get credentials from: https://www.strava.com/settings/api"
            )
        if not self.client_secret:
            raise ValueError(
                "STRAVA_CLIENT_SECRET not set. "
                "Please set it in your .env file. "
                "Get credentials from: https://www.strava.com/settings/api"
            )

    @classmethod
    def from_env(cls) -> "StravaSettings":
        """
        Load settings from environment variables.

        Returns:
            StravaSettings instance

        Raises:
            ValueError: If required environment variables are missing
        """
        import os

        settings = cls(
            client_id=os.getenv("STRAVA_CLIENT_ID", ""),
            client_secret=os.getenv("STRAVA_CLIENT_SECRET", ""),
            redirect_uri=os.getenv(
                "STRAVA_REDIRECT_URI", "http://localhost:8080/strava/callback"
            ),
            token_path=os.getenv("STRAVA_TOKEN_PATH", "local/strava/token.json"),
            default_sync_days=int(os.getenv("STRAVA_DEFAULT_SYNC_DAYS", "7")),
            default_download_format=os.getenv("STRAVA_DEFAULT_DOWNLOAD_FORMAT", "all"),
            activity_dir=os.getenv("STRAVA_ACTIVITY_DIR", "data/strava/activities"),
        )

        settings.validate()
        return settings


@dataclass
class StravaRateLimitStatus:
    """
    Rate limit tracking for Strava API.

    Strava has two rate limits:
    - 100 requests per 15 minutes
    - 1000 requests per day
    """

    requests_15min: int = 0
    requests_daily: int = 0
    reset_15min: datetime = field(default_factory=datetime.now)
    reset_daily: datetime = field(default_factory=datetime.now)

    # Strava's limits
    LIMIT_15MIN = 100
    LIMIT_DAILY = 1000

    def is_limit_exceeded(self) -> bool:
        """
        Check if either rate limit is exceeded.

        Returns:
            True if rate limit exceeded, False otherwise
        """
        now = datetime.now()

        # Reset counters if windows have passed
        if now >= self.reset_15min:
            self.requests_15min = 0
            from datetime import timedelta

            self.reset_15min = now + timedelta(minutes=15)

        if now >= self.reset_daily:
            self.requests_daily = 0
            from datetime import timedelta

            self.reset_daily = now + timedelta(days=1)

        # Check limits
        return (
            self.requests_15min >= self.LIMIT_15MIN
            or self.requests_daily >= self.LIMIT_DAILY
        )

    def increment(self) -> None:
        """Increment both rate limit counters."""
        self.requests_15min += 1
        self.requests_daily += 1

    def seconds_until_reset(self) -> int:
        """
        Get seconds until next rate limit reset.

        Returns:
            Seconds until the soonest rate limit window resets
        """
        now = datetime.now()
        seconds_15min = int((self.reset_15min - now).total_seconds())
        seconds_daily = int((self.reset_daily - now).total_seconds())

        # Return the soonest reset time
        return min(seconds_15min, seconds_daily) if seconds_15min > 0 else seconds_daily

    def get_status_dict(self) -> dict:
        """
        Get rate limit status as dictionary.

        Returns:
            Dictionary with current usage and limits
        """
        return {
            "15min": {
                "used": self.requests_15min,
                "limit": self.LIMIT_15MIN,
                "remaining": self.LIMIT_15MIN - self.requests_15min,
                "reset_at": self.reset_15min.isoformat(),
            },
            "daily": {
                "used": self.requests_daily,
                "limit": self.LIMIT_DAILY,
                "remaining": self.LIMIT_DAILY - self.requests_daily,
                "reset_at": self.reset_daily.isoformat(),
            },
        }
