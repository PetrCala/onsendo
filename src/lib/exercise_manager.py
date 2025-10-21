"""
Exercise data management system.

This module provides tools for importing, validating, and managing exercise data
from various sources (Apple Watch, Garmin, manual entry, GPX files, etc.).

Architecture mirrors the heart rate management system for consistency.
"""

import hashlib
import json
import os
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from loguru import logger

from src.db.models import ExerciseSession as ExerciseSessionModel, OnsenVisit, HeartRateData
from src.types.exercise import (
    ExerciseType,
    DataSource,
    IndoorOutdoor,
    map_workout_type_to_exercise_type,
)


@dataclass
class ExercisePoint:
    """A single data point in an exercise session (GPS, metrics, etc.)."""

    timestamp: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: Optional[float] = None
    heart_rate: Optional[float] = None
    speed_mps: Optional[float] = None
    distance_km: Optional[float] = None


@dataclass
class ExerciseSession:
    """
    A complete exercise session with metadata and data points.

    This class has many attributes to comprehensively represent
    exercise data from various sources (Apple Health, Garmin, etc.).
    """
    # pylint: disable=too-many-instance-attributes

    start_time: datetime
    end_time: datetime
    exercise_type: ExerciseType
    data_source: DataSource
    source_file: str
    activity_name: Optional[str] = None
    workout_type: Optional[str] = None
    distance_km: Optional[float] = None
    calories_burned: Optional[int] = None
    elevation_gain_m: Optional[float] = None
    avg_heart_rate: Optional[float] = None
    min_heart_rate: Optional[float] = None
    max_heart_rate: Optional[float] = None
    indoor_outdoor: Optional[IndoorOutdoor] = None
    weather_conditions: Optional[str] = None
    data_points: list[ExercisePoint] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Initialize data points list if not provided."""
        if self.data_points is None:
            self.data_points = []

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def route_data_json(self) -> Optional[str]:
        """Serialize route data points to JSON string for database storage."""
        if not self.data_points:
            return None

        route_points = []
        for point in self.data_points:
            point_data = {
                "timestamp": point.timestamp.isoformat(),
            }
            if point.latitude is not None:
                point_data["lat"] = point.latitude
            if point.longitude is not None:
                point_data["lon"] = point.longitude
            if point.elevation_m is not None:
                point_data["elevation"] = point.elevation_m
            if point.heart_rate is not None:
                point_data["hr"] = point.heart_rate
            if point.speed_mps is not None:
                point_data["speed"] = point.speed_mps

            route_points.append(point_data)

        return json.dumps(route_points)


@dataclass
class ExerciseSessionSummary:
    """Aggregated summary metrics for displaying exercise statistics."""

    total_sessions: int
    total_distance_km: float
    total_duration_minutes: int
    total_calories: int
    avg_heart_rate: Optional[float] = None
    sessions_by_type: Optional[dict[str, int]] = None


class ExerciseDataValidator:
    """Validates exercise data for quality and consistency."""

    MIN_HEART_RATE = 30.0
    MAX_HEART_RATE = 220.0
    MIN_DURATION_MINUTES = 1
    MAX_DURATION_HOURS = 24
    MAX_RUNNING_PACE_MIN_PER_KM = 12.0  # 12 min/km = very slow jog
    MIN_RUNNING_PACE_MIN_PER_KM = 2.0  # 2 min/km = world record pace
    MAX_CYCLING_SPEED_KPH = 80.0  # Elite racing speed
    MAX_ELEVATION_GAIN_PER_KM = 500.0  # Extreme climbing

    @classmethod
    def validate_session(cls, session: ExerciseSession) -> tuple[bool, list[str]]:
        """
        Validate an exercise session and return validation results.

        Args:
            session: ExerciseSession to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        # Check duration
        if session.duration_minutes < cls.MIN_DURATION_MINUTES:
            errors.append(
                f"Exercise too short: {session.duration_minutes} minutes "
                f"(minimum: {cls.MIN_DURATION_MINUTES})"
            )

        if session.duration_minutes > cls.MAX_DURATION_HOURS * 60:
            errors.append(
                f"Exercise too long: {session.duration_minutes} minutes "
                f"(maximum: {cls.MAX_DURATION_HOURS * 60})"
            )

        # Check heart rate values (if present)
        if session.min_heart_rate is not None and session.min_heart_rate < cls.MIN_HEART_RATE:
            errors.append(
                f"Unrealistically low heart rate: {session.min_heart_rate} BPM "
                f"(minimum: {cls.MIN_HEART_RATE})"
            )

        if session.max_heart_rate is not None and session.max_heart_rate > cls.MAX_HEART_RATE:
            errors.append(
                f"Unrealistically high heart rate: {session.max_heart_rate} BPM "
                f"(maximum: {cls.MAX_HEART_RATE})"
            )

        # Check distance/pace for running
        if session.exercise_type == ExerciseType.RUNNING and session.distance_km:
            pace = session.duration_minutes / session.distance_km  # min/km

            if pace < cls.MIN_RUNNING_PACE_MIN_PER_KM:
                errors.append(
                    f"Unrealistically fast running pace: {pace:.1f} min/km "
                    f"(minimum: {cls.MIN_RUNNING_PACE_MIN_PER_KM})"
                )

            if pace > cls.MAX_RUNNING_PACE_MIN_PER_KM:
                errors.append(
                    f"Unrealistically slow running pace: {pace:.1f} min/km "
                    f"(maximum: {cls.MAX_RUNNING_PACE_MIN_PER_KM})"
                )

        # Check cycling speed
        if session.exercise_type == ExerciseType.CYCLING and session.distance_km:
            speed_kph = (session.distance_km / session.duration_minutes) * 60

            if speed_kph > cls.MAX_CYCLING_SPEED_KPH:
                errors.append(
                    f"Unrealistically high cycling speed: {speed_kph:.1f} km/h "
                    f"(maximum: {cls.MAX_CYCLING_SPEED_KPH})"
                )

        # Check elevation gain
        if (
            session.elevation_gain_m is not None
            and session.distance_km is not None
            and session.distance_km > 0
        ):
            elevation_per_km = session.elevation_gain_m / session.distance_km

            if elevation_per_km > cls.MAX_ELEVATION_GAIN_PER_KM:
                errors.append(
                    f"Extreme elevation gain: {elevation_per_km:.0f} m/km "
                    f"(maximum: {cls.MAX_ELEVATION_GAIN_PER_KM})"
                )

        # Check data points consistency
        if session.data_points:
            points_errors = cls._validate_data_points(session)
            errors.extend(points_errors)

        return len(errors) == 0, errors

    @classmethod
    def _validate_data_points(cls, session: ExerciseSession) -> list[str]:
        """Validate GPS/metric data points for consistency."""
        errors = []

        if not session.data_points:
            return errors

        # Check for time sequence
        sorted_points = sorted(session.data_points, key=lambda x: x.timestamp)

        for i in range(1, len(sorted_points)):
            time_diff = (
                sorted_points[i].timestamp - sorted_points[i - 1].timestamp
            ).total_seconds()

            # If gap is more than 10 minutes, it's suspicious
            if time_diff > 600:
                errors.append(
                    f"Large gap in data: {time_diff/60:.1f} minutes between points"
                )

        # Check for GPS coordinates consistency (if present)
        gps_points = [p for p in session.data_points if p.latitude and p.longitude]

        if len(gps_points) > 1:
            # Check for unrealistic jumps in position
            for i in range(1, len(gps_points)):
                lat_diff = abs(gps_points[i].latitude - gps_points[i - 1].latitude)
                lon_diff = abs(gps_points[i].longitude - gps_points[i - 1].longitude)

                # Rough check: more than 0.1 degrees (~11km) in one sample is suspicious
                if lat_diff > 0.1 or lon_diff > 0.1:
                    errors.append("Suspicious GPS jump detected in route data")
                    break

        return errors


