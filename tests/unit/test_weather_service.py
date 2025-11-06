"""
Unit tests for weather service.
"""

import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock

import pytest
import requests

from src.lib.weather_service import WeatherService, get_weather_service


class TestWeatherServiceInit:
    """Test WeatherService initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        service = WeatherService(api_key="test_key")
        assert service.api_key == "test_key"
        assert service.is_configured()

    def test_init_without_api_key_uses_env(self):
        """Test initialization without explicit key uses environment variable."""
        with patch.dict(os.environ, {"WEATHERAPI_API_KEY": "env_key"}):
            service = WeatherService()
            assert service.api_key == "env_key"
            assert service.is_configured()

    def test_init_without_api_key_no_env(self):
        """Test initialization without key and no env variable."""
        with patch.dict(os.environ, {}, clear=True):
            service = WeatherService()
            assert service.api_key is None
            assert not service.is_configured()

    def test_is_configured_empty_string(self):
        """Test that empty string API key is not considered configured."""
        service = WeatherService(api_key="   ")
        assert not service.is_configured()


class TestWeatherServiceFetchTemperature:
    """Test temperature fetching functionality."""

    def test_fetch_temperature_success(self):
        """Test successful temperature fetch."""
        service = WeatherService(api_key="test_key")

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "forecast": {
                "forecastday": [
                    {
                        "hour": [
                            {"time": "2025-11-06 14:00", "temp_c": 18.5},
                            {"time": "2025-11-06 15:00", "temp_c": 19.2},
                        ]
                    }
                ]
            }
        }

        with patch("requests.get", return_value=mock_response):
            dt = datetime(2025, 11, 6, 15, 30)
            temp = service.fetch_temperature(lat=33.2794, lon=131.5006, dt=dt)
            assert temp == 19.2

    def test_fetch_temperature_no_api_key(self):
        """Test that fetch raises ValueError when API key not configured."""
        # Ensure no API key in environment
        with patch.dict(os.environ, {}, clear=True):
            service = WeatherService(api_key=None)

            dt = datetime(2025, 11, 6, 15, 30)
            with pytest.raises(ValueError, match="API key not configured"):
                service.fetch_temperature(lat=33.2794, lon=131.5006, dt=dt)

    def test_fetch_temperature_invalid_coordinates(self):
        """Test that fetch raises ValueError for invalid coordinates."""
        service = WeatherService(api_key="test_key")
        dt = datetime(2025, 11, 6, 15, 30)

        # Invalid latitude
        with pytest.raises(ValueError, match="Invalid coordinates"):
            service.fetch_temperature(lat=91.0, lon=131.5006, dt=dt)

        # Invalid longitude
        with pytest.raises(ValueError, match="Invalid coordinates"):
            service.fetch_temperature(lat=33.2794, lon=181.0, dt=dt)

    def test_fetch_temperature_network_error(self):
        """Test handling of network errors."""
        service = WeatherService(api_key="test_key")

        with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Network error")):
            dt = datetime(2025, 11, 6, 15, 30)
            temp = service.fetch_temperature(lat=33.2794, lon=131.5006, dt=dt, max_retries=1)
            assert temp is None

    def test_fetch_temperature_retry_logic(self):
        """Test that retry logic works correctly."""
        service = WeatherService(api_key="test_key")

        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "forecast": {
                "forecastday": [
                    {
                        "hour": [
                            {"time": "2025-11-06 15:00", "temp_c": 20.0},
                        ]
                    }
                ]
            }
        }

        with patch("requests.get", side_effect=[
            requests.exceptions.Timeout("Timeout"),
            mock_response
        ]):
            dt = datetime(2025, 11, 6, 15, 30)
            temp = service.fetch_temperature(lat=33.2794, lon=131.5006, dt=dt, max_retries=1)
            assert temp == 20.0

    def test_fetch_temperature_api_error(self):
        """Test handling of API errors (4xx, 5xx)."""
        service = WeatherService(api_key="test_key")

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")

        with patch("requests.get", return_value=mock_response):
            dt = datetime(2025, 11, 6, 15, 30)
            temp = service.fetch_temperature(lat=33.2794, lon=131.5006, dt=dt, max_retries=1)
            assert temp is None

    def test_fetch_temperature_invalid_response_structure(self):
        """Test handling of unexpected API response structure."""
        service = WeatherService(api_key="test_key")

        # Mock response with missing fields
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "structure"}

        with patch("requests.get", return_value=mock_response):
            dt = datetime(2025, 11, 6, 15, 30)
            temp = service.fetch_temperature(lat=33.2794, lon=131.5006, dt=dt, max_retries=0)
            assert temp is None

    def test_fetch_temperature_no_data_for_hour(self):
        """Test handling when no data available for specific hour."""
        service = WeatherService(api_key="test_key")

        # Mock response with different hours
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "forecast": {
                "forecastday": [
                    {
                        "hour": [
                            {"time": "2025-11-06 14:00", "temp_c": 18.5},
                            # Hour 15 is missing
                            {"time": "2025-11-06 16:00", "temp_c": 19.5},
                        ]
                    }
                ]
            }
        }

        with patch("requests.get", return_value=mock_response):
            dt = datetime(2025, 11, 6, 15, 30)
            temp = service.fetch_temperature(lat=33.2794, lon=131.5006, dt=dt)
            assert temp is None

    def test_fetch_temperature_with_timezone(self):
        """Test that timezone-aware datetime is converted to JST."""
        service = WeatherService(api_key="test_key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "forecast": {
                "forecastday": [
                    {
                        "hour": [
                            {"time": "2025-11-06 09:00", "temp_c": 15.0},
                        ]
                    }
                ]
            }
        }

        with patch("requests.get", return_value=mock_response) as mock_get:
            # UTC midnight = JST 9 AM
            utc_time = datetime(2025, 11, 6, 0, 0, tzinfo=timezone.utc)
            temp = service.fetch_temperature(lat=33.2794, lon=131.5006, dt=utc_time)

            # Verify the API was called with correct date
            call_args = mock_get.call_args
            assert call_args[1]["params"]["dt"] == "2025-11-06"
            assert temp == 15.0

    def test_fetch_temperature_naive_datetime_assumed_jst(self):
        """Test that naive datetime is assumed to be JST."""
        service = WeatherService(api_key="test_key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "forecast": {
                "forecastday": [
                    {
                        "hour": [
                            {"time": "2025-11-06 15:00", "temp_c": 20.0},
                        ]
                    }
                ]
            }
        }

        with patch("requests.get", return_value=mock_response) as mock_get:
            # Naive datetime (no timezone)
            dt = datetime(2025, 11, 6, 15, 30)
            temp = service.fetch_temperature(lat=33.2794, lon=131.5006, dt=dt)

            # Should be treated as JST (no conversion)
            call_args = mock_get.call_args
            assert call_args[1]["params"]["dt"] == "2025-11-06"
            assert temp == 20.0


class TestGetWeatherService:
    """Test the factory function."""

    def test_get_weather_service(self):
        """Test that factory function returns configured service."""
        with patch.dict(os.environ, {"WEATHERAPI_API_KEY": "factory_key"}):
            service = get_weather_service()
            assert isinstance(service, WeatherService)
            assert service.api_key == "factory_key"

    def test_get_weather_service_no_env(self):
        """Test factory function without environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            service = get_weather_service()
            assert isinstance(service, WeatherService)
            assert not service.is_configured()
