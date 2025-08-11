"""
Unit tests for mock heart rate data generation.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.testing.mocks.mock_heart_rate_data import (
    MockHeartRateSession,
    MockHeartRateDataGenerator,
    create_single_session,
    create_workout_session,
    create_sleep_session,
    create_daily_sessions,
    create_realistic_scenario,
)


class TestMockHeartRateSession:
    """Test MockHeartRateSession class."""

    def test_session_creation(self):
        """Test creating a basic heart rate session."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 30, 0)

        session = MockHeartRateSession(
            start_time=start_time,
            end_time=end_time,
            base_heart_rate=70,
            variability_factor=0.1,
        )

        assert session.start_time == start_time
        assert session.end_time == end_time
        assert session.base_heart_rate == 70
        assert session.variability_factor == 0.1
        assert session.duration_minutes == 30
        assert len(session.data_points) > 0

    def test_session_properties(self):
        """Test session property calculations."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 10, 0)

        session = MockHeartRateSession(
            start_time=start_time,
            end_time=end_time,
            base_heart_rate=80,
            variability_factor=0.05,
        )

        assert session.duration_minutes == 10
        assert session.data_points_count > 0
        assert session.average_heart_rate > 0
        assert session.min_heart_rate > 0
        assert session.max_heart_rate > 0

        # Heart rate should be within realistic bounds
        assert 40 <= session.min_heart_rate <= 200
        assert 40 <= session.max_heart_rate <= 200
        assert (
            session.min_heart_rate
            <= session.average_heart_rate
            <= session.max_heart_rate
        )

    def test_trend_directions(self):
        """Test different trend directions."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 30, 0)

        # Stable trend
        stable_session = MockHeartRateSession(
            start_time=start_time,
            end_time=end_time,
            trend_direction="stable",
            base_heart_rate=70,
        )

        # Increasing trend
        increasing_session = MockHeartRateSession(
            start_time=start_time,
            end_time=end_time,
            trend_direction="increasing",
            base_heart_rate=70,
        )

        # Decreasing trend
        decreasing_session = MockHeartRateSession(
            start_time=start_time,
            end_time=end_time,
            trend_direction="decreasing",
            base_heart_rate=70,
        )

        # Variable trend
        variable_session = MockHeartRateSession(
            start_time=start_time,
            end_time=end_time,
            trend_direction="variable",
            base_heart_rate=70,
        )

        # All sessions should have data points
        assert len(stable_session.data_points) > 0
        assert len(increasing_session.data_points) > 0
        assert len(decreasing_session.data_points) > 0
        assert len(variable_session.data_points) > 0

    def test_export_csv(self):
        """Test CSV export functionality."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 5, 0)

        session = MockHeartRateSession(
            start_time=start_time, end_time=end_time, base_heart_rate=75
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_file = f.name

        try:
            exported_path = session.export_csv(temp_file)

            # Check file exists and has content
            assert os.path.exists(exported_path)
            assert os.path.getsize(exported_path) > 0

            # Check CSV structure
            with open(exported_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) > 1  # Header + data
                assert "timestamp,heart_rate,confidence" in lines[0]

                # Check data lines
                for line in lines[1:]:
                    parts = line.strip().split(",")
                    assert len(parts) == 3
                    assert parts[1].isdigit()  # heart_rate should be numeric
                    assert float(parts[2]) >= 0  # confidence should be non-negative

        finally:
            os.unlink(temp_file)

    def test_export_json(self):
        """Test JSON export functionality."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 5, 0)

        session = MockHeartRateSession(
            start_time=start_time, end_time=end_time, base_heart_rate=75
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            exported_path = session.export_json(temp_file)

            # Check file exists and has content
            assert os.path.exists(exported_path)
            assert os.path.getsize(exported_path) > 0

            # Check JSON structure
            import json

            with open(exported_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                assert "session_info" in data
                assert "data_points" in data
                assert len(data["data_points"]) > 0

                # Check first data point structure
                first_point = data["data_points"][0]
                assert "timestamp" in first_point
                assert "heart_rate" in first_point
                assert "confidence" in first_point

        finally:
            os.unlink(temp_file)

    def test_export_text(self):
        """Test text export functionality."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 5, 0)

        session = MockHeartRateSession(
            start_time=start_time, end_time=end_time, base_heart_rate=75
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_file = f.name

        try:
            exported_path = session.export_text(temp_file)

            # Check file exists and has content
            assert os.path.exists(exported_path)
            assert os.path.getsize(exported_path) > 0

            # Check text structure
            with open(exported_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) > 1  # Header + data
                assert any("Heart Rate Session:" in line for line in lines)
                assert any("Duration:" in line for line in lines)

                # Check data lines
                data_lines = [line for line in lines if not line.startswith("#")]
                for line in data_lines:
                    if line.strip():
                        parts = line.strip().split(",")
                        assert len(parts) == 3

        finally:
            os.unlink(temp_file)

    def test_export_apple_health_format(self):
        """Test Apple Health CSV export functionality."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 5, 0)

        session = MockHeartRateSession(
            start_time=start_time,
            end_time=end_time,
            base_heart_rate=75,
            sample_rate_hz=1.0,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_file = f.name

        try:
            exported_path = session.export_apple_health_format(temp_file)

            # Check file exists and has content
            assert os.path.exists(exported_path)
            assert os.path.getsize(exported_path) > 0

            # Check Apple Health CSV structure
            with open(exported_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) > 1  # Header + data
                assert "SampleType,SampleRate,StartTime,Data" in lines[0]

                # Check data lines
                for line in lines[1:]:
                    parts = line.strip().split(",")
                    assert len(parts) == 4
                    assert parts[0] == "HEART_RATE"
                    assert parts[1] == "1.0"  # sample rate
                    assert "T" in parts[2] and "Z" in parts[2]  # ISO format
                    assert ";" in parts[3]  # semicolon-separated heart rate values

        finally:
            os.unlink(temp_file)


class TestMockHeartRateDataGenerator:
    """Test MockHeartRateDataGenerator class."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = MockHeartRateDataGenerator()
        assert generator.fake is not None
        assert hasattr(generator, "heart_rate_scenarios")
        assert "resting" in generator.heart_rate_scenarios
        assert "intense_exercise" in generator.heart_rate_scenarios

    def test_generate_session_basic(self):
        """Test basic session generation."""
        generator = MockHeartRateDataGenerator()

        session = generator.generate_session("resting")

        assert isinstance(session, MockHeartRateSession)
        assert session.data_points_count > 0
        assert session.duration_minutes > 0
        assert session.average_heart_rate > 0

    def test_generate_session_with_parameters(self):
        """Test session generation with specific parameters."""
        generator = MockHeartRateDataGenerator()

        start_time = datetime(2024, 1, 15, 10, 0, 0)
        duration_minutes = 45

        session = generator.generate_session(
            "light_exercise", start_time=start_time, duration_minutes=duration_minutes
        )

        assert session.start_time == start_time
        assert session.duration_minutes == duration_minutes
        assert session.base_heart_rate >= 80
        assert session.base_heart_rate <= 100

    def test_generate_workout_session(self):
        """Test workout session generation."""
        generator = MockHeartRateDataGenerator()

        session = generator.generate_workout_session()

        assert isinstance(session, MockHeartRateSession)
        assert session.duration_minutes > 0
        assert session.data_points_count > 0
        assert "workout" in session.notes.lower()

        # Workout should have significant heart rate variation
        hr_range = session.max_heart_rate - session.min_heart_rate
        assert hr_range > 20  # Should have variation

    def test_generate_sleep_session(self):
        """Test sleep session generation."""
        generator = MockHeartRateDataGenerator()

        session = generator.generate_sleep_session()

        assert isinstance(session, MockHeartRateSession)
        assert session.duration_minutes >= 240  # At least 4 hours
        assert session.base_heart_rate >= 50
        assert session.base_heart_rate <= 70
        assert "sleep" in session.notes.lower()

    def test_generate_daily_sessions(self):
        """Test daily sessions generation."""
        generator = MockHeartRateDataGenerator()

        date = datetime(2024, 1, 15, 6, 0, 0)  # 6 AM
        sessions = generator.generate_daily_sessions(date, num_sessions=3)

        assert len(sessions) > 0
        assert len(sessions) <= 3

        for session in sessions:
            assert isinstance(session, MockHeartRateSession)
            assert session.start_time.day == date.day
            assert session.data_points_count > 0

    def test_scenario_specific_generation(self):
        """Test generation for specific scenarios."""
        generator = MockHeartRateDataGenerator()

        # Test intense exercise with peak
        intense_session = generator.generate_session("intense_exercise")
        assert intense_session.data_points_count > 0

        # Test recovery
        recovery_session = generator.generate_session("recovery")
        assert recovery_session.data_points_count > 0

        # Test sleep
        sleep_session = generator.generate_session("sleep")
        assert sleep_session.data_points_count > 0
        assert sleep_session.duration_minutes >= 240


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_single_session(self):
        """Test create_single_session function."""
        session = create_single_session("resting")

        assert isinstance(session, MockHeartRateSession)
        assert session.data_points_count > 0
        assert session.duration_minutes > 0

    def test_create_workout_session(self):
        """Test create_workout_session function."""
        session = create_workout_session()

        assert isinstance(session, MockHeartRateSession)
        assert "workout" in session.notes.lower()

    def test_create_sleep_session(self):
        """Test create_sleep_session function."""
        session = create_sleep_session()

        assert isinstance(session, MockHeartRateSession)
        assert "sleep" in session.notes.lower()
        assert session.duration_minutes >= 240

    def test_create_daily_sessions(self):
        """Test create_daily_sessions function."""
        sessions = create_daily_sessions(num_sessions=2)

        assert len(sessions) > 0
        assert len(sessions) <= 2

        for session in sessions:
            assert isinstance(session, MockHeartRateSession)

    def test_create_realistic_scenario(self):
        """Test create_realistic_scenario function."""
        # Test daily scenario
        daily_sessions = create_realistic_scenario("daily", num_sessions=2)
        assert len(daily_sessions) > 0

        # Test workout scenario
        workout_sessions = create_realistic_scenario("workout")
        assert len(workout_sessions) == 1
        assert "workout" in workout_sessions[0].notes.lower()

        # Test sleep scenario
        sleep_sessions = create_realistic_scenario("sleep")
        assert len(sleep_sessions) == 1
        assert "sleep" in sleep_sessions[0].notes.lower()

        # Test mixed scenario
        mixed_sessions = create_realistic_scenario("mixed", num_sessions=2)
        assert len(mixed_sessions) > 1


class TestDataQuality:
    """Test data quality and realism."""

    def test_heart_rate_bounds(self):
        """Test that heart rates are within realistic bounds."""
        session = create_single_session("intense_exercise", duration_minutes=30)

        assert session.min_heart_rate >= 40
        assert session.max_heart_rate <= 200
        assert session.average_heart_rate >= session.min_heart_rate
        assert session.average_heart_rate <= session.max_heart_rate

    def test_data_point_consistency(self):
        """Test that data points are consistent."""
        session = create_single_session("resting", duration_minutes=10)

        # Check timestamp ordering
        timestamps = [point[0] for point in session.data_points]
        assert timestamps == sorted(timestamps)

        # Check heart rate values
        heart_rates = [point[1] for point in session.data_points]
        assert all(40 <= hr <= 200 for hr in heart_rates)

        # Check confidence values
        confidences = [point[2] for point in session.data_points]
        assert all(0 <= conf <= 1 for conf in confidences)

    def test_session_duration_accuracy(self):
        """Test that session duration matches data points."""
        session = create_single_session("light_exercise", duration_minutes=15)

        expected_duration = 15
        actual_duration = session.duration_minutes

        assert abs(expected_duration - actual_duration) <= 1  # Allow 1 minute tolerance

    def test_sample_rate_consistency(self):
        """Test that sample rate is consistent with data points."""
        session = MockHeartRateSession(
            start_time=datetime(2024, 1, 15, 10, 0, 0),
            end_time=datetime(2024, 1, 15, 10, 1, 0),  # 1 minute
            sample_rate_hz=2.0,  # 2 samples per second
        )

        # Should have approximately 120 data points (2 Hz * 60 seconds)
        expected_points = 120
        actual_points = session.data_points_count

        # Allow some tolerance for edge cases
        assert abs(expected_points - actual_points) <= 10


class TestAppleHealthImport:
    """Test Apple Health CSV import functionality."""

    def test_apple_health_import(self):
        """Test importing Apple Health CSV format."""
        from src.lib.heart_rate_manager import HeartRateDataImporter

        # Create a temporary Apple Health CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write('"SampleType","SampleRate","StartTime","Data"\n')
            f.write(
                '"HEART_RATE",1,"2025-08-11T15:24:12.000Z","72;74;73;75;76;80;82;85;87"\n'
            )
            f.write(
                '"HEART_RATE",1,"2025-08-11T15:25:12.000Z","88;90;92;95;98;100;102;105;108"\n'
            )
            temp_file = f.name

        try:
            # Import with Apple Health format hint
            session = HeartRateDataImporter.import_from_file(
                temp_file, format_hint="apple_health"
            )

            assert session.format == "apple_health"
            assert session.source_file == temp_file
            assert session.data_points_count > 0

            # Check that heart rate values are parsed correctly
            heart_rates = [point.heart_rate for point in session.data_points]
            assert 72 in heart_rates
            assert 108 in heart_rates

            # Check that timestamps are properly distributed
            timestamps = [point.timestamp for point in session.data_points]
            assert timestamps == sorted(timestamps)

        finally:
            os.unlink(temp_file)

    def test_apple_health_auto_detection(self):
        """Test automatic detection of Apple Health format."""
        from src.lib.heart_rate_manager import HeartRateDataImporter

        # Create a temporary Apple Health CSV file with .health extension
        with tempfile.NamedTemporaryFile(mode="w", suffix=".health", delete=False) as f:
            f.write('"SampleType","SampleRate","StartTime","Data"\n')
            f.write(
                '"HEART_RATE",1,"2025-08-11T15:24:12.000Z","72;74;73;75;76;80;82;85;87"\n'
            )
            temp_file = f.name

        try:
            # Import without format hint (should auto-detect)
            session = HeartRateDataImporter.import_from_file(temp_file)

            assert session.format == "apple_health"
            assert session.data_points_count > 0

        finally:
            os.unlink(temp_file)
