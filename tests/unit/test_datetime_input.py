"""
Unit tests for datetime_input utility module.
"""

from datetime import datetime, timedelta
from unittest.mock import patch
from src.lib.datetime_input import (
    get_date_input,
    get_time_input,
    combine_date_time,
    get_datetime_input,
)


class TestGetDateInput:
    """Test get_date_input() function."""

    @patch("builtins.input", return_value="")
    def test_empty_input_with_shortcuts_returns_today(self, mock_input):
        """Test that empty input returns today when shortcuts are allowed."""
        result = get_date_input(allow_shortcuts=True)
        expected = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        assert result.date() == expected.date()
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    @patch("builtins.input", return_value="0")
    def test_zero_input_returns_today(self, mock_input):
        """Test that '0' input returns today."""
        result = get_date_input(allow_shortcuts=True)
        expected = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        assert result.date() == expected.date()
        assert result.hour == 0

    @patch("builtins.input", return_value="1")
    def test_one_input_returns_tomorrow(self, mock_input):
        """Test that '1' input returns tomorrow."""
        result = get_date_input(allow_shortcuts=True)
        expected = (datetime.now() + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        assert result.date() == expected.date()
        assert result.hour == 0

    @patch("builtins.input", return_value="2025-10-28")
    def test_explicit_date_input(self, mock_input):
        """Test that explicit date in YYYY-MM-DD format is parsed correctly."""
        result = get_date_input(allow_shortcuts=True)

        assert result.year == 2025
        assert result.month == 10
        assert result.day == 28
        assert result.hour == 0
        assert result.minute == 0

    @patch("builtins.input", side_effect=["invalid", "2025-10-28"])
    def test_invalid_then_valid_date(self, mock_input):
        """Test that invalid date is rejected and user is re-prompted."""
        result = get_date_input(allow_shortcuts=True)

        assert result.year == 2025
        assert result.month == 10
        assert result.day == 28
        assert mock_input.call_count == 2

    @patch("builtins.input", side_effect=["", "2025-10-28"])
    def test_empty_input_without_shortcuts_prompts_again(self, mock_input):
        """Test that empty input without shortcuts prompts user again."""
        result = get_date_input(allow_shortcuts=False)

        assert result.year == 2025
        assert result.month == 10
        assert result.day == 28
        assert mock_input.call_count == 2


class TestGetTimeInput:
    """Test get_time_input() function."""

    @patch("builtins.input", return_value="")
    def test_empty_input_with_now_returns_none(self, mock_input):
        """Test that empty input returns None when allow_now is True."""
        result = get_time_input(allow_now=True)

        assert result is None

    @patch("builtins.input", return_value="18:30")
    def test_explicit_time_input(self, mock_input):
        """Test that explicit time in HH:MM format is parsed correctly."""
        result = get_time_input(allow_now=True)

        assert result == (18, 30)

    @patch("builtins.input", return_value="09:05")
    def test_time_with_leading_zeros(self, mock_input):
        """Test that time with leading zeros is parsed correctly."""
        result = get_time_input(allow_now=True)

        assert result == (9, 5)

    @patch("builtins.input", side_effect=["invalid", "12:45"])
    def test_invalid_then_valid_time(self, mock_input):
        """Test that invalid time is rejected and user is re-prompted."""
        result = get_time_input(allow_now=True)

        assert result == (12, 45)
        assert mock_input.call_count == 2

    @patch("builtins.input", side_effect=["25:00", "23:59"])
    def test_invalid_hour_then_valid_time(self, mock_input):
        """Test that invalid hour (25) is rejected."""
        result = get_time_input(allow_now=True)

        assert result == (23, 59)
        assert mock_input.call_count == 2

    @patch("builtins.input", side_effect=["", "14:30"])
    def test_empty_input_without_now_prompts_again(self, mock_input):
        """Test that empty input without allow_now prompts user again."""
        result = get_time_input(allow_now=False)

        assert result == (14, 30)
        assert mock_input.call_count == 2


class TestCombineDateTime:
    """Test combine_date_time() function."""

    def test_combine_date_and_time(self):
        """Test combining date and time into datetime."""
        date_obj = datetime(2025, 10, 28, 0, 0, 0)
        time_tuple = (18, 30)

        result = combine_date_time(date_obj, time_tuple)

        assert result.year == 2025
        assert result.month == 10
        assert result.day == 28
        assert result.hour == 18
        assert result.minute == 30
        assert result.second == 0
        assert result.microsecond == 0

    def test_combine_with_none_date_uses_today(self):
        """Test that None date uses today's date."""
        time_tuple = (14, 45)

        result = combine_date_time(None, time_tuple)
        today = datetime.now()

        assert result.date() == today.date()
        assert result.hour == 14
        assert result.minute == 45

    def test_combine_with_none_time_uses_now(self):
        """Test that None time uses current time."""
        date_obj = datetime(2025, 10, 28, 0, 0, 0)

        result = combine_date_time(date_obj, None)
        now = datetime.now()

        assert result.year == 2025
        assert result.month == 10
        assert result.day == 28
        # Time should be close to current time (within a few seconds)
        assert abs((result.hour * 60 + result.minute) - (now.hour * 60 + now.minute)) <= 1

    def test_combine_with_both_none(self):
        """Test that both None values use current datetime."""
        result = combine_date_time(None, None)
        now = datetime.now()

        assert result.date() == now.date()
        assert abs((result.hour * 60 + result.minute) - (now.hour * 60 + now.minute)) <= 1


class TestGetDatetimeInput:
    """Test get_datetime_input() convenience function."""

    @patch("builtins.input", side_effect=["2025-10-28", "19:00"])
    def test_get_datetime_with_explicit_inputs(self, mock_input):
        """Test that explicit date and time inputs are combined correctly."""
        result = get_datetime_input(
            date_prompt="Visit date",
            time_prompt="Visit time",
            allow_date_shortcuts=True,
            allow_now=True
        )

        assert result.year == 2025
        assert result.month == 10
        assert result.day == 28
        assert result.hour == 19
        assert result.minute == 0

    @patch("builtins.input", side_effect=["0", ""])
    def test_get_datetime_with_shortcuts(self, mock_input):
        """Test that date shortcut (0) and empty time work correctly."""
        result = get_datetime_input(
            allow_date_shortcuts=True,
            allow_now=True
        )

        today = datetime.now()
        assert result.date() == today.date()

    @patch("builtins.input", side_effect=["1", "08:00"])
    def test_get_datetime_with_tomorrow_shortcut(self, mock_input):
        """Test that tomorrow shortcut (1) works correctly."""
        result = get_datetime_input(
            allow_date_shortcuts=True,
            allow_now=True
        )

        tomorrow = datetime.now() + timedelta(days=1)
        assert result.date() == tomorrow.date()
        assert result.hour == 8
        assert result.minute == 0

    @patch("builtins.input", side_effect=["invalid", "2025-10-28", "invalid", "15:30"])
    def test_get_datetime_with_validation_errors(self, mock_input):
        """Test that validation errors in both date and time are handled."""
        result = get_datetime_input(
            allow_date_shortcuts=True,
            allow_now=True
        )

        assert result.year == 2025
        assert result.month == 10
        assert result.day == 28
        assert result.hour == 15
        assert result.minute == 30
        assert mock_input.call_count == 4


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @patch("builtins.input", side_effect=["2025-02-29", "2025-02-28"])
    def test_invalid_date_february_29_non_leap_year(self, mock_input):
        """Test that invalid date like Feb 29 in non-leap year is rejected and re-prompted."""
        # 2025 is not a leap year, so Feb 29 is invalid
        result = get_date_input(allow_shortcuts=True)

        # Should accept the second input (Feb 28)
        assert result.year == 2025
        assert result.month == 2
        assert result.day == 28
        assert mock_input.call_count == 2

    @patch("builtins.input", return_value="2024-02-29")
    def test_valid_leap_year_date(self, mock_input):
        """Test that Feb 29 in leap year is accepted."""
        result = get_date_input(allow_shortcuts=True)

        assert result.year == 2024
        assert result.month == 2
        assert result.day == 29

    @patch("builtins.input", return_value="00:00")
    def test_midnight_time(self, mock_input):
        """Test that midnight (00:00) is handled correctly."""
        result = get_time_input(allow_now=True)

        assert result == (0, 0)

    @patch("builtins.input", return_value="23:59")
    def test_end_of_day_time(self, mock_input):
        """Test that end of day (23:59) is handled correctly."""
        result = get_time_input(allow_now=True)

        assert result == (23, 59)
