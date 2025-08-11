"""
Heart rate data management system.

This module provides tools for importing, validating, and managing heart rate data
from various sources (smart watches, fitness trackers, etc.).
"""

import hashlib
import json
import os
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging

from src.db.conn import get_db
from src.const import CONST
from src.db.models import HeartRateData, OnsenVisit

logger = logging.getLogger(__name__)


@dataclass
class HeartRatePoint:
    """A single heart rate measurement point."""

    timestamp: datetime
    heart_rate: float
    confidence: Optional[float] = None


@dataclass
class HeartRateSession:
    """A complete heart rate recording session."""

    start_time: datetime
    end_time: datetime
    data_points: List[HeartRatePoint]
    format: str
    source_file: str
    notes: Optional[str] = None

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def average_heart_rate(self) -> float:
        """Calculate average heart rate."""
        if not self.data_points:
            return 0.0
        return sum(point.heart_rate for point in self.data_points) / len(
            self.data_points
        )

    @property
    def min_heart_rate(self) -> float:
        """Get minimum heart rate."""
        if not self.data_points:
            return 0.0
        return min(point.heart_rate for point in self.data_points)

    @property
    def max_heart_rate(self) -> float:
        """Get maximum heart rate."""
        if not self.data_points:
            return 0.0
        return max(point.heart_rate for point in self.data_points)

    @property
    def data_points_count(self) -> int:
        """Get number of data points."""
        return len(self.data_points)


class HeartRateDataValidator:
    """Validates heart rate data for quality and consistency."""

    MIN_HEART_RATE = 30.0  # Very low but possible during sleep
    MAX_HEART_RATE = 220.0  # Very high but possible during extreme exercise
    MIN_DURATION_MINUTES = 1  # Minimum recording duration
    MAX_DURATION_HOURS = 24  # Maximum reasonable recording duration
    MIN_DATA_POINTS = 5  # Minimum data points for meaningful analysis

    @classmethod
    def validate_session(cls, session: HeartRateSession) -> Tuple[bool, List[str]]:
        """Validate a heart rate session and return validation results."""
        errors = []

        # Check duration
        if session.duration_minutes < cls.MIN_DURATION_MINUTES:
            errors.append(
                f"Recording too short: {session.duration_minutes} minutes (minimum: {cls.MIN_DURATION_MINUTES})"
            )

        if session.duration_minutes > cls.MAX_DURATION_HOURS * 60:
            errors.append(
                f"Recording too long: {session.duration_minutes} minutes (maximum: {cls.MAX_DURATION_HOURS * 60})"
            )

        # Check data points
        if session.data_points_count < cls.MIN_DATA_POINTS:
            errors.append(
                f"Too few data points: {session.data_points_count} (minimum: {cls.MIN_DATA_POINTS})"
            )

        # Check heart rate values
        if session.min_heart_rate < cls.MIN_HEART_RATE:
            errors.append(
                f"Unrealistically low heart rate: {session.min_heart_rate} BPM (minimum: {cls.MIN_HEART_RATE})"
            )

        if session.max_heart_rate > cls.MAX_HEART_RATE:
            errors.append(
                f"Unrealistically high heart rate: {session.max_heart_rate} BPM (maximum: {cls.MAX_HEART_RATE})"
            )

        # Check for reasonable variation
        if session.max_heart_rate - session.min_heart_rate < 10:
            errors.append("Heart rate variation too low - data may be invalid")

        # Check for gaps in data
        gaps = cls._check_data_gaps(session)
        if gaps:
            errors.extend(gaps)

        return len(errors) == 0, errors

    @classmethod
    def _check_data_gaps(cls, session: HeartRateSession) -> List[str]:
        """Check for suspicious gaps in heart rate data."""
        if len(session.data_points) < 2:
            return []

        gaps = []
        sorted_points = sorted(session.data_points, key=lambda x: x.timestamp)

        for i in range(1, len(sorted_points)):
            time_diff = (
                sorted_points[i].timestamp - sorted_points[i - 1].timestamp
            ).total_seconds()

            # If gap is more than 5 minutes, it's suspicious
            if time_diff > 300:
                gaps.append(
                    f"Large gap in data: {time_diff/60:.1f} minutes between measurements"
                )

        return gaps


