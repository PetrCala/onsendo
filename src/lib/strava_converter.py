"""
Strava data conversion utilities.

This module provides converters for transforming Strava API data into
Onsendo-compatible formats (ExerciseSession, HeartRateSession) and
standard file formats (GPX, JSON, CSV).
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Mapping, Optional

from loguru import logger

from src.lib.exercise_manager import ExercisePoint, ExerciseSession
from src.lib.heart_rate_manager import HeartRatePoint, HeartRateSession
from src.types.exercise import DataSource, ExerciseType, IndoorOutdoor
from src.types.strava import StravaActivityDetail, StravaStream


class StravaActivityTypeMapper:
    """Maps Strava activity types to Onsendo exercise types."""

    TYPE_MAPPING: dict[str, ExerciseType] = {
        # Running
        "Run": ExerciseType.RUNNING,
        "TrailRun": ExerciseType.RUNNING,
        "VirtualRun": ExerciseType.RUNNING,
        # Cycling
        "Ride": ExerciseType.CYCLING,
        "VirtualRide": ExerciseType.CYCLING,
        "MountainBikeRide": ExerciseType.CYCLING,
        "GravelRide": ExerciseType.CYCLING,
        "EBikeRide": ExerciseType.CYCLING,
        "Velomobile": ExerciseType.CYCLING,
        # Hiking & Walking
        "Hike": ExerciseType.HIKING,
        "Walk": ExerciseType.WALKING,
        # Swimming
        "Swim": ExerciseType.SWIMMING,
        # Yoga & Flexibility
        "Yoga": ExerciseType.YOGA,
        # Gym & Strength
        "WeightTraining": ExerciseType.GYM,
        "Workout": ExerciseType.GYM,
        "Crossfit": ExerciseType.GYM,
        "StairStepper": ExerciseType.GYM,
        "Elliptical": ExerciseType.GYM,
        "Rowing": ExerciseType.GYM,
        "RockClimbing": ExerciseType.GYM,
        # Other sports
        "AlpineSki": ExerciseType.OTHER,
        "BackcountrySki": ExerciseType.OTHER,
        "Canoeing": ExerciseType.OTHER,
        "Kayaking": ExerciseType.OTHER,
        "Snowboard": ExerciseType.OTHER,
        "Surfing": ExerciseType.OTHER,
    }

    @classmethod
    def map_type(cls, strava_type: str) -> ExerciseType:
        """
        Map Strava activity type to Onsendo ExerciseType.

        Args:
            strava_type: Strava activity type string

        Returns:
            Corresponding ExerciseType

        Example:
            >>> StravaActivityTypeMapper.map_type("Run")
            ExerciseType.RUNNING
            >>> StravaActivityTypeMapper.map_type("WeightTraining")
            ExerciseType.GYM
        """
        return cls.TYPE_MAPPING.get(strava_type, ExerciseType.OTHER)


class StravaToExerciseConverter:
    """Converts Strava activities to ExerciseSession objects."""

    @classmethod
    def convert(
        cls,
        activity: StravaActivityDetail,
        streams: Optional[dict[str, StravaStream]] = None,
    ) -> ExerciseSession:
        """
        Convert Strava activity to ExerciseSession.

        Args:
            activity: Strava activity detail
            streams: Optional stream data (GPS, HR, etc.)

        Returns:
            ExerciseSession object ready for database storage

        Example:
            >>> activity = client.get_activity(12345678)
            >>> streams = client.get_activity_streams(12345678)
            >>> session = StravaToExerciseConverter.convert(activity, streams)
            >>> manager.store_session(session)
        """
        # Map activity type
        exercise_type = StravaActivityTypeMapper.map_type(activity.activity_type)

        # Determine indoor/outdoor
        indoor_outdoor = IndoorOutdoor.UNKNOWN
        if "Virtual" in activity.activity_type or "Indoor" in activity.activity_type:
            indoor_outdoor = IndoorOutdoor.INDOOR
        elif activity.start_latlng or streams and "latlng" in streams:
            indoor_outdoor = IndoorOutdoor.OUTDOOR

        # Build data points from streams
        data_points = []
        if streams:
            data_points = cls._build_data_points(streams, activity.start_date)

        # Calculate elevation gain if not provided
        elevation_gain_m = activity.total_elevation_gain_m
        if elevation_gain_m is None and streams and "altitude" in streams:
            elevation_gain_m = cls._calculate_elevation_gain(streams["altitude"])

        return ExerciseSession(
            start_time=activity.start_date_local,
            end_time=activity.start_date_local
            + timedelta(seconds=activity.elapsed_time_s),
            exercise_type=exercise_type,
            data_source=DataSource.STRAVA,
            source_file=f"strava_activity_{activity.id}",
            activity_name=activity.name,
            workout_type=activity.sport_type,
            distance_km=activity.distance_km,
            calories_burned=activity.calories,
            elevation_gain_m=elevation_gain_m,
            avg_heart_rate=activity.average_heartrate,
            min_heart_rate=None,  # Strava doesn't provide min HR in activity details
            max_heart_rate=activity.max_heartrate,
            indoor_outdoor=indoor_outdoor,
            weather_conditions=None,  # Could add temp if available
            data_points=data_points if data_points else None,
            notes=activity.description,
        )

    @classmethod
    def _build_data_points(
        cls, streams: dict[str, StravaStream], start_time: datetime
    ) -> list[ExercisePoint]:
        """
        Build ExercisePoint objects from Strava streams.

        Combines time, latlng, altitude, heartrate, and velocity
        streams into unified data points.

        Args:
            streams: Dictionary of stream data
            start_time: Activity start time

        Returns:
            List of ExercisePoint objects
        """
        points = []

        # Get stream data
        time_stream = streams.get("time")
        latlng_stream = streams.get("latlng")
        altitude_stream = streams.get("altitude")
        hr_stream = streams.get("heartrate")
        distance_stream = streams.get("distance")
        velocity_stream = streams.get("velocity_smooth")

        if not time_stream:
            return []

        # Build points from time stream (common basis)
        for i, time_offset in enumerate(time_stream.data):
            timestamp = start_time + timedelta(seconds=time_offset)

            # Extract data from each stream at index i
            lat, lon = None, None
            if latlng_stream and i < len(latlng_stream.data):
                latlng = latlng_stream.data[i]
                if latlng and len(latlng) >= 2:
                    lat, lon = float(latlng[0]), float(latlng[1])

            elevation = None
            if altitude_stream and i < len(altitude_stream.data):
                elevation = float(altitude_stream.data[i])

            hr = None
            if hr_stream and i < len(hr_stream.data):
                hr = float(hr_stream.data[i])

            speed = None
            if velocity_stream and i < len(velocity_stream.data):
                speed = float(velocity_stream.data[i])

            distance = None
            if distance_stream and i < len(distance_stream.data):
                distance = float(distance_stream.data[i]) / 1000  # Convert to km

            point = ExercisePoint(
                timestamp=timestamp,
                latitude=lat,
                longitude=lon,
                elevation_m=elevation,
                heart_rate=hr,
                speed_mps=speed,
                distance_km=distance,
            )
            points.append(point)

        return points

    @classmethod
    def _calculate_elevation_gain(cls, altitude_stream: StravaStream) -> float:
        """
        Calculate total elevation gain from altitude data.

        Args:
            altitude_stream: Altitude stream data

        Returns:
            Total elevation gain in meters
        """
        if not altitude_stream or not altitude_stream.data:
            return 0.0

        elevation_gain = 0.0
        for i in range(1, len(altitude_stream.data)):
            diff = altitude_stream.data[i] - altitude_stream.data[i - 1]
            if diff > 0:
                elevation_gain += diff

        return elevation_gain


class StravaToHeartRateConverter:
    """Converts Strava activities to HeartRateSession objects."""

    @classmethod
    def convert(
        cls, activity: StravaActivityDetail, hr_stream: StravaStream
    ) -> HeartRateSession:
        """
        Convert Strava activity with HR data to HeartRateSession.

        Args:
            activity: Strava activity detail
            hr_stream: Heart rate stream data

        Returns:
            HeartRateSession object ready for database storage

        Example:
            >>> activity = client.get_activity(12345678)
            >>> streams = client.get_activity_streams(12345678, ["heartrate", "time"])
            >>> if "heartrate" in streams:
            ...     hr_session = StravaToHeartRateConverter.convert(
            ...         activity, streams["heartrate"]
            ...     )
        """
        # Get time stream for timestamps
        time_stream = None
        if hasattr(hr_stream, "time_stream"):
            time_stream = hr_stream.time_stream

        # Build HR data points
        hr_points = cls._build_hr_points(
            hr_stream, time_stream, activity.start_date_local
        )

        return HeartRateSession(
            start_time=activity.start_date_local,
            end_time=activity.start_date_local
            + timedelta(seconds=activity.elapsed_time_s),
            data_points=hr_points,
            format="strava",
            source_file=f"strava_activity_{activity.id}_hr",
            notes=f"Heart rate data from Strava activity: {activity.name}",
        )

    @classmethod
    def _build_hr_points(
        cls,
        hr_stream: StravaStream,
        time_stream: Optional[StravaStream],
        start_time: datetime,
    ) -> list[HeartRatePoint]:
        """
        Build HeartRatePoint objects from heart rate stream.

        Args:
            hr_stream: Heart rate stream
            time_stream: Time stream (for timestamps)
            start_time: Activity start time

        Returns:
            List of HeartRatePoint objects
        """
        points = []

        if not hr_stream or not hr_stream.data:
            return points

        for i, hr_value in enumerate(hr_stream.data):
            # Calculate timestamp
            if time_stream and i < len(time_stream.data):
                time_offset = time_stream.data[i]
                timestamp = start_time + timedelta(seconds=time_offset)
            else:
                # Estimate based on index (assume 1 second intervals)
                timestamp = start_time + timedelta(seconds=i)

            point = HeartRatePoint(timestamp=timestamp, heart_rate=float(hr_value))
            points.append(point)

        return points


class StravaFileExporter:
    """Exports Strava activities to standard file formats."""

    @staticmethod
    def has_gpx_support(streams: Mapping[str, StravaStream]) -> bool:
        """Check whether provided streams contain enough data for GPX export."""

        time_stream = streams.get("time")
        latlng_stream = streams.get("latlng")

        if not time_stream or not latlng_stream:
            return False

        return bool(time_stream.data and latlng_stream.data)

    @classmethod
    def recommend_formats(
        cls,
        streams: dict[str, StravaStream],
        requested_formats: list[str],
    ) -> tuple[list[str], list[tuple[str, str]]]:
        """
        Determine which formats can be exported based on available streams.

        Automatically selects appropriate formats based on stream availability:
        - GPX requires GPS data (latlng + time streams)
        - JSON always works (exports all available data)
        - HR CSV requires heart rate data

        If no formats are exportable, JSON is added as fallback to ensure
        some data is always captured.

        Args:
            streams: Dictionary of available streams from Strava
            requested_formats: List of formats user requested

        Returns:
            Tuple of (exportable_formats, skipped_formats_with_reasons)
            - exportable_formats: List of format strings that can be exported
            - skipped_formats_with_reasons: List of (format, reason) tuples

        Example:
            >>> streams = {"time": stream1, "heartrate": stream2}  # No GPS
            >>> exportable, skipped = StravaFileExporter.recommend_formats(
            ...     streams, ["gpx", "json", "hr_csv"]
            ... )
            >>> print(exportable)
            ['json', 'hr_csv']
            >>> print(skipped)
            [('gpx', 'No GPS data available')]
        """
        exportable = []
        skipped = []

        for fmt in requested_formats:
            if fmt == "gpx":
                if cls.has_gpx_support(streams):
                    exportable.append("gpx")
                else:
                    skipped.append(("gpx", "No GPS data available"))
            elif fmt == "json":
                exportable.append("json")  # JSON always works
            elif fmt == "hr_csv":
                if streams.get("heartrate"):
                    exportable.append("hr_csv")
                else:
                    skipped.append(("hr_csv", "No heart rate data available"))

        # Fallback: If nothing exportable, ensure JSON is included as
        # minimum viable export to capture all available data
        if not exportable:
            exportable.append("json")
            logger.info(
                "No requested formats available, falling back to JSON export"
            )

        return exportable, skipped

    @classmethod
    def export_to_gpx(  # pylint: disable=too-many-locals
        cls,
        activity: StravaActivityDetail,
        streams: dict[str, StravaStream],
        output_path: Path,
    ) -> None:
        """
        Export activity with GPS route to GPX format.

        Args:
            activity: Strava activity detail
            streams: Stream data (must include time, latlng)
            output_path: Path to save GPX file

        Raises:
            StravaConversionError: If required streams are missing
            StravaFileError: If file cannot be written

        Example:
            >>> activity = client.get_activity(12345678)
            >>> streams = client.get_activity_streams(12345678)
            >>> StravaFileExporter.export_to_gpx(
            ...     activity, streams, Path("data/strava/activities/run.gpx")
            ... )
        """
        from src.types.strava import StravaConversionError, StravaFileError

        # Validate required streams
        if "time" not in streams or "latlng" not in streams:
            raise StravaConversionError(
                "GPX export requires 'time' and 'latlng' streams"
            )

        time_stream = streams["time"]
        latlng_stream = streams["latlng"]
        altitude_stream = streams.get("altitude")
        hr_stream = streams.get("heartrate")

        # Create GPX XML structure
        gpx = ET.Element("gpx", {
            "version": "1.1",
            "creator": "Onsendo Strava Integration",
            "xmlns": "http://www.topografix.com/GPX/1/1",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": "http://www.topografix.com/GPX/1/1 "
            "http://www.topografix.com/GPX/1/1/gpx.xsd",
        })

        # Metadata
        metadata = ET.SubElement(gpx, "metadata")
        name_elem = ET.SubElement(metadata, "name")
        name_elem.text = activity.name
        time_elem = ET.SubElement(metadata, "time")
        time_elem.text = activity.start_date.isoformat() + "Z"

        # Track
        trk = ET.SubElement(gpx, "trk")
        trk_name = ET.SubElement(trk, "name")
        trk_name.text = activity.name
        trk_type = ET.SubElement(trk, "type")
        trk_type.text = activity.activity_type

        # Track segment
        trkseg = ET.SubElement(trk, "trkseg")

        # Add track points
        for i, time_offset in enumerate(time_stream.data):
            if i >= len(latlng_stream.data):
                break

            latlng = latlng_stream.data[i]
            if not latlng or len(latlng) < 2:
                continue

            lat, lon = latlng[0], latlng[1]
            trkpt = ET.SubElement(trkseg, "trkpt", {
                "lat": str(lat),
                "lon": str(lon),
            })

            # Elevation
            if altitude_stream and i < len(altitude_stream.data):
                ele = ET.SubElement(trkpt, "ele")
                ele.text = str(altitude_stream.data[i])

            # Timestamp
            timestamp = activity.start_date + timedelta(seconds=time_offset)
            time_pt = ET.SubElement(trkpt, "time")
            time_pt.text = timestamp.isoformat() + "Z"

            # Heart rate (GPX extension)
            if hr_stream and i < len(hr_stream.data):
                extensions = ET.SubElement(trkpt, "extensions")
                hr = ET.SubElement(extensions, "hr")
                hr.text = str(int(hr_stream.data[i]))

        # Write to file
        try:
            tree = ET.ElementTree(gpx)
            ET.indent(tree, space="  ")  # Pretty-print
            output_path.parent.mkdir(parents=True, exist_ok=True)
            tree.write(output_path, encoding="utf-8", xml_declaration=True)
            logger.info(f"Exported GPX file: {output_path}")
        except Exception as e:
            raise StravaFileError(f"Failed to write GPX file: {e}") from e

    @classmethod
    def export_to_json(
        cls,
        activity: StravaActivityDetail,
        streams: Optional[dict[str, StravaStream]],
        output_path: Path,
    ) -> None:
        """
        Export full activity + streams to JSON format.

        Args:
            activity: Strava activity detail
            streams: Optional stream data
            output_path: Path to save JSON file

        Raises:
            StravaFileError: If file cannot be written

        Example:
            >>> activity = client.get_activity(12345678)
            >>> streams = client.get_activity_streams(12345678)
            >>> StravaFileExporter.export_to_json(
            ...     activity, streams, Path("data/strava/activities/run.json")
            ... )
        """
        from src.types.strava import StravaFileError

        # Build JSON structure
        data = {
            "id": activity.id,
            "name": activity.name,
            "type": activity.activity_type,
            "sport_type": activity.sport_type,
            "start_date": activity.start_date.isoformat(),
            "start_date_local": activity.start_date_local.isoformat(),
            "timezone": activity.timezone,
            "distance_m": activity.distance_m,
            "moving_time_s": activity.moving_time_s,
            "elapsed_time_s": activity.elapsed_time_s,
            "total_elevation_gain_m": activity.total_elevation_gain_m,
            "calories": activity.calories,
            "has_heartrate": activity.has_heartrate,
            "average_heartrate": activity.average_heartrate,
            "max_heartrate": activity.max_heartrate,
            "start_latlng": activity.start_latlng,
            "end_latlng": activity.end_latlng,
            "average_speed": activity.average_speed,
            "max_speed": activity.max_speed,
            "average_cadence": activity.average_cadence,
            "average_watts": activity.average_watts,
            "average_temp": activity.average_temp,
            "description": activity.description,
            "gear_id": activity.gear_id,
        }

        # Add streams if available
        if streams:
            data["streams"] = {}
            for stream_type, stream in streams.items():
                data["streams"][stream_type] = {
                    "data": stream.data,
                    "original_size": stream.original_size,
                    "resolution": stream.resolution,
                }

        # Write to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Exported JSON file: {output_path}")
        except Exception as e:
            raise StravaFileError(f"Failed to write JSON file: {e}") from e

    @classmethod
    def export_hr_to_csv(
        cls,
        activity: StravaActivityDetail,
        hr_stream: StravaStream,
        time_stream: Optional[StravaStream],
        output_path: Path,
    ) -> None:
        """
        Export heart rate data to CSV format.

        Args:
            activity: Strava activity detail
            hr_stream: Heart rate stream
            time_stream: Optional time stream for timestamps
            output_path: Path to save CSV file

        Raises:
            StravaConversionError: If HR stream is empty
            StravaFileError: If file cannot be written

        Example:
            >>> activity = client.get_activity(12345678)
            >>> streams = client.get_activity_streams(12345678, ["heartrate", "time"])
            >>> StravaFileExporter.export_hr_to_csv(
            ...     activity,
            ...     streams["heartrate"],
            ...     streams.get("time"),
            ...     Path("data/strava/activities/run_hr.csv")
            ... )
        """
        from src.types.strava import StravaConversionError, StravaFileError

        if not hr_stream or not hr_stream.data:
            raise StravaConversionError("Heart rate stream is empty")

        # Build CSV rows
        rows = []
        for i, hr_value in enumerate(hr_stream.data):
            # Calculate timestamp
            if time_stream and i < len(time_stream.data):
                time_offset = time_stream.data[i]
                timestamp = activity.start_date_local + timedelta(seconds=time_offset)
            else:
                # Estimate based on index
                timestamp = activity.start_date_local + timedelta(seconds=i)

            rows.append({
                "timestamp": timestamp.isoformat(),
                "heart_rate": int(hr_value),
            })

        # Write to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                import csv

                writer = csv.DictWriter(f, fieldnames=["timestamp", "heart_rate"])
                writer.writeheader()
                writer.writerows(rows)
            logger.info(f"Exported HR CSV file: {output_path}")
        except Exception as e:
            raise StravaFileError(f"Failed to write CSV file: {e}") from e
