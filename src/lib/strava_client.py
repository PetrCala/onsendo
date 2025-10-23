"""
Strava API client for OAuth2 authentication and API requests.

This module provides the StravaClient class for interacting with the Strava API v3.
Handles OAuth2 authentication, token management, rate limiting, and API requests.
"""

import json
import os
import time
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Optional
from urllib.parse import parse_qs, urlparse

import requests
from loguru import logger

from src.types.strava import (
    StravaAuthenticationError,
    StravaCredentials,
    StravaNetworkError,
    StravaRateLimitError,
    StravaRateLimitStatus,
    StravaToken,
)


class StravaOAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth2 callback."""

    auth_code: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self) -> None:
        """Handle GET request from Strava OAuth callback."""
        # Parse the authorization code from callback URL
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        if "code" in query_params:
            # Success - got authorization code
            StravaOAuthCallbackHandler.auth_code = query_params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <head><title>Onsendo - Strava Authorization</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>&#10004; Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                """
            )
        elif "error" in query_params:
            # Error - user denied or error occurred
            StravaOAuthCallbackHandler.error = query_params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <head><title>Onsendo - Strava Authorization Failed</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1>&#10060; Authorization Failed</h1>
                    <p>Please try again or check your Strava application settings.</p>
                </body>
                </html>
                """
            )

    def log_message(self, format: str, *args) -> None:
        """Suppress default logging."""
        pass


class StravaClient:
    """
    Client for Strava API v3.

    Handles OAuth2 authentication, token management, rate limiting,
    and API requests to the Strava API.

    Attributes:
        BASE_URL: Strava API v3 base URL
        AUTH_URL: OAuth2 authorization URL
        TOKEN_URL: OAuth2 token exchange/refresh URL
    """

    BASE_URL = "https://www.strava.com/api/v3"
    AUTH_URL = "https://www.strava.com/oauth/authorize"
    TOKEN_URL = "https://www.strava.com/oauth/token"

    # Required OAuth2 scopes
    REQUIRED_SCOPES = "read,activity:read_all,profile:read_all"

    def __init__(self, credentials: StravaCredentials, token_path: str):
        """
        Initialize Strava client with credentials and token storage.

        Args:
            credentials: Strava OAuth2 credentials
            token_path: Path to store/load access token
        """
        credentials.validate()

        self.credentials = credentials
        self.token_path = Path(token_path)
        self.token: Optional[StravaToken] = None
        self.rate_limit = StravaRateLimitStatus()

        # Try to load existing token
        self._load_token()

    def authenticate(self) -> bool:
        """
        Perform OAuth2 authorization flow.

        Opens browser for user authorization, starts local server
        to receive callback, exchanges code for token.

        Returns:
            True if authentication successful

        Raises:
            StravaAuthenticationError: If authentication fails
        """
        logger.info("Starting Strava OAuth2 authentication flow")

        # Reset class variables
        StravaOAuthCallbackHandler.auth_code = None
        StravaOAuthCallbackHandler.error = None

        # Build authorization URL
        auth_url = (
            f"{self.AUTH_URL}?"
            f"client_id={self.credentials.client_id}&"
            f"redirect_uri={self.credentials.redirect_uri}&"
            f"response_type=code&"
            f"scope={self.REQUIRED_SCOPES}"
        )

        # Start local server to receive callback
        port = int(urlparse(self.credentials.redirect_uri).port or 8080)
        server = HTTPServer(("localhost", port), StravaOAuthCallbackHandler)

        # Run server in background thread
        server_thread = Thread(target=server.handle_request, daemon=True)
        server_thread.start()

        # Open browser for user authorization
        print("\n" + "=" * 60)
        print("Opening browser for Strava authorization...")
        print("=" * 60)
        print(f"\nIf browser doesn't open, visit: {auth_url}\n")

        webbrowser.open(auth_url)

        # Wait for callback (timeout after 5 minutes)
        timeout = 300
        start_time = time.time()

        while server_thread.is_alive():
            if time.time() - start_time > timeout:
                server.shutdown()
                raise StravaAuthenticationError(
                    "Authentication timeout - no response after 5 minutes"
                )

            if (
                StravaOAuthCallbackHandler.auth_code
                or StravaOAuthCallbackHandler.error
            ):
                break

            time.sleep(0.5)

        # Check for errors
        if StravaOAuthCallbackHandler.error:
            raise StravaAuthenticationError(
                f"Authorization failed: {StravaOAuthCallbackHandler.error}"
            )

        if not StravaOAuthCallbackHandler.auth_code:
            raise StravaAuthenticationError("No authorization code received")

        # Exchange authorization code for access token
        logger.info("Exchanging authorization code for access token")

        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.credentials.client_id,
                    "client_secret": self.credentials.client_secret,
                    "code": StravaOAuthCallbackHandler.auth_code,
                    "grant_type": "authorization_code",
                },
                timeout=30,
            )

            response.raise_for_status()
            token_data = response.json()

            # Create and save token
            self.token = StravaToken(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=token_data["expires_at"],
                token_type=token_data.get("token_type", "Bearer"),
            )

            self._save_token(self.token)
            logger.info("Authentication successful - token saved")

            return True

        except requests.exceptions.RequestException as e:
            raise StravaAuthenticationError(f"Token exchange failed: {e}")

    def _load_token(self) -> bool:
        """
        Load token from disk if exists and valid.

        Returns:
            True if token loaded successfully, False otherwise
        """
        if not self.token_path.exists():
            logger.debug(f"No token file found at {self.token_path}")
            return False

        try:
            with open(self.token_path, "r", encoding="utf-8") as f:
                token_data = json.load(f)

            self.token = StravaToken.from_dict(token_data)
            logger.info(f"Loaded token from {self.token_path}")

            # Check if token needs refresh
            if self.token.is_expired:
                logger.info("Token is expired, attempting refresh")
                self._refresh_token()

            return True

        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            logger.warning(f"Failed to load token: {e}")
            return False

    def _save_token(self, token: StravaToken) -> None:
        """
        Save token to disk with secure permissions.

        Args:
            token: Token to save
        """
        # Ensure directory exists
        self.token_path.parent.mkdir(parents=True, exist_ok=True)

        # Write token data
        with open(self.token_path, "w", encoding="utf-8") as f:
            json.dump(token.to_dict(), f, indent=2)

        # Set restrictive permissions (owner read/write only)
        os.chmod(self.token_path, 0o600)

        logger.info(f"Token saved to {self.token_path}")

    def _refresh_token(self) -> None:
        """
        Refresh access token using refresh token.

        Raises:
            StravaAuthenticationError: If token refresh fails
        """
        if not self.token:
            raise StravaAuthenticationError("No token to refresh")

        logger.info("Refreshing access token")

        try:
            response = requests.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.credentials.client_id,
                    "client_secret": self.credentials.client_secret,
                    "refresh_token": self.token.refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=30,
            )

            response.raise_for_status()
            token_data = response.json()

            # Update token
            self.token = StravaToken(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=token_data["expires_at"],
                token_type=token_data.get("token_type", "Bearer"),
            )

            self._save_token(self.token)
            logger.info("Token refreshed successfully")

        except requests.exceptions.RequestException as e:
            raise StravaAuthenticationError(f"Token refresh failed: {e}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """
        Make authenticated API request with rate limiting.

        Handles:
        - Token refresh if expired
        - Rate limit checking
        - Error responses
        - Retries with exponential backoff

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/athlete/activities")
            params: Optional query parameters
            json_data: Optional JSON body data

        Returns:
            JSON response as dictionary

        Raises:
            StravaAuthenticationError: If not authenticated or auth fails
            StravaRateLimitError: If rate limit exceeded
            StravaNetworkError: If network error occurs
        """
        if not self.token:
            raise StravaAuthenticationError(
                "Not authenticated. Run: poetry run onsendo strava auth"
            )

        # Refresh token if needed
        if self.token.is_expired:
            self._refresh_token()

        # Check rate limits
        if self.rate_limit.is_limit_exceeded():
            wait_seconds = self.rate_limit.seconds_until_reset()
            raise StravaRateLimitError(
                f"Rate limit exceeded. Reset in {wait_seconds} seconds. "
                f"Status: {self.rate_limit.get_status_dict()}"
            )

        # Build URL
        url = f"{self.BASE_URL}{endpoint}"

        # Add authorization header
        headers = {"Authorization": f"Bearer {self.token.access_token}"}

        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    timeout=30,
                )

                # Increment rate limit counter
                self.rate_limit.increment()

                # Handle rate limit response
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 900))
                    raise StravaRateLimitError(
                        f"Rate limit exceeded. Retry after {retry_after} seconds."
                    )

                # Handle auth errors
                if response.status_code == 401:
                    # Try to refresh token
                    if attempt < max_retries - 1:
                        logger.warning("Received 401, attempting token refresh")
                        self._refresh_token()
                        continue
                    else:
                        raise StravaAuthenticationError(
                            "Authentication failed. Please re-authenticate: "
                            "poetry run onsendo strava auth"
                        )

                # Raise for other HTTP errors
                response.raise_for_status()

                # Return JSON response
                return response.json()

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Request timeout, retrying in {wait_time}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    raise StravaNetworkError("Request failed after multiple retries")

            except requests.exceptions.ConnectionError as e:
                raise StravaNetworkError(f"Network connection failed: {e}")

            except requests.exceptions.HTTPError as e:
                # For non-retry errors, raise immediately
                if response.status_code not in [401, 429, 500, 502, 503, 504]:
                    raise StravaNetworkError(f"HTTP error: {e}")

                # For server errors, retry
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f"Server error {response.status_code}, retrying in {wait_time}s"
                    )
                    time.sleep(wait_time)
                else:
                    raise StravaNetworkError(f"HTTP error after retries: {e}")

        # Should not reach here, but just in case
        raise StravaNetworkError("Request failed")

    def is_authenticated(self) -> bool:
        """
        Check if client is authenticated.

        Returns:
            True if authenticated with valid token
        """
        if not self.token:
            return False

        if self.token.is_expired:
            try:
                self._refresh_token()
                return True
            except StravaAuthenticationError:
                return False

        return True

    def get_token_info(self) -> dict:
        """
        Get information about current token.

        Returns:
            Dictionary with token status information
        """
        if not self.token:
            return {"authenticated": False}

        return {
            "authenticated": True,
            "expires_at": datetime.fromtimestamp(self.token.expires_at).isoformat(),
            "expires_in_seconds": self.token.expires_in_seconds,
            "is_expired": self.token.is_expired,
        }

    def get_rate_limit_status(self) -> dict:
        """
        Get current rate limit usage.

        Returns:
            Dictionary with 15min and daily usage stats
        """
        return self.rate_limit.get_status_dict()
