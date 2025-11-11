"""
Weight tracking management system.

This module provides tools for importing, validating, and managing weight data
from various sources (smart scales, Apple Health, manual entry, etc.).

Architecture follows the exercise and heart rate management patterns for consistency.
"""

import hashlib
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from src.db.models import WeightMeasurement as WeightMeasurementModel


@dataclass
class WeightMeasurement:
    """
    A single weight measurement with optional metadata.

    This is the service layer representation used for data transfer
    between importers, validators, and the database manager.
    """

    measurement_time: datetime
    weight_kg: float
    data_source: str  # manual, scale, apple_health, etc.
    measurement_conditions: Optional[str] = None  # fasted, after_meal, post_workout
    time_of_day: Optional[str] = None  # morning, afternoon, evening
    hydrated_before: Optional[bool] = None  # True if drank water before measurement
    source_file: Optional[str] = None  # Path to original file if imported
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        # Ensure weight is positive
        if self.weight_kg <= 0:
            raise ValueError(f"Weight must be positive, got: {self.weight_kg}")

        # Normalize data source to lowercase
        self.data_source = self.data_source.lower()


@dataclass
class WeightSummary:
    """Aggregated summary metrics for displaying weight statistics."""

    total_measurements: int
    avg_weight_kg: float
    min_weight_kg: float
    max_weight_kg: float
    weight_change_kg: float  # First to last measurement
    measurements_by_source: dict[str, int] = field(default_factory=dict)
    moving_avg_7day: Optional[float] = None  # 7-day moving average
    moving_avg_30day: Optional[float] = None  # 30-day moving average
    trend: Optional[str] = None  # stable, gaining, losing