class HeartRateDataImporter:
    """Imports heart rate data from various file formats."""

    SUPPORTED_FORMATS = {
        ".csv": "csv",
        ".json": "json",
        ".txt": "text",
        ".health": "apple_health",
    }

    @classmethod
    def import_from_file(
        cls, file_path: str, format_hint: Optional[str] = None
    ) -> HeartRateSession:
        """Import heart rate data from a file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine format
        if format_hint and format_hint in cls.SUPPORTED_FORMATS.values():
            file_format = format_hint
        else:
            file_format = cls.SUPPORTED_FORMATS.get(file_path.suffix.lower())

        if not file_format:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        # Import based on format
        if file_format == "csv":
            return cls._import_csv(file_path)
        elif file_format == "json":
            return cls._import_json(file_path)
        elif file_format == "text":
            return cls._import_text(file_path)
        elif file_format == "apple_health":
            return cls._import_apple_health(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

    @classmethod
    def _import_csv(cls, file_path: Path) -> HeartRateSession:
        """Import from CSV format."""
        data_points = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Try common column names
                    timestamp_str = (
                        row.get("timestamp") or row.get("time") or row.get("date")
                    )
                    heart_rate_str = (
                        row.get("heart_rate") or row.get("hr") or row.get("bpm")
                    )

                    if not timestamp_str or not heart_rate_str:
                        continue

                    # Parse timestamp
                    timestamp = cls._parse_timestamp(timestamp_str)
                    heart_rate = float(heart_rate_str)

                    # Get confidence if available
                    confidence = None
                    if "confidence" in row:
                        try:
                            confidence = float(row["confidence"])
                        except ValueError:
                            pass

                    data_points.append(
                        HeartRatePoint(timestamp, heart_rate, confidence)
                    )

                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid row: {row}, error: {e}")
                    continue

        if not data_points:
            raise ValueError("No valid data points found in CSV file")

        # Sort by timestamp
        data_points.sort(key=lambda x: x.timestamp)

        return HeartRateSession(
            start_time=data_points[0].timestamp,
            end_time=data_points[-1].timestamp,
            data_points=data_points,
            format="csv",
            source_file=str(file_path),
        )

    @classmethod
    def _import_json(cls, file_path: Path) -> HeartRateSession:
        """Import from JSON format."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data_points = []

        # Handle different JSON structures
        if isinstance(data, list):
            # List of measurements
            for item in data:
                try:
                    timestamp = cls._parse_timestamp(
                        item.get("timestamp", item.get("time"))
                    )
                    heart_rate = float(
                        item.get("heart_rate", item.get("hr", item.get("bpm")))
                    )
                    confidence = item.get("confidence")

                    data_points.append(
                        HeartRatePoint(timestamp, heart_rate, confidence)
                    )
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid item: {item}, error: {e}")
                    continue

        elif isinstance(data, dict):
            # Single session with data points
            if "data_points" in data:
                for point in data["data_points"]:
                    try:
                        timestamp = cls._parse_timestamp(
                            point.get("timestamp", point.get("time"))
                        )
                        heart_rate = float(
                            point.get("heart_rate", point.get("hr", point.get("bpm")))
                        )
                        confidence = point.get("confidence")

                        data_points.append(
                            HeartRatePoint(timestamp, heart_rate, confidence)
                        )
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid point: {point}, error: {e}")
                        continue

        if not data_points:
            raise ValueError("No valid data points found in JSON file")

        # Sort by timestamp
        data_points.sort(key=lambda x: x.timestamp)

        return HeartRateSession(
            start_time=data_points[0].timestamp,
            end_time=data_points[-1].timestamp,
            data_points=data_points,
            format="json",
            source_file=str(file_path),
        )

    @classmethod
    def _import_text(cls, file_path: Path) -> HeartRateSession:
        """Import from plain text format (timestamp, heart_rate pairs)."""
        data_points = []

        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    parts = line.split(",")
                    if len(parts) >= 2:
                        timestamp_str = parts[0].strip()
                        heart_rate_str = parts[1].strip()

                        timestamp = cls._parse_timestamp(timestamp_str)
                        heart_rate = float(heart_rate_str)

                        confidence = None
                        if len(parts) >= 3:
                            try:
                                confidence = float(parts[2].strip())
                            except ValueError:
                                pass

                        data_points.append(
                            HeartRatePoint(timestamp, heart_rate, confidence)
                        )

                except (ValueError, KeyError) as e:
                    logger.warning(
                        f"Skipping invalid line {line_num}: {line}, error: {e}"
                    )
                    continue

        if not data_points:
            raise ValueError("No valid data points found in text file")

        # Sort by timestamp
        data_points.sort(key=lambda x: x.timestamp)

        return HeartRateSession(
            start_time=data_points[0].timestamp,
            end_time=data_points[-1].timestamp,
            data_points=data_points,
            format="text",
            source_file=str(file_path),
        )

    @classmethod
    def _import_apple_health(cls, file_path: Path) -> HeartRateSession:
        """Import from Apple Health CSV format."""
        data_points = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Check if this is a heart rate row
                    if row.get("SampleType") != "HEART_RATE":
                        continue

                    # Parse timestamp
                    timestamp_str = row.get("StartTime", "")
                    if not timestamp_str:
                        continue

                    # Handle Apple Health timestamp format (ISO with Z suffix)
                    timestamp = cls._parse_timestamp(timestamp_str)

                    # Parse heart rate data (semicolon-separated values)
                    hr_data = row.get("Data", "")
                    if not hr_data:
                        continue

                    # Split by semicolon and parse each heart rate value
                    hr_values = hr_data.split(";")
                    sample_rate = float(row.get("SampleRate", 1.0))

                    # Calculate time interval between samples
                    time_interval = 1.0 / sample_rate if sample_rate > 0 else 1.0

                    for i, hr_str in enumerate(hr_values):
                        try:
                            heart_rate = float(hr_str.strip())

                            # Calculate timestamp for this sample
                            sample_timestamp = timestamp + timedelta(
                                seconds=i * time_interval
                            )

                            # Create data point (no confidence data in Apple Health format)
                            data_points.append(
                                HeartRatePoint(sample_timestamp, heart_rate, None)
                            )

                        except ValueError:
                            # Skip invalid heart rate values
                            continue

                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid row: {row}, error: {e}")
                    continue

        if not data_points:
            raise ValueError("No valid heart rate data found in Apple Health file")

        # Sort by timestamp
        data_points.sort(key=lambda x: x.timestamp)

        return HeartRateSession(
            start_time=data_points[0].timestamp,
            end_time=data_points[-1].timestamp,
            data_points=data_points,
            format="apple_health",
            source_file=str(file_path),
        )

    @classmethod
    def _parse_timestamp(cls, timestamp_str: str) -> datetime:
        """Parse timestamp string into datetime object."""
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%H:%M:%S",
            "%H:%M",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # If none work, try to parse as ISO format
        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Could not parse timestamp: {timestamp_str}")


