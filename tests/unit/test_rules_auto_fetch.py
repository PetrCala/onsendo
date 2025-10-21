"""
Unit tests for rule revision auto-fetch functionality.

These tests mock dependencies and don't require database access.
For integration tests with actual database, see tests/integration/test_rules_auto_fetch_integration.py
"""

from unittest.mock import patch

from src.cli.commands.rules.revision_create import collect_summary_metrics
from src.types.rules import WeeklyReviewMetrics


class TestCollectSummaryMetricsWithAutoFetch:
    """Test the collect_summary_metrics function with auto-fetched data."""

    @patch("builtins.input")
    def test_collect_metrics_without_auto_fetch(self, mock_input):
        """Test collect_summary_metrics without auto-fetched data (manual entry)."""
        # Simulate user entering values
        mock_input.side_effect = ["3", "2.5", "2", "15.5", "2", "y", "1"]

        metrics = collect_summary_metrics(auto_fetched_metrics=None)

        assert metrics.onsen_visits_count == 3
        assert metrics.total_soaking_hours == 2.5
        assert metrics.sauna_sessions_count == 2
        assert metrics.running_distance_km == 15.5
        assert metrics.gym_sessions_count == 2
        assert metrics.hike_completed is True
        assert metrics.rest_days_count == 1

    @patch("builtins.input")
    def test_collect_metrics_with_auto_fetch_accept_all(self, mock_input):
        """Test collect_summary_metrics accepting all auto-fetched values."""
        # Create auto-fetched metrics
        auto_metrics = WeeklyReviewMetrics(
            onsen_visits_count=3,
            total_soaking_hours=2.5,
            sauna_sessions_count=2,
            running_distance_km=15.0,
            gym_sessions_count=1,
            hike_completed=True,
            rest_days_count=None,
        )

        # Simulate user pressing Enter for all values (accept defaults)
        mock_input.side_effect = ["", "", "", "", "", "", ""]

        metrics = collect_summary_metrics(auto_fetched_metrics=auto_metrics)

        # Should match auto-fetched values
        assert metrics.onsen_visits_count == 3
        assert metrics.total_soaking_hours == 2.5
        assert metrics.sauna_sessions_count == 2
        assert metrics.running_distance_km == 15.0
        assert metrics.gym_sessions_count == 1
        assert metrics.hike_completed is True
        assert metrics.rest_days_count is None

    @patch("builtins.input")
    def test_collect_metrics_with_auto_fetch_override_some(self, mock_input):
        """Test collect_summary_metrics overriding some auto-fetched values."""
        # Create auto-fetched metrics
        auto_metrics = WeeklyReviewMetrics(
            onsen_visits_count=3,
            total_soaking_hours=2.5,
            sauna_sessions_count=2,
            running_distance_km=15.0,
            gym_sessions_count=1,
            hike_completed=False,
            rest_days_count=None,
        )

        # Simulate user accepting some, overriding others
        mock_input.side_effect = [
            "",  # Accept onsen visits: 3
            "",  # Accept soaking hours: 2.5
            "3",  # Override sauna sessions: 3
            "20.5",  # Override running distance: 20.5
            "",  # Accept gym sessions: 1
            "yes",  # Override hike completed: True
            "2",  # Add rest days: 2
        ]

        metrics = collect_summary_metrics(auto_fetched_metrics=auto_metrics)

        assert metrics.onsen_visits_count == 3  # Accepted
        assert metrics.total_soaking_hours == 2.5  # Accepted
        assert metrics.sauna_sessions_count == 3  # Overridden
        assert metrics.running_distance_km == 20.5  # Overridden
        assert metrics.gym_sessions_count == 1  # Accepted
        assert metrics.hike_completed is True  # Overridden
        assert metrics.rest_days_count == 2  # Manually entered

    @patch("builtins.input")
    def test_collect_metrics_with_invalid_override(self, mock_input):
        """Test collect_summary_metrics handles invalid user input gracefully."""
        # Create auto-fetched metrics
        auto_metrics = WeeklyReviewMetrics(
            onsen_visits_count=3,
            sauna_sessions_count=2,
        )

        # Simulate user entering invalid data (should fall back to auto value)
        mock_input.side_effect = [
            "invalid",  # Invalid int -> should use auto value (3)
            "",  # Accept sauna sessions
            "",  # Skip other fields
            "",
            "",
            "",
            "",
        ]

        metrics = collect_summary_metrics(auto_fetched_metrics=auto_metrics)

        # Should fall back to auto value when invalid input provided
        assert metrics.onsen_visits_count == 3
        assert metrics.sauna_sessions_count == 2

    @patch("builtins.input")
    def test_collect_metrics_with_empty_values(self, mock_input):
        """Test collect_summary_metrics handles empty/None values."""
        # Simulate all empty inputs
        mock_input.side_effect = ["", "", "", "", "", "", ""]

        metrics = collect_summary_metrics(auto_fetched_metrics=None)

        # All should be None or default values
        assert metrics.onsen_visits_count is None
        assert metrics.total_soaking_hours is None
        assert metrics.sauna_sessions_count is None
        assert metrics.running_distance_km is None
        assert metrics.gym_sessions_count is None
        assert metrics.hike_completed is None
        assert metrics.rest_days_count is None

    @patch("builtins.input")
    def test_collect_metrics_with_zero_values(self, mock_input):
        """Test collect_summary_metrics with zero values from auto-fetch."""
        # Create auto-fetched metrics with zeros
        auto_metrics = WeeklyReviewMetrics(
            onsen_visits_count=0,
            sauna_sessions_count=0,
            hike_completed=False,
        )

        # Accept all values
        mock_input.side_effect = ["", "", "", "", "", "", ""]

        metrics = collect_summary_metrics(auto_fetched_metrics=auto_metrics)

        # Should preserve zero values
        assert metrics.onsen_visits_count == 0
        assert metrics.sauna_sessions_count == 0
        assert metrics.hike_completed is False

    @patch("builtins.input")
    def test_collect_metrics_partial_auto_fetch(self, mock_input):
        """Test collect_summary_metrics with partial auto-fetched data."""
        # Create auto-fetched metrics with only some values
        auto_metrics = WeeklyReviewMetrics(
            onsen_visits_count=5,
            running_distance_km=20.0,
            # Other fields are None
        )

        # User accepts auto values and manually enters others
        mock_input.side_effect = [
            "",  # Accept onsen visits: 5
            "3.5",  # Manually enter soaking hours
            "3",  # Manually enter sauna sessions
            "",  # Accept running distance: 20.0
            "2",  # Manually enter gym sessions
            "yes",  # Manually enter hike completed
            "1",  # Manually enter rest days
        ]

        metrics = collect_summary_metrics(auto_fetched_metrics=auto_metrics)

        assert metrics.onsen_visits_count == 5  # Auto
        assert metrics.total_soaking_hours == 3.5  # Manual
        assert metrics.sauna_sessions_count == 3  # Manual
        assert metrics.running_distance_km == 20.0  # Auto
        assert metrics.gym_sessions_count == 2  # Manual
        assert metrics.hike_completed is True  # Manual
        assert metrics.rest_days_count == 1  # Manual

    @patch("builtins.input")
    def test_collect_metrics_boolean_variations(self, mock_input):
        """Test different boolean input variations for hike_completed."""
        # Test with True auto value
        auto_metrics = WeeklyReviewMetrics(hike_completed=True)

        mock_input.side_effect = ["", "", "", "", "", "", ""]
        metrics = collect_summary_metrics(auto_fetched_metrics=auto_metrics)
        assert metrics.hike_completed is True

        # Test overriding True to False
        mock_input.side_effect = ["", "", "", "", "", "n", ""]
        metrics = collect_summary_metrics(auto_fetched_metrics=auto_metrics)
        assert metrics.hike_completed is False

        # Test with False auto value
        auto_metrics = WeeklyReviewMetrics(hike_completed=False)
        mock_input.side_effect = ["", "", "", "", "", "", ""]
        metrics = collect_summary_metrics(auto_fetched_metrics=auto_metrics)
        assert metrics.hike_completed is False

        # Test overriding False to True
        mock_input.side_effect = ["", "", "", "", "", "yes", ""]
        metrics = collect_summary_metrics(auto_fetched_metrics=auto_metrics)
        assert metrics.hike_completed is True