class WeightDataValidator:
    """Validates weight data for quality and consistency."""

    MIN_WEIGHT_KG = 40.0  # Safety bounds
    MAX_WEIGHT_KG = 200.0
    VALID_CONDITIONS = {
        "fasted",
        "after_meal",
        "post_workout",
        "before_workout",
        "normal",
    }
    VALID_TIME_OF_DAY = {"morning", "afternoon", "evening", "night"}

    @classmethod
    def validate_measurement(
        cls, measurement: WeightMeasurement
    ) -> tuple[bool, list[str]]:
        """
        Validate a weight measurement and return validation results.

        Args:
            measurement: WeightMeasurement to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Check weight range
        if measurement.weight_kg < cls.MIN_WEIGHT_KG:
            errors.append(
                f"Weight too low: {measurement.weight_kg} kg "
                f"(minimum: {cls.MIN_WEIGHT_KG})"
            )

        if measurement.weight_kg > cls.MAX_WEIGHT_KG:
            errors.append(
                f"Weight too high: {measurement.weight_kg} kg "
                f"(maximum: {cls.MAX_WEIGHT_KG})"
            )

        # Check timestamp is not in the future
        if measurement.measurement_time > datetime.now():
            errors.append(
                f"Measurement time is in the future: {measurement.measurement_time}"
            )

        # Check measurement conditions if provided
        if measurement.measurement_conditions:
            conditions_lower = measurement.measurement_conditions.lower()
            if conditions_lower not in cls.VALID_CONDITIONS:
                errors.append(
                    f"Invalid measurement conditions: '{measurement.measurement_conditions}'. "
                    f"Valid options: {', '.join(sorted(cls.VALID_CONDITIONS))}"
                )

        # Check time of day if provided
        if measurement.time_of_day:
            time_lower = measurement.time_of_day.lower()
            if time_lower not in cls.VALID_TIME_OF_DAY:
                errors.append(
                    f"Invalid time of day: '{measurement.time_of_day}'. "
                    f"Valid options: {', '.join(sorted(cls.VALID_TIME_OF_DAY))}"
                )

        return len(errors) == 0, errors


class WeightDataImporter:
    """Imports weight data from various file formats."""

    SUPPORTED_FORMATS = {
        ".csv": "csv",
        ".json": "json",
        ".xml": "apple_health",
    }

    @classmethod
    def detect_format(cls, file_path: str) -> Optional[str]:
        """
        Detect file format from extension.

        Args:
            file_path: Path to the file

        Returns:
            Format string (csv, json, apple_health) or None if unknown
        """
        extension = Path(file_path).suffix.lower()
        return cls.SUPPORTED_FORMATS.get(extension)

    @classmethod
    def import_from_file(
        cls, file_path: str, format_hint: Optional[str] = None
    ) -> list[WeightMeasurement]:
        """
        Import weight data from a file.

        Args:
            file_path: Path to the file to import
            format_hint: Optional format override (csv, json, apple_health)

        Returns:
            List of WeightMeasurement objects

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If format is unsupported or data is invalid
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Detect or use provided format
        file_format = format_hint or cls.detect_format(file_path)

        if not file_format:
            raise ValueError(
                f"Could not detect format for: {file_path}. "
                f"Use --format to specify: {', '.join(cls.SUPPORTED_FORMATS.values())}"
            )

        logger.info(f"Importing weight data from {file_path} (format: {file_format})")

        # Import based on format
        if file_format == "csv":
            return cls._import_csv(file_path)
        if file_format == "json":
            return cls._import_json(file_path)
        if file_format == "apple_health":
            return cls._import_apple_health(file_path)

        raise ValueError(f"Unsupported format: {file_format}")

    @classmethod
    def _import_csv(cls, file_path: str) -> list[WeightMeasurement]:
        """
        Import from CSV format.

        Expected columns: timestamp, weight_kg, [conditions], [time_of_day], [notes]
        """
        measurements = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Parse timestamp
                timestamp_str = row.get("timestamp") or row.get("date") or row.get("time")
                if not timestamp_str:
                    logger.warning(f"Skipping row without timestamp: {row}")
                    continue

                timestamp = cls._parse_timestamp(timestamp_str)

                # Parse weight
                weight_str = row.get("weight_kg") or row.get("weight") or row.get("value")
                if not weight_str:
                    logger.warning(f"Skipping row without weight: {row}")
                    continue

                weight_kg = float(weight_str)

                # Optional fields
                conditions = row.get("conditions") or row.get("measurement_conditions")
                time_of_day = row.get("time_of_day")
                notes = row.get("notes")

                measurement = WeightMeasurement(
                    measurement_time=timestamp,
                    weight_kg=weight_kg,
                    data_source="csv",
                    measurement_conditions=conditions,
                    time_of_day=time_of_day,
                    source_file=file_path,
                    notes=notes,
                )

                measurements.append(measurement)

        if not measurements:
            raise ValueError(f"No valid measurements found in {file_path}")

        logger.info(f"Imported {len(measurements)} measurements from CSV")
        return measurements

    @classmethod
    def _import_json(cls, file_path: str) -> list[WeightMeasurement]:
        """
        Import from JSON format.

        Expected format:
        [
          {
            "timestamp": "2025-11-01T07:30:00",
            "weight_kg": 72.5,
            "conditions": "fasted",
            "time_of_day": "morning",
            "notes": "After workout"
          },
          ...
        ]
        """
        measurements = []

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both single object and array
        if isinstance(data, dict):
            data = [data]

        for item in data:
            # Parse timestamp
            timestamp_str = item.get("timestamp") or item.get("date") or item.get("time")
            if not timestamp_str:
                logger.warning(f"Skipping item without timestamp: {item}")
                continue

            timestamp = cls._parse_timestamp(timestamp_str)

            # Parse weight
            weight_kg = item.get("weight_kg") or item.get("weight") or item.get("value")
            if weight_kg is None:
                logger.warning(f"Skipping item without weight: {item}")
                continue

            weight_kg = float(weight_kg)

            # Optional fields
            conditions = item.get("conditions") or item.get("measurement_conditions")
            time_of_day = item.get("time_of_day")
            notes = item.get("notes")

            measurement = WeightMeasurement(
                measurement_time=timestamp,
                weight_kg=weight_kg,
                data_source="json",
                measurement_conditions=conditions,
                time_of_day=time_of_day,
                source_file=file_path,
                notes=notes,
            )

            measurements.append(measurement)

        if not measurements:
            raise ValueError(f"No valid measurements found in {file_path}")

        logger.info(f"Imported {len(measurements)} measurements from JSON")
        return measurements

    @classmethod
    def _import_apple_health(cls, file_path: str) -> list[WeightMeasurement]:
        """
        Import from Apple Health XML export.

        Looks for BodyMass records in the Health export XML.
        """
        measurements = []

        tree = ET.parse(file_path)
        root = tree.getroot()

        # Find all BodyMass records
        for record in root.findall(".//Record[@type='HKQuantityTypeIdentifierBodyMass']"):
            # Parse timestamp
            creation_date = record.get("creationDate")
            if not creation_date:
                logger.warning(f"Skipping record without creationDate")
                continue

            timestamp = cls._parse_timestamp(creation_date)

            # Parse weight (usually in kg, but check unit)
            weight_str = record.get("value")
            unit = record.get("unit", "kg")

            if not weight_str:
                logger.warning(f"Skipping record without value")
                continue

            weight_kg = float(weight_str)

            # Convert if necessary (Apple Health uses kg by default)
            if unit.lower() == "lb":
                weight_kg = weight_kg * 0.453592  # Convert lbs to kg

            measurement = WeightMeasurement(
                measurement_time=timestamp,
                weight_kg=weight_kg,
                data_source="apple_health",
                source_file=file_path,
            )

            measurements.append(measurement)

        if not measurements:
            raise ValueError(f"No BodyMass records found in {file_path}")

        logger.info(f"Imported {len(measurements)} measurements from Apple Health")
        return measurements

    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> datetime:
        """
        Parse timestamp from various formats.

        Supports:
        - ISO format: 2025-11-01T07:30:00
        - Date only: 2025-11-01
        - Apple Health format: 2025-11-01 07:30:00 +0000
        """
        # Try ISO format first
        for fmt in [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S %z",
        ]:
            try:
                return datetime.strptime(timestamp_str.strip(), fmt)
            except ValueError:
                continue

        # Try parsing with fromisoformat
        try:
            return datetime.fromisoformat(timestamp_str.strip())
        except ValueError:
            pass

        raise ValueError(f"Could not parse timestamp: {timestamp_str}")