class HeartRateDataManager:
    """Manages heart rate data storage and retrieval."""

    def __init__(self, db_session=None):
        """Initialize with an optional database session.

        If no session is provided, the manager will create its own
        database connection for each operation.
        """
        self.db_session = db_session

    def store_session(
        self, session: HeartRateSession, visit_id: Optional[int] = None
    ) -> HeartRateData:
        """Store a heart rate session in the database."""
        # Calculate file hash for integrity
        file_hash = self._calculate_file_hash(session.source_file)

        # Create database record
        heart_rate_record = HeartRateData(
            visit_id=visit_id,
            recording_start=session.start_time,
            recording_end=session.end_time,
            data_format=session.format,
            data_file_path=session.source_file,
            data_hash=file_hash,
            average_heart_rate=session.average_heart_rate,
            min_heart_rate=session.min_heart_rate,
            max_heart_rate=session.max_heart_rate,
            total_recording_minutes=session.duration_minutes,
            data_points_count=session.data_points_count,
            notes=session.notes,
        )

        if self.db_session:
            # Use provided session
            self.db_session.add(heart_rate_record)
            self.db_session.commit()
        else:
            # Create our own database connection
            with get_db(CONST.DATABASE_URL) as db:
                db.add(heart_rate_record)
                db.commit()

        logger.info(f"Stored heart rate session: {heart_rate_record.id}")
        return heart_rate_record

    def link_to_visit(self, heart_rate_id: int, visit_id: int) -> bool:
        """Link heart rate data to an onsen visit."""
        try:
            if self.db_session:
                # Use provided session
                heart_rate_record = (
                    self.db_session.query(HeartRateData)
                    .filter_by(id=heart_rate_id)
                    .first()
                )
                if not heart_rate_record:
                    logger.error(f"Heart rate record {heart_rate_id} not found")
                    return False

                visit_record = (
                    self.db_session.query(OnsenVisit).filter_by(id=visit_id).first()
                )
                if not visit_record:
                    logger.error(f"Visit record {visit_id} not found")
                    return False

                heart_rate_record.visit_id = visit_id
                self.db_session.commit()

                logger.info(f"Linked heart rate {heart_rate_id} to visit {visit_id}")
                return True
            else:
                # Create our own database connection
                with get_db(CONST.DATABASE_URL) as db:
                    heart_rate_record = (
                        db.query(HeartRateData).filter_by(id=heart_rate_id).first()
                    )
                    if not heart_rate_record:
                        logger.error(f"Heart rate record {heart_rate_id} not found")
                        return False

                    visit_record = db.query(OnsenVisit).filter_by(id=visit_id).first()
                    if not visit_record:
                        logger.error(f"Visit record {visit_id} not found")
                        return False

                    heart_rate_record.visit_id = visit_id
                    db.commit()

                    logger.info(
                        f"Linked heart rate {heart_rate_id} to visit {visit_id}"
                    )
                    return True

        except Exception as e:
            logger.error(f"Error linking heart rate to visit: {e}")
            if self.db_session:
                self.db_session.rollback()
            return False

    def unlink_from_visit(self, heart_rate_id: int) -> bool:
        """Unlink heart rate data from its visit."""
        try:
            heart_rate_record = (
                self.db_session.query(HeartRateData).filter_by(id=heart_rate_id).first()
            )
            if not heart_rate_record:
                logger.error(f"Heart rate record {heart_rate_id} not found")
                return False

            heart_rate_record.visit_id = None
            self.db_session.commit()

            logger.info(f"Unlinked heart rate {heart_rate_id} from visit")
            return True

        except Exception as e:
            logger.error(f"Error unlinking heart rate from visit: {e}")
            self.db_session.rollback()
            return False

    def get_by_visit(self, visit_id: int) -> List[HeartRateData]:
        """Get all heart rate data for a specific visit."""
        return self.db_session.query(HeartRateData).filter_by(visit_id=visit_id).all()

    def get_unlinked(self) -> List[HeartRateData]:
        """Get all heart rate data not linked to any visit."""
        return self.db_session.query(HeartRateData).filter_by(visit_id=None).all()

    def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[HeartRateData]:
        """Get heart rate data within a date range."""
        return (
            self.db_session.query(HeartRateData)
            .filter(
                HeartRateData.recording_start >= start_date,
                HeartRateData.recording_end <= end_date,
            )
            .all()
        )

    def delete_record(self, heart_rate_id: int) -> bool:
        """Delete a heart rate record."""
        try:
            heart_rate_record = (
                self.db_session.query(HeartRateData).filter_by(id=heart_rate_id).first()
            )
            if not heart_rate_record:
                logger.error(f"Heart rate record {heart_rate_id} not found")
                return False

            self.db_session.delete(heart_rate_record)
            self.db_session.commit()

            logger.info(f"Deleted heart rate record {heart_rate_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting heart rate record: {e}")
            self.db_session.rollback()
            return False

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def validate_file_integrity(self, heart_rate_id: int) -> bool:
        """Validate that the stored file hash matches the current file."""
        try:
            heart_rate_record = (
                self.db_session.query(HeartRateData).filter_by(id=heart_rate_id).first()
            )
            if not heart_rate_record:
                return False

            if not os.path.exists(heart_rate_record.data_file_path):
                logger.warning(f"File not found: {heart_rate_record.data_file_path}")
                return False

            current_hash = self._calculate_file_hash(heart_rate_record.data_file_path)
            return current_hash == heart_rate_record.data_hash

        except Exception as e:
            logger.error(f"Error validating file integrity: {e}")
            return False
