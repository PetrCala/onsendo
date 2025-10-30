"""
Unit tests for weight tracking management system.
"""

import pytest
import tempfile
import os
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta

from src.lib.weight_manager import (
    WeightMeasurement,
    WeightSummary,
    WeightDataValidator,
    WeightDataImporter,
)


class TestWeightMeasurement:
    """Test WeightMeasurement dataclass."""

    def test_weight_measurement_creation(self):
        """Test creating a weight measurement."""
        measurement = WeightMeasurement(
            measurement_time=datetime(2025, 10, 15, 7, 30, 0),
            weight_kg=72.5,
            data_source="manual",
            measurement_conditions="fasted",
            time_of_day="morning",
            notes="After workout",
        )

        assert measurement.measurement_time == datetime(2025, 10, 15, 7, 30, 0)
        assert measurement.weight_kg == 72.5
        assert measurement.data_source == "manual"
        assert measurement.measurement_conditions == "fasted"
        assert measurement.time_of_day == "morning"
        assert measurement.notes == "After workout"

    def test_weight_measurement_required_only(self):
        """Test measurement with only required fields."""
        measurement = WeightMeasurement(
            measurement_time=datetime(2025, 10, 15, 7, 30, 0),
            weight_kg=70.0,
            data_source="scale",
        )

        assert measurement.weight_kg == 70.0
        assert measurement.measurement_conditions is None
        assert measurement.time_of_day is None
        assert measurement.notes is None

    def test_weight_measurement_invalid_weight(self):
        """Test that negative weight raises error."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            WeightMeasurement(
                measurement_time=datetime(2025, 10, 15, 7, 30, 0),
                weight_kg=-5.0,
                data_source="manual",
            )

    def test_data_source_normalization(self):
        """Test that data source is normalized to lowercase."""
        measurement = WeightMeasurement(
            measurement_time=datetime(2025, 10, 15, 7, 30, 0),
            weight_kg=70.0,
            data_source="MANUAL",
        )

        assert measurement.data_source == "manual"


class TestWeightDataValidator:
    """Test WeightDataValidator class."""

    def test_valid_measurement(self):
        """Test validation of a valid measurement."""
        measurement = WeightMeasurement(
            measurement_time=datetime(2025, 10, 15, 7, 30, 0),
            weight_kg=72.5,
            data_source="manual",
        )

        is_valid, errors = WeightDataValidator.validate_measurement(measurement)
        assert is_valid
        assert len(errors) == 0

    def test_weight_too_low(self):
        """Test validation of unrealistically low weight."""
        measurement = WeightMeasurement(
            measurement_time=datetime(2025, 10, 15, 7, 30, 0),
            weight_kg=30.0,  # Below 40 kg minimum
            data_source="manual",
        )

        is_valid, errors = WeightDataValidator.validate_measurement(measurement)
        assert not is_valid
        assert any("too low" in error.lower() for error in errors)

    def test_weight_too_high(self):
        """Test validation of unrealistically high weight."""
        measurement = WeightMeasurement(
            measurement_time=datetime(2025, 10, 15, 7, 30, 0),
            weight_kg=250.0,  # Above 200 kg maximum
            data_source="manual",
        )

        is_valid, errors = WeightDataValidator.validate_measurement(measurement)
        assert not is_valid
        assert any("too high" in error.lower() for error in errors)

    def test_future_timestamp(self):
        """Test validation of future measurement time."""
        future_time = datetime.now() + timedelta(days=1)
        measurement = WeightMeasurement(
            measurement_time=future_time,
            weight_kg=72.5,
            data_source="manual",
        )

        is_valid, errors = WeightDataValidator.validate_measurement(measurement)
        assert not is_valid
        assert any("future" in error.lower() for error in errors)

    def test_valid_conditions(self):
        """Test validation accepts valid measurement conditions."""
        for condition in ["fasted", "after_meal", "post_workout", "before_workout", "normal"]:
            measurement = WeightMeasurement(
                measurement_time=datetime(2025, 10, 15, 7, 30, 0),
                weight_kg=72.5,
                data_source="manual",
                measurement_conditions=condition,
            )

            is_valid, errors = WeightDataValidator.validate_measurement(measurement)
            assert is_valid, f"Condition '{condition}' should be valid"

    def test_invalid_conditions(self):
        """Test validation rejects invalid measurement conditions."""
        measurement = WeightMeasurement(
            measurement_time=datetime(2025, 10, 15, 7, 30, 0),
            weight_kg=72.5,
            data_source="manual",
            measurement_conditions="invalid_condition",
        )

        is_valid, errors = WeightDataValidator.validate_measurement(measurement)
        assert not is_valid
        assert any("invalid measurement conditions" in error.lower() for error in errors)

    def test_valid_time_of_day(self):
        """Test validation accepts valid time of day values."""
        for time_of_day in ["morning", "afternoon", "evening", "night"]:
            measurement = WeightMeasurement(
                measurement_time=datetime(2025, 10, 15, 7, 30, 0),
                weight_kg=72.5,
                data_source="manual",
                time_of_day=time_of_day,
            )

            is_valid, errors = WeightDataValidator.validate_measurement(measurement)
            assert is_valid, f"Time of day '{time_of_day}' should be valid"

    def test_invalid_time_of_day(self):
        """Test validation rejects invalid time of day."""
        measurement = WeightMeasurement(
            measurement_time=datetime(2025, 10, 15, 7, 30, 0),
            weight_kg=72.5,
            data_source="manual",
            time_of_day="invalid_time",
        )

        is_valid, errors = WeightDataValidator.validate_measurement(measurement)
        assert not is_valid
        assert any("invalid time of day" in error.lower() for error in errors)


class TestWeightDataImporter:
    """Test WeightDataImporter class."""

    def test_detect_format_csv(self):
        """Test format detection for CSV files."""
        assert WeightDataImporter.detect_format("data.csv") == "csv"
        assert WeightDataImporter.detect_format("DATA.CSV") == "csv"

    def test_detect_format_json(self):
        """Test format detection for JSON files."""
        assert WeightDataImporter.detect_format("data.json") == "json"
        assert WeightDataImporter.detect_format("DATA.JSON") == "json"

    def test_detect_format_apple_health(self):
        """Test format detection for Apple Health XML files."""
        assert WeightDataImporter.detect_format("export.xml") == "apple_health"

    def test_detect_format_unknown(self):
        """Test format detection for unknown file types."""
        assert WeightDataImporter.detect_format("data.txt") is None
        assert WeightDataImporter.detect_format("data.pdf") is None

    def test_import_csv(self):
        """Test importing from CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "weights.csv"

            # Create test CSV
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "weight_kg", "conditions", "time_of_day", "notes"])
                writer.writerow(["2025-11-01 07:30:00", "72.5", "fasted", "morning", "Test 1"])
                writer.writerow(["2025-11-02 07:30:00", "73.0", "after_meal", "morning", "Test 2"])

            # Import
            measurements = WeightDataImporter.import_from_file(str(csv_file))

            assert len(measurements) == 2
            assert measurements[0].weight_kg == 72.5
            assert measurements[0].measurement_conditions == "fasted"
            assert measurements[1].weight_kg == 73.0
            assert measurements[1].notes == "Test 2"

    def test_import_json(self):
        """Test importing from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "weights.json"

            # Create test JSON
            data = [
                {
                    "timestamp": "2025-11-01T07:30:00",
                    "weight_kg": 72.5,
                    "conditions": "fasted",
                    "time_of_day": "morning",
                    "notes": "Test 1",
                },
                {
                    "timestamp": "2025-11-02T07:30:00",
                    "weight_kg": 73.0,
                    "conditions": "after_meal",
                    "time_of_day": "morning",
                    "notes": "Test 2",
                },
            ]

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f)

            # Import
            measurements = WeightDataImporter.import_from_file(str(json_file))

            assert len(measurements) == 2
            assert measurements[0].weight_kg == 72.5
            assert measurements[0].measurement_conditions == "fasted"
            assert measurements[1].weight_kg == 73.0

    def test_import_json_single_object(self):
        """Test importing from JSON file with single object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "weight.json"

            # Create test JSON (single object)
            data = {
                "timestamp": "2025-11-01T07:30:00",
                "weight_kg": 72.5,
                "conditions": "fasted",
            }

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f)

            # Import
            measurements = WeightDataImporter.import_from_file(str(json_file))

            assert len(measurements) == 1
            assert measurements[0].weight_kg == 72.5

    def test_import_file_not_found(self):
        """Test importing from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            WeightDataImporter.import_from_file("/nonexistent/file.csv")

    def test_import_empty_file(self):
        """Test importing from empty file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "empty.csv"

            # Create empty CSV (just headers)
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "weight_kg"])

            # Import should raise ValueError
            with pytest.raises(ValueError, match="No valid measurements"):
                WeightDataImporter.import_from_file(str(csv_file))

    def test_parse_timestamp_formats(self):
        """Test parsing various timestamp formats."""
        # ISO format
        ts1 = WeightDataImporter._parse_timestamp("2025-11-01T07:30:00")
        assert ts1.year == 2025
        assert ts1.month == 11
        assert ts1.day == 1

        # Date with space
        ts2 = WeightDataImporter._parse_timestamp("2025-11-01 07:30:00")
        assert ts2.year == 2025

        # Date only
        ts3 = WeightDataImporter._parse_timestamp("2025-11-01")
        assert ts3.year == 2025
        assert ts3.month == 11

    def test_parse_timestamp_invalid(self):
        """Test parsing invalid timestamp raises error."""
        with pytest.raises(ValueError, match="Could not parse timestamp"):
            WeightDataImporter._parse_timestamp("invalid-date")