class WeightDataManager:
    """Manages weight data storage and retrieval."""

    def __init__(self, db_session: Session):
        """
        Initialize the weight data manager.

        Args:
            db_session: SQLAlchemy database session

        Raises:
            ValueError: If db_session is None
        """
        if db_session is None:
            raise ValueError("db_session is required")
        self.db_session = db_session

    def store_measurement(
        self, measurement: WeightMeasurement
    ) -> WeightMeasurementModel:
        """
        Store a weight measurement in the database.

        Args:
            measurement: WeightMeasurement to store

        Returns:
            The stored database model

        Raises:
            ValueError: If validation fails
        """
        # Calculate file hash if from file
        file_hash = None
        if measurement.source_file:
            file_hash = self._calculate_file_hash(measurement.source_file)

        # Create database record
        db_record = WeightMeasurementModel(
            measurement_time=measurement.measurement_time,
            weight_kg=measurement.weight_kg,
            measurement_conditions=measurement.measurement_conditions,
            time_of_day=measurement.time_of_day,
            hydrated_before=measurement.hydrated_before,
            data_source=measurement.data_source,
            data_file_path=measurement.source_file,
            data_hash=file_hash,
            notes=measurement.notes,
        )

        self.db_session.add(db_record)
        self.db_session.commit()

        logger.info(
            f"Stored weight measurement: {measurement.weight_kg} kg "
            f"at {measurement.measurement_time} (ID: {db_record.id})"
        )

        return db_record

    def store_measurements_bulk(
        self, measurements: list[WeightMeasurement]
    ) -> list[WeightMeasurementModel]:
        """
        Store multiple weight measurements in bulk.

        Args:
            measurements: List of WeightMeasurement objects to store

        Returns:
            List of stored database models
        """
        db_records = []

        for measurement in measurements:
            # Calculate file hash if from file
            file_hash = None
            if measurement.source_file:
                file_hash = self._calculate_file_hash(measurement.source_file)

            db_record = WeightMeasurementModel(
                measurement_time=measurement.measurement_time,
                weight_kg=measurement.weight_kg,
                measurement_conditions=measurement.measurement_conditions,
                time_of_day=measurement.time_of_day,
                data_source=measurement.data_source,
                data_file_path=measurement.source_file,
                data_hash=file_hash,
                notes=measurement.notes,
            )

            db_records.append(db_record)

        self.db_session.add_all(db_records)
        self.db_session.commit()

        logger.info(f"Stored {len(db_records)} weight measurements in bulk")

        return db_records

    def get_all(self) -> list[WeightMeasurementModel]:
        """
        Get all weight measurements.

        Returns:
            List of all weight measurements, ordered by measurement_time descending
        """
        return (
            self.db_session.query(WeightMeasurementModel)
            .order_by(WeightMeasurementModel.measurement_time.desc())
            .all()
        )

    def get_by_id(self, measurement_id: int) -> Optional[WeightMeasurementModel]:
        """
        Get a single weight measurement by ID.

        Args:
            measurement_id: ID of the measurement

        Returns:
            WeightMeasurementModel or None if not found
        """
        return (
            self.db_session.query(WeightMeasurementModel)
            .filter(WeightMeasurementModel.id == measurement_id)
            .first()
        )

    def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[WeightMeasurementModel]:
        """
        Get measurements within a date range.

        Args:
            start_date: Start of the date range (inclusive)
            end_date: End of the date range (inclusive)

        Returns:
            List of measurements in the date range, ordered by measurement_time
        """
        return (
            self.db_session.query(WeightMeasurementModel)
            .filter(WeightMeasurementModel.measurement_time >= start_date)
            .filter(WeightMeasurementModel.measurement_time <= end_date)
            .order_by(WeightMeasurementModel.measurement_time)
            .all()
        )

    def delete_measurement(self, measurement_id: int) -> bool:
        """
        Delete a weight measurement by ID.

        Args:
            measurement_id: ID of the measurement to delete

        Returns:
            True if deleted, False if not found
        """
        measurement = self.get_by_id(measurement_id)

        if not measurement:
            return False

        self.db_session.delete(measurement)
        self.db_session.commit()

        logger.info(f"Deleted weight measurement ID: {measurement_id}")

        return True

    def get_summary(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Optional[WeightSummary]:
        """
        Get aggregated statistics for weight measurements.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            WeightSummary with aggregated statistics, or None if no data
        """
        query = self.db_session.query(WeightMeasurementModel)

        # Apply date filters if provided
        if start_date:
            query = query.filter(WeightMeasurementModel.measurement_time >= start_date)
        if end_date:
            query = query.filter(WeightMeasurementModel.measurement_time <= end_date)

        measurements = query.order_by(WeightMeasurementModel.measurement_time).all()

        if not measurements:
            return None

        # Calculate basic stats
        weights = [m.weight_kg for m in measurements]
        total_count = len(weights)
        avg_weight = sum(weights) / total_count
        min_weight = min(weights)
        max_weight = max(weights)
        weight_change = weights[-1] - weights[0]  # Last - First

        # Count by source
        sources = {}
        for m in measurements:
            sources[m.data_source] = sources.get(m.data_source, 0) + 1

        # Calculate moving averages
        moving_avg_7day = None
        moving_avg_30day = None

        if total_count >= 7:
            recent_7 = weights[-7:]
            moving_avg_7day = sum(recent_7) / len(recent_7)

        if total_count >= 30:
            recent_30 = weights[-30:]
            moving_avg_30day = sum(recent_30) / len(recent_30)

        # Determine trend (based on recent vs earlier measurements)
        trend = "stable"
        if total_count >= 7:
            recent_avg = sum(weights[-7:]) / 7
            older_avg = sum(weights[: min(7, total_count - 7)]) / min(7, total_count - 7)

            change_pct = ((recent_avg - older_avg) / older_avg) * 100

            if change_pct > 1.0:  # >1% increase
                trend = "gaining"
            elif change_pct < -1.0:  # >1% decrease
                trend = "losing"

        return WeightSummary(
            total_measurements=total_count,
            avg_weight_kg=round(avg_weight, 1),
            min_weight_kg=round(min_weight, 1),
            max_weight_kg=round(max_weight, 1),
            weight_change_kg=round(weight_change, 1),
            measurements_by_source=sources,
            moving_avg_7day=round(moving_avg_7day, 1) if moving_avg_7day else None,
            moving_avg_30day=round(moving_avg_30day, 1) if moving_avg_30day else None,
            trend=trend,
        )

    @staticmethod
    def _calculate_file_hash(file_path: str) -> str:
        """
        Calculate SHA-256 hash of a file for integrity verification.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash as hex string
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