class ExerciseDataImporter:
    """Imports exercise data from various file formats."""

    SUPPORTED_FORMATS = {
        ".csv": "csv",
        ".json": "json",
        ".gpx": "gpx",
        ".tcx": "tcx",
        ".xml": "apple_health",
    }

    @classmethod
    def import_from_file(
        cls, file_path: str, format_hint: Optional[str] = None
    ) -> ExerciseSession:
        """
        Import exercise data from a file.

        Args:
            file_path: Path to the data file
            format_hint: Optional hint about file format (overrides auto-detection)

        Returns:
            ExerciseSession object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If format is unsupported or data is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine format
        if format_hint:
            file_format = format_hint.lower()
        else:
            file_format = cls.SUPPORTED_FORMATS.get(file_path.suffix.lower())

        if not file_format:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        # Import based on format
        if file_format == "csv":
            return cls._import_csv(file_path)
        elif file_format == "json":
            return cls._import_json(file_path)
        elif file_format == "gpx":
            return cls._import_gpx(file_path)
        elif file_format == "tcx":
            return cls._import_tcx(file_path)
        elif file_format == "apple_health":
            return cls._import_apple_health(file_path)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

    @classmethod
    def _import_csv(cls, file_path: Path) -> ExerciseSession:
        """Import from CSV format."""
        data_points = []
        metadata = {}

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Check if first row contains metadata
            first_row = next(reader, None)
            if first_row and "metadata" in first_row.get("type", "").lower():
                metadata = first_row
                # Start reading actual data from next row
            else:
                # First row is data, include it
                if first_row:
                    f.seek(0)
                    reader = csv.DictReader(f)

            for row in reader:
                try:
                    timestamp_str = row.get("timestamp") or row.get("time")
                    if not timestamp_str:
                        continue

                    timestamp = cls._parse_timestamp(timestamp_str)

                    point = ExercisePoint(timestamp=timestamp)

                    # Parse optional fields
                    if "latitude" in row and row["latitude"]:
                        point.latitude = float(row["latitude"])
                    if "longitude" in row and row["longitude"]:
                        point.longitude = float(row["longitude"])
                    if "elevation" in row and row["elevation"]:
                        point.elevation_m = float(row["elevation"])
                    if "heart_rate" in row and row["heart_rate"]:
                        point.heart_rate = float(row["heart_rate"])
                    if "speed" in row and row["speed"]:
                        point.speed_mps = float(row["speed"])

                    data_points.append(point)

                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping invalid row: {row}, error: {e}")
                    continue

        if not data_points:
            raise ValueError("No valid data points found in CSV file")

        # Sort by timestamp
        data_points.sort(key=lambda x: x.timestamp)

        # Extract metadata or use defaults
        exercise_type = ExerciseType(metadata.get("exercise_type", ExerciseType.OTHER))
        activity_name = metadata.get("activity_name")
        distance_km = float(metadata["distance_km"]) if metadata.get("distance_km") else None
        calories = int(metadata["calories"]) if metadata.get("calories") else None

        # Calculate heart rate stats if present
        hr_points = [p.heart_rate for p in data_points if p.heart_rate is not None]
        avg_hr = sum(hr_points) / len(hr_points) if hr_points else None
        min_hr = min(hr_points) if hr_points else None
        max_hr = max(hr_points) if hr_points else None

        return ExerciseSession(
            start_time=data_points[0].timestamp,
            end_time=data_points[-1].timestamp,
            exercise_type=exercise_type,
            data_source=DataSource.OTHER,
            source_file=str(file_path),
            activity_name=activity_name,
            distance_km=distance_km,
            calories_burned=calories,
            avg_heart_rate=avg_hr,
            min_heart_rate=min_hr,
            max_heart_rate=max_hr,
            data_points=data_points,
        )

    @classmethod
    def _import_json(cls, file_path: Path) -> ExerciseSession:
        """Import from JSON format."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract metadata
        exercise_type = ExerciseType(data.get("exercise_type", ExerciseType.OTHER))
        activity_name = data.get("activity_name")
        start_time = cls._parse_timestamp(data["start_time"])
        end_time = cls._parse_timestamp(data["end_time"])
        distance_km = data.get("distance_km")
        calories = data.get("calories_burned")
        elevation_gain = data.get("elevation_gain_m")
        avg_hr = data.get("avg_heart_rate")
        min_hr = data.get("min_heart_rate")
        max_hr = data.get("max_heart_rate")
        indoor_outdoor = data.get("indoor_outdoor")
        weather = data.get("weather_conditions")

        # Parse data points if present
        data_points = []
        if "route_data" in data:
            for point_data in data["route_data"]:
                timestamp = cls._parse_timestamp(point_data["timestamp"])
                point = ExercisePoint(
                    timestamp=timestamp,
                    latitude=point_data.get("latitude"),
                    longitude=point_data.get("longitude"),
                    elevation_m=point_data.get("elevation"),
                    heart_rate=point_data.get("heart_rate"),
                    speed_mps=point_data.get("speed"),
                )
                data_points.append(point)

        return ExerciseSession(
            start_time=start_time,
            end_time=end_time,
            exercise_type=exercise_type,
            data_source=DataSource.OTHER,
            source_file=str(file_path),
            activity_name=activity_name,
            distance_km=distance_km,
            calories_burned=calories,
            elevation_gain_m=elevation_gain,
            avg_heart_rate=avg_hr,
            min_heart_rate=min_hr,
            max_heart_rate=max_hr,
            indoor_outdoor=IndoorOutdoor(indoor_outdoor) if indoor_outdoor else None,
            weather_conditions=weather,
            data_points=data_points,
        )

    @classmethod
    def _import_gpx(cls, file_path: Path) -> ExerciseSession:
        """Import from GPX format (GPS Exchange Format)."""
        tree = ET.parse(file_path)
        root = tree.getroot()

        # GPX namespace
        ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

        data_points = []
        total_distance = 0.0
        elevations = []

        # Parse track points
        for trkpt in root.findall(".//gpx:trkpt", ns):
            lat = float(trkpt.get("lat"))
            lon = float(trkpt.get("lon"))

            # Parse time
            time_elem = trkpt.find("gpx:time", ns)
            if time_elem is None:
                continue

            timestamp = cls._parse_timestamp(time_elem.text)

            # Parse elevation
            ele_elem = trkpt.find("gpx:ele", ns)
            elevation = float(ele_elem.text) if ele_elem is not None else None

            if elevation is not None:
                elevations.append(elevation)

            # Parse heart rate (from extensions if present)
            hr = None
            extensions = trkpt.find("gpx:extensions", ns)
            if extensions is not None:
                hr_elem = extensions.find(".//*[local-name()='hr']")
                if hr_elem is not None:
                    hr = float(hr_elem.text)

            point = ExercisePoint(
                timestamp=timestamp,
                latitude=lat,
                longitude=lon,
                elevation_m=elevation,
                heart_rate=hr,
            )
            data_points.append(point)

        if not data_points:
            raise ValueError("No valid track points found in GPX file")

        # Sort by timestamp
        data_points.sort(key=lambda x: x.timestamp)

        # Calculate total distance using Haversine formula
        for i in range(1, len(data_points)):
            p1 = data_points[i - 1]
            p2 = data_points[i]
            if p1.latitude and p1.longitude and p2.latitude and p2.longitude:
                dist = cls._haversine_distance(
                    p1.latitude, p1.longitude, p2.latitude, p2.longitude
                )
                total_distance += dist

        # Calculate elevation gain
        elevation_gain = 0.0
        if elevations:
            for i in range(1, len(elevations)):
                diff = elevations[i] - elevations[i - 1]
                if diff > 0:
                    elevation_gain += diff

        # Calculate heart rate stats
        hr_points = [p.heart_rate for p in data_points if p.heart_rate is not None]
        avg_hr = sum(hr_points) / len(hr_points) if hr_points else None
        min_hr = min(hr_points) if hr_points else None
        max_hr = max(hr_points) if hr_points else None

        # Determine exercise type (default to running for GPX files)
        exercise_type = ExerciseType.RUNNING

        return ExerciseSession(
            start_time=data_points[0].timestamp,
            end_time=data_points[-1].timestamp,
            exercise_type=exercise_type,
            data_source=DataSource.GPX_FILE,
            source_file=str(file_path),
            distance_km=total_distance,
            elevation_gain_m=elevation_gain,
            avg_heart_rate=avg_hr,
            min_heart_rate=min_hr,
            max_heart_rate=max_hr,
            indoor_outdoor=IndoorOutdoor.OUTDOOR,
            data_points=data_points,
        )

    @classmethod
    def _import_tcx(cls, file_path: Path) -> ExerciseSession:
        """Import from TCX format (Training Center XML)."""
        tree = ET.parse(file_path)
        root = tree.getroot()

        # TCX namespace
        ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}

        data_points = []
        total_distance = 0.0
        total_calories = 0
        elevations = []

        # Parse activity
        activity = root.find(".//tcx:Activity", ns)
        if activity is None:
            raise ValueError("No activity found in TCX file")

        # Get sport type
        sport = activity.get("Sport", "Other")
        exercise_type = cls._map_tcx_sport_to_exercise_type(sport)

        # Parse laps
        for lap in root.findall(".//tcx:Lap", ns):
            # Parse calories from lap
            calories_elem = lap.find("tcx:Calories", ns)
            if calories_elem is not None:
                total_calories += int(calories_elem.text)

            # Parse track points
            for trackpoint in lap.findall(".//tcx:Trackpoint", ns):
                # Parse time
                time_elem = trackpoint.find("tcx:Time", ns)
                if time_elem is None:
                    continue

                timestamp = cls._parse_timestamp(time_elem.text)

                # Parse position
                lat = None
                lon = None
                position = trackpoint.find("tcx:Position", ns)
                if position is not None:
                    lat_elem = position.find("tcx:LatitudeDegrees", ns)
                    lon_elem = position.find("tcx:LongitudeDegrees", ns)
                    if lat_elem is not None and lon_elem is not None:
                        lat = float(lat_elem.text)
                        lon = float(lon_elem.text)

                # Parse elevation
                ele_elem = trackpoint.find("tcx:AltitudeMeters", ns)
                elevation = float(ele_elem.text) if ele_elem is not None else None

                if elevation is not None:
                    elevations.append(elevation)

                # Parse heart rate
                hr = None
                hr_elem = trackpoint.find(".//tcx:HeartRateBpm/tcx:Value", ns)
                if hr_elem is not None:
                    hr = float(hr_elem.text)

                # Parse distance
                dist_elem = trackpoint.find("tcx:DistanceMeters", ns)
                dist_m = float(dist_elem.text) if dist_elem is not None else None

                point = ExercisePoint(
                    timestamp=timestamp,
                    latitude=lat,
                    longitude=lon,
                    elevation_m=elevation,
                    heart_rate=hr,
                    distance_km=dist_m / 1000 if dist_m else None,
                )
                data_points.append(point)

        if not data_points:
            raise ValueError("No valid track points found in TCX file")

        # Sort by timestamp
        data_points.sort(key=lambda x: x.timestamp)

        # Get total distance from last point (TCX stores cumulative distance)
        total_distance = data_points[-1].distance_km if data_points[-1].distance_km else 0.0

        # Calculate elevation gain
        elevation_gain = 0.0
        if elevations:
            for i in range(1, len(elevations)):
                diff = elevations[i] - elevations[i - 1]
                if diff > 0:
                    elevation_gain += diff

        # Calculate heart rate stats
        hr_points = [p.heart_rate for p in data_points if p.heart_rate is not None]
        avg_hr = sum(hr_points) / len(hr_points) if hr_points else None
        min_hr = min(hr_points) if hr_points else None
        max_hr = max(hr_points) if hr_points else None

        return ExerciseSession(
            start_time=data_points[0].timestamp,
            end_time=data_points[-1].timestamp,
            exercise_type=exercise_type,
            data_source=DataSource.GARMIN,
            source_file=str(file_path),
            distance_km=total_distance,
            calories_burned=total_calories if total_calories > 0 else None,
            elevation_gain_m=elevation_gain,
            avg_heart_rate=avg_hr,
            min_heart_rate=min_hr,
            max_heart_rate=max_hr,
            data_points=data_points,
        )

    @classmethod
    def _import_apple_health(cls, file_path: Path) -> ExerciseSession:
        """Import from Apple Health workout export (XML or CSV)."""
        # Try CSV first, then XML
        if file_path.suffix.lower() == ".csv":
            return cls._import_apple_health_csv(file_path)
        else:
            return cls._import_apple_health_xml(file_path)

    @classmethod
    def _import_apple_health_csv(cls, file_path: Path) -> ExerciseSession:
        """Import from Apple Health CSV export."""
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            workout_data = None
            route_points = []

            for row in reader:
                # Look for workout summary row
                if row.get("type") == "workout":
                    workout_data = row
                # Look for route points
                elif row.get("type") == "route_point":
                    timestamp = cls._parse_timestamp(row["timestamp"])
                    point = ExercisePoint(
                        timestamp=timestamp,
                        latitude=float(row["latitude"]) if row.get("latitude") else None,
                        longitude=float(row["longitude"]) if row.get("longitude") else None,
                        elevation_m=float(row["elevation"]) if row.get("elevation") else None,
                        heart_rate=float(row["heart_rate"]) if row.get("heart_rate") else None,
                    )
                    route_points.append(point)

            if not workout_data:
                raise ValueError("No workout data found in Apple Health CSV")

            # Parse workout metadata
            start_time = cls._parse_timestamp(workout_data["start_time"])
            end_time = cls._parse_timestamp(workout_data["end_time"])
            workout_type = workout_data.get("workout_type", "")
            exercise_type = map_workout_type_to_exercise_type(workout_type)
            distance_km = (
                float(workout_data["distance_km"]) if workout_data.get("distance_km") else None
            )
            calories = (
                int(workout_data["calories"]) if workout_data.get("calories") else None
            )
            avg_hr = (
                float(workout_data["avg_heart_rate"])
                if workout_data.get("avg_heart_rate")
                else None
            )
            min_hr = (
                float(workout_data["min_heart_rate"])
                if workout_data.get("min_heart_rate")
                else None
            )
            max_hr = (
                float(workout_data["max_heart_rate"])
                if workout_data.get("max_heart_rate")
                else None
            )

            return ExerciseSession(
                start_time=start_time,
                end_time=end_time,
                exercise_type=exercise_type,
                data_source=DataSource.APPLE_HEALTH,
                source_file=str(file_path),
                workout_type=workout_type,
                distance_km=distance_km,
                calories_burned=calories,
                avg_heart_rate=avg_hr,
                min_heart_rate=min_hr,
                max_heart_rate=max_hr,
                data_points=route_points if route_points else None,
            )

    @classmethod
    def _import_apple_health_xml(cls, file_path: Path) -> ExerciseSession:
        """Import from Apple Health XML export."""
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Find workout element
        workout = root.find(".//Workout")
        if workout is None:
            raise ValueError("No workout found in Apple Health XML")

        # Parse workout attributes
        workout_type = workout.get("workoutActivityType", "")
        exercise_type = map_workout_type_to_exercise_type(workout_type)

        start_str = workout.get("startDate")
        end_str = workout.get("endDate")
        start_time = cls._parse_timestamp(start_str)
        end_time = cls._parse_timestamp(end_str)

        # Parse distance (in km or mi - need to check unit)
        distance_str = workout.get("distance")
        distance_unit = workout.get("distanceUnit", "km")
        distance_km = None
        if distance_str:
            distance_val = float(distance_str)
            if distance_unit == "mi":
                distance_km = distance_val * 1.60934  # Convert miles to km
            else:
                distance_km = distance_val

        # Parse calories
        calories_str = workout.get("totalEnergyBurned")
        calories = int(float(calories_str)) if calories_str else None

        # Parse route points if present
        route_points = []
        for location in workout.findall(".//WorkoutRoute/Location"):
            timestamp_str = location.get("date")
            if not timestamp_str:
                continue

            timestamp = cls._parse_timestamp(timestamp_str)
            lat = float(location.get("latitude"))
            lon = float(location.get("longitude"))
            elevation = location.get("altitude")
            elevation_m = float(elevation) if elevation else None

            point = ExercisePoint(
                timestamp=timestamp,
                latitude=lat,
                longitude=lon,
                elevation_m=elevation_m,
            )
            route_points.append(point)

        return ExerciseSession(
            start_time=start_time,
            end_time=end_time,
            exercise_type=exercise_type,
            data_source=DataSource.APPLE_HEALTH,
            source_file=str(file_path),
            workout_type=workout_type,
            distance_km=distance_km,
            calories_burned=calories,
            data_points=route_points if route_points else None,
        )

    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> datetime:
        """Parse timestamp string into datetime object."""
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        # Try ISO format
        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Could not parse timestamp: {timestamp_str}")

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two GPS coordinates using Haversine formula.

        Returns:
            Distance in kilometers
        """
        import math

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lon1_rad = math.radians(lon1)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Earth radius in kilometers
        r = 6371.0

        return r * c

    @staticmethod
    def _map_tcx_sport_to_exercise_type(sport: str) -> ExerciseType:
        """Map TCX sport type to Onsendo exercise type."""
        sport_lower = sport.lower()

        if "run" in sport_lower:
            return ExerciseType.RUNNING
        elif "bike" in sport_lower or "cycling" in sport_lower:
            return ExerciseType.CYCLING
        elif "swim" in sport_lower:
            return ExerciseType.SWIMMING
        elif "hike" in sport_lower or "hiking" in sport_lower:
            return ExerciseType.HIKING
        else:
            return ExerciseType.OTHER


class ExerciseDataManager:
    """Manages exercise data storage and retrieval."""

    def __init__(self, db_session: Session):
        """
        Initialize with a required database session.

        Args:
            db_session: SQLAlchemy database session to use for all operations
        """
        if db_session is None:
            raise ValueError("db_session is required")
        self.db_session = db_session

    def store_session(
        self,
        session: ExerciseSession,
        visit_id: Optional[int] = None,
        heart_rate_id: Optional[int] = None,
    ) -> ExerciseSessionModel:
        """
        Store an exercise session in the database.

        Args:
            session: ExerciseSession to store
            visit_id: Optional ID of linked onsen visit
            heart_rate_id: Optional ID of linked heart rate data

        Returns:
            Database ExerciseSession model instance
        """
        # Calculate file hash for integrity
        file_hash = None
        if session.source_file and os.path.exists(session.source_file):
            file_hash = self._calculate_file_hash(session.source_file)

        # Create database record
        exercise_record = ExerciseSessionModel(
            visit_id=visit_id,
            heart_rate_id=heart_rate_id,
            recording_start=session.start_time,
            recording_end=session.end_time,
            duration_minutes=session.duration_minutes,
            exercise_type=session.exercise_type.value,
            activity_name=session.activity_name,
            workout_type=session.workout_type,
            data_source=session.data_source.value,
            data_file_path=session.source_file,
            data_hash=file_hash,
            distance_km=session.distance_km,
            calories_burned=session.calories_burned,
            elevation_gain_m=session.elevation_gain_m,
            avg_heart_rate=session.avg_heart_rate,
            min_heart_rate=session.min_heart_rate,
            max_heart_rate=session.max_heart_rate,
            indoor_outdoor=session.indoor_outdoor.value if session.indoor_outdoor else None,
            weather_conditions=session.weather_conditions,
            route_data=session.route_data_json,
            notes=session.notes,
        )

        self.db_session.add(exercise_record)
        self.db_session.commit()
        record_id = exercise_record.id

        logger.info(f"Stored exercise session: {record_id}")
        return exercise_record

    def link_to_visit(self, exercise_id: int, visit_id: int) -> bool:
        """Link exercise session to an onsen visit."""
        try:
            exercise_record = (
                self.db_session.query(ExerciseSessionModel)
                .filter_by(id=exercise_id)
                .first()
            )
            if not exercise_record:
                logger.error(f"Exercise session {exercise_id} not found")
                return False

            visit_record = self.db_session.query(OnsenVisit).filter_by(id=visit_id).first()
            if not visit_record:
                logger.error(f"Visit record {visit_id} not found")
                return False

            exercise_record.visit_id = visit_id
            self.db_session.commit()

            logger.info(f"Linked exercise {exercise_id} to visit {visit_id}")
            return True

        except Exception as e:
            logger.error(f"Error linking exercise to visit: {e}")
            self.db_session.rollback()
            return False

    def link_to_heart_rate(self, exercise_id: int, heart_rate_id: int) -> bool:
        """Link exercise session to heart rate data."""
        try:
            exercise_record = (
                self.db_session.query(ExerciseSessionModel)
                .filter_by(id=exercise_id)
                .first()
            )
            if not exercise_record:
                logger.error(f"Exercise session {exercise_id} not found")
                return False

            hr_record = (
                self.db_session.query(HeartRateData).filter_by(id=heart_rate_id).first()
            )
            if not hr_record:
                logger.error(f"Heart rate record {heart_rate_id} not found")
                return False

            exercise_record.heart_rate_id = heart_rate_id
            self.db_session.commit()

            logger.info(f"Linked exercise {exercise_id} to heart rate {heart_rate_id}")
            return True

        except Exception as e:
            logger.error(f"Error linking exercise to heart rate: {e}")
            self.db_session.rollback()
            return False

    def unlink_from_visit(self, exercise_id: int) -> bool:
        """Unlink exercise session from its visit."""
        try:
            exercise_record = (
                self.db_session.query(ExerciseSessionModel)
                .filter_by(id=exercise_id)
                .first()
            )
            if not exercise_record:
                logger.error(f"Exercise session {exercise_id} not found")
                return False

            exercise_record.visit_id = None
            self.db_session.commit()

            logger.info(f"Unlinked exercise {exercise_id} from visit")
            return True

        except Exception as e:
            logger.error(f"Error unlinking exercise from visit: {e}")
            self.db_session.rollback()
            return False

    def unlink_from_heart_rate(self, exercise_id: int) -> bool:
        """Unlink exercise session from heart rate data."""
        try:
            exercise_record = (
                self.db_session.query(ExerciseSessionModel)
                .filter_by(id=exercise_id)
                .first()
            )
            if not exercise_record:
                logger.error(f"Exercise session {exercise_id} not found")
                return False

            exercise_record.heart_rate_id = None
            self.db_session.commit()

            logger.info(f"Unlinked exercise {exercise_id} from heart rate")
            return True

        except Exception as e:
            logger.error(f"Error unlinking exercise from heart rate: {e}")
            self.db_session.rollback()
            return False

    def get_by_id(self, exercise_id: int) -> Optional[ExerciseSessionModel]:
        """Get exercise session by ID."""
        return (
            self.db_session.query(ExerciseSessionModel).filter_by(id=exercise_id).first()
        )

    def get_by_visit(self, visit_id: int) -> list[ExerciseSessionModel]:
        """Get all exercise sessions for a specific visit."""
        return (
            self.db_session.query(ExerciseSessionModel).filter_by(visit_id=visit_id).all()
        )

    def get_unlinked(self) -> list[ExerciseSessionModel]:
        """Get all exercise sessions not linked to any visit."""
        return (
            self.db_session.query(ExerciseSessionModel).filter_by(visit_id=None).all()
        )

    def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[ExerciseSessionModel]:
        """Get exercise sessions within a date range."""
        return (
            self.db_session.query(ExerciseSessionModel)
            .filter(
                ExerciseSessionModel.recording_start >= start_date,
                ExerciseSessionModel.recording_end <= end_date,
            )
            .all()
        )

    def get_by_exercise_type(self, exercise_type: ExerciseType) -> list[ExerciseSessionModel]:
        """Get all sessions of a specific exercise type."""
        return (
            self.db_session.query(ExerciseSessionModel)
            .filter_by(exercise_type=exercise_type.value)
            .all()
        )

    def delete_record(self, exercise_id: int) -> bool:
        """Delete an exercise session record."""
        try:
            exercise_record = (
                self.db_session.query(ExerciseSessionModel)
                .filter_by(id=exercise_id)
                .first()
            )
            if not exercise_record:
                logger.error(f"Exercise session {exercise_id} not found")
                return False

            self.db_session.delete(exercise_record)
            self.db_session.commit()

            logger.info(f"Deleted exercise session {exercise_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting exercise session: {e}")
            self.db_session.rollback()
            return False

    def get_weekly_summary(
        self, week_start: datetime, week_end: datetime
    ) -> ExerciseSessionSummary:
        """
        Get aggregated exercise statistics for a week (for rule revisions).

        Args:
            week_start: Start of the week
            week_end: End of the week

        Returns:
            ExerciseSessionSummary with aggregated metrics
        """
        sessions = self.get_by_date_range(week_start, week_end)

        total_sessions = len(sessions)
        total_distance = sum(s.distance_km for s in sessions if s.distance_km)
        total_duration = sum(s.duration_minutes for s in sessions)
        total_calories = sum(s.calories_burned for s in sessions if s.calories_burned)

        # Calculate average heart rate across all sessions
        hr_sessions = [s for s in sessions if s.avg_heart_rate]
        avg_hr = (
            sum(s.avg_heart_rate for s in hr_sessions) / len(hr_sessions)
            if hr_sessions
            else None
        )

        # Count sessions by type
        sessions_by_type = {}
        for session in sessions:
            ex_type = session.exercise_type
            sessions_by_type[ex_type] = sessions_by_type.get(ex_type, 0) + 1

        return ExerciseSessionSummary(
            total_sessions=total_sessions,
            total_distance_km=total_distance,
            total_duration_minutes=total_duration,
            total_calories=total_calories,
            avg_heart_rate=avg_hr,
            sessions_by_type=sessions_by_type,
        )

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def validate_file_integrity(self, exercise_id: int) -> bool:
        """Validate that the stored file hash matches the current file."""
        try:
            exercise_record = (
                self.db_session.query(ExerciseSessionModel)
                .filter_by(id=exercise_id)
                .first()
            )

            if not exercise_record:
                return False

            if not exercise_record.data_file_path:
                return True  # No file to validate

            if not os.path.exists(exercise_record.data_file_path):
                logger.warning(f"File not found: {exercise_record.data_file_path}")
                return False

            current_hash = self._calculate_file_hash(exercise_record.data_file_path)
            return current_hash == exercise_record.data_hash

        except Exception as e:
            logger.error(f"Error validating file integrity: {e}")
            return False

    def suggest_visit_links(
        self, exercise_id: int, time_window_hours: int = 2
    ) -> list[tuple[int, str]]:
        """
        Suggest potential onsen visits to link based on timestamps.

        Args:
            exercise_id: ID of exercise session
            time_window_hours: How many hours before/after exercise to search

        Returns:
            List of (visit_id, description) tuples
        """
        exercise = self.get_by_id(exercise_id)
        if not exercise:
            return []

        # Search for visits within time window
        time_window = timedelta(hours=time_window_hours)
        search_start = exercise.recording_end - time_window
        search_end = exercise.recording_end + time_window

        potential_visits = (
            self.db_session.query(OnsenVisit)
            .filter(
                OnsenVisit.visit_time >= search_start,
                OnsenVisit.visit_time <= search_end,
            )
            .all()
        )

        suggestions = []
        for visit in potential_visits:
            time_diff = abs((visit.visit_time - exercise.recording_end).total_seconds() / 60)
            description = (
                f"Visit at {visit.visit_time.strftime('%Y-%m-%d %H:%M')} "
                f"({time_diff:.0f} min after exercise)"
            )
            suggestions.append((visit.id, description))

        return suggestions
