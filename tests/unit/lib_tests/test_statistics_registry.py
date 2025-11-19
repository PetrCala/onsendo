"""Unit tests for statistics registry."""

import pytest

from src.lib.statistics_registry import StatisticsRegistry


class TestStatisticsRegistry:
    """Tests for StatisticsRegistry class."""

    def test_get_all_statistics(self):
        """Test that get_all_statistics returns all statistics."""
        registry = StatisticsRegistry()
        statistics = registry.get_all_statistics()

        assert len(statistics) > 0
        assert all("field_name" in stat for stat in statistics)
        assert all("display_name" in stat for stat in statistics)
        assert all("type" in stat for stat in statistics)
        assert all("description" in stat for stat in statistics)

    def test_get_statistic_by_field_name(self):
        """Test getting statistic by field name."""
        registry = StatisticsRegistry()
        stat = registry.get_statistic("personal_rating")

        assert stat is not None
        assert stat["field_name"] == "personal_rating"
        assert stat["display_name"] == "Personal Rating"
        assert stat["type"] == "rating"

    def test_get_statistic_nonexistent(self):
        """Test getting nonexistent statistic returns None."""
        registry = StatisticsRegistry()
        stat = registry.get_statistic("nonexistent_field")

        assert stat is None

    def test_get_statistic_display_name(self):
        """Test display name conversion."""
        registry = StatisticsRegistry()

        # Known field
        assert registry.get_statistic_display_name("personal_rating") == "Personal Rating"

        # Unknown field (fallback formatting)
        assert registry.get_statistic_display_name("unknown_field") == "Unknown Field"

    def test_format_statistic_value_rating(self):
        """Test formatting rating values."""
        registry = StatisticsRegistry()

        assert registry.format_statistic_value("personal_rating", 8.5) == "8.5/10"
        assert registry.format_statistic_value("accessibility_rating", 7) == "7.0/10"

    def test_format_statistic_value_duration(self):
        """Test formatting duration values."""
        registry = StatisticsRegistry()

        assert registry.format_statistic_value("stay_length_minutes", 45) == "45 min"
        assert registry.format_statistic_value("travel_time_minutes", 30) == "30 min"

    def test_format_statistic_value_fee(self):
        """Test formatting fee values."""
        registry = StatisticsRegistry()

        assert registry.format_statistic_value("entry_fee_yen", 500) == "¥500"
        assert registry.format_statistic_value("entry_fee_yen", 1000) == "¥1000"

    def test_format_statistic_value_temperature(self):
        """Test formatting temperature values."""
        registry = StatisticsRegistry()

        assert registry.format_statistic_value("temperature_outside_celsius", 25.5) == "25.5°C"
        assert registry.format_statistic_value("main_bath_temperature", 40.0) == "40.0°C"

    def test_format_statistic_value_numeric(self):
        """Test formatting generic numeric values."""
        registry = StatisticsRegistry()

        assert registry.format_statistic_value("energy_level_change", 2) == "2.0"
        assert registry.format_statistic_value("energy_level_change", -3) == "-3.0"

    def test_get_field_names(self):
        """Test getting all field names."""
        registry = StatisticsRegistry()
        field_names = registry.get_field_names()

        assert len(field_names) > 0
        assert "personal_rating" in field_names
        assert "stay_length_minutes" in field_names
        assert "entry_fee_yen" in field_names
        assert all(isinstance(name, str) for name in field_names)

