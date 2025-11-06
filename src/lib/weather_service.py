"""
Weather service for fetching historical temperature data.

This module provides integration with WeatherAPI.com to retrieve historical
temperature data for onsen visit recording.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests
from loguru import logger


class WeatherService:
    """Service for fetching weather data from WeatherAPI.com."""

    API_BASE_URL = "http://api.weatherapi.com/v1"
    TIMEOUT_SECONDS = 10
    JST_OFFSET = timedelta(hours=9)  # Japan Standard Time is UTC+9

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the weather service.

        Args:
            api_key: WeatherAPI.com API key. If not provided, attempts to load
                    from WEATHERAPI_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("WEATHERAPI_API_KEY")

    def is_configured(self) -> bool:
        """
        Check if the weather service is properly configured.

        Returns:
            True if API key is available, False otherwise.
        """
        return self.api_key is not None and len(self.api_key.strip()) > 0

    def fetch_temperature(
        self, lat: float, lon: float, dt: datetime, max_retries: int = 1
    ) -> Optional[float]:
        """
        Fetch historical temperature for a specific location and time.

        Args:
            lat: Latitude of the location.
            lon: Longitude of the location.
            dt: Datetime of the observation (assumed to be in JST).
            max_retries: Number of retries on failure (default: 1).

        Returns:
            Temperature in Celsius, or None if fetch failed.

        Raises:
            ValueError: If coordinates are invalid or API key not configured.
        """
        if not self.is_configured():
            raise ValueError(
                "WeatherAPI.com API key not configured. "
                "Set WEATHERAPI_API_KEY environment variable."
            )

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError(f"Invalid coordinates: lat={lat}, lon={lon}")

        # Convert datetime to JST if it has timezone info
        if dt.tzinfo is not None:
            jst_tz = timezone(self.JST_OFFSET)
            dt_jst = dt.astimezone(jst_tz)
        else:
            # Assume the datetime is already in JST
            dt_jst = dt

        logger.info(
            f"Fetching temperature for location ({lat}, {lon}) "
            f"at {dt_jst.strftime('%Y-%m-%d %H:%M')} JST"
        )

        attempt = 0
        last_error = None

        while attempt <= max_retries:
            try:
                temperature = self._make_api_request(lat, lon, dt_jst)
                if temperature is not None:
                    logger.info(f"Successfully fetched temperature: {temperature}°C")
                    return temperature

                logger.warning("API returned None for temperature")
                last_error = "No temperature data available"
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                logger.warning(
                    f"API request failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                )
            except (KeyError, ValueError, TypeError) as e:
                last_error = str(e)
                logger.error(f"Failed to parse API response: {e}")
                # Don't retry on parse errors
                break

            attempt += 1

        logger.error(
            f"Failed to fetch temperature after {max_retries + 1} attempts. "
            f"Last error: {last_error}"
        )
        return None

    def _make_api_request(self, lat: float, lon: float, dt_jst: datetime) -> Optional[float]:
        """
        Make the actual API request to WeatherAPI.com.

        Args:
            lat: Latitude of the location.
            lon: Longitude of the location.
            dt_jst: Datetime in JST timezone.

        Returns:
            Temperature in Celsius, or None if not available.

        Raises:
            requests.exceptions.RequestException: On network/API errors.
            KeyError, ValueError, TypeError: On response parsing errors.
        """
        endpoint = f"{self.API_BASE_URL}/history.json"

        params = {
            "key": self.api_key,
            "q": f"{lat},{lon}",
            "dt": dt_jst.strftime("%Y-%m-%d"),
        }

        logger.debug(f"Making request to {endpoint} with params: {params}")

        response = requests.get(endpoint, params=params, timeout=self.TIMEOUT_SECONDS)
        response.raise_for_status()

        data = response.json()

        # Extract temperature for the specific hour
        hour = dt_jst.hour
        try:
            forecast_day = data["forecast"]["forecastday"][0]
            hourly_data = forecast_day["hour"]

            # Find the matching hour
            for hour_entry in hourly_data:
                hour_time = datetime.strptime(
                    hour_entry["time"], "%Y-%m-%d %H:%M"
                )
                if hour_time.hour == hour:
                    temp_c = hour_entry["temp_c"]
                    logger.debug(f"Found temperature for hour {hour}: {temp_c}°C")
                    return float(temp_c)

            logger.warning(f"No temperature data found for hour {hour}")
            return None

        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected API response structure: {e}")
            raise ValueError(f"Failed to parse temperature from API response: {e}") from e


def get_weather_service() -> WeatherService:
    """
    Get a configured WeatherService instance.

    Returns:
        WeatherService instance with API key from environment.
    """
    return WeatherService()
