"""
Strava data conversion utilities.

This module provides converters for transforming Strava API data into
Onsendo-compatible Activity format and standard file formats (GPX, JSON, CSV).
"""

import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Mapping, Optional

from loguru import logger

from src.lib.activity_manager import ActivityData
from src.lib.route_data_analyzer import should_classify_as_onsen_monitoring
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


class StravaToActivityConverter:
    """Converts Strava activities to ActivityData objects for the unified activity system."""

    # Timezone fix for specific onsen monitoring activities
    # These activities were recorded in European timezone (UTC+1) instead of JST (UTC+9)
    # Requires +8 hour correction to align with JST
    TIMEZONE_FIX_STRAVA_IDS = {
        16260033512,  # Onsendo 1/88 - Yamada onsen
        16267464501,  # Onsendo 2/88 - Suehiro onsen
        16267965840,  # Onsendo 3/88 - Teruyu onsen
        16276842757,  # Onsendo 4/88 - Yamato onsen
        16278276762,  # Onsendo 5/88 - Takegawara onsen
        16291745250,  # Onsendo 6/88 - Yahata onsen
        16291744853,  # Onsendo 7/88 - Higashihasuda onsen
        16298077670,  # Onsendo 8/88 - Matsubara onsen
        16298797489,  # Onsendo 9/88 - Ebisuya onsen
        16308540420,  # Onsendo 10/88 - Tenman onsen
        16309449316,  # Onsendo 11/88 - Kasuga onsen
        16338045104,  # Onsendo 12/88 - Kinei onsen
        16339447496,  # Onsendo 13/88 - Sunline Beppu
    }
    TIMEZONE_FIX_OFFSET = timedelta(hours=8)

    @classmethod
    def _needs_timezone_fix(cls, strava_id: int) -> bool:
        """
        Check if activity requires timezone correction.

        Args:
            strava_id: Strava activity ID

        Returns:
            True if activity needs +8 hour timezone correction
        """
        return strava_id in cls.TIMEZONE_FIX_STRAVA_IDS

    @classmethod
    def convert(
        cls,
        activity: StravaActivityDetail,
        streams: Optional[dict[str, StravaStream]] = None,
    ) -> ActivityData:
        """
        Convert Strava activity to ActivityData for unified activity system.

        Automatically detects onsen monitoring activities based on:
        - Activity name contains "onsendo" (case-insensitive) AND "88"
        - Route data shows stationary HR monitoring (no movement, has HR)

        Args:
            activity: Strava activity detail
            streams: Optional stream data (GPS, HR, etc.)

        Returns:
            ActivityData object ready for ActivityManager storage

        Example:
            >>> activity = client.get_activity(12345678)
            >>> streams = client.get_activity_streams(12345678)
            >>> activity_data = StravaToActivityConverter.convert(activity, streams)
            >>> manager.store_activity(activity_data)
        """
        # Check if this activity needs timezone correction
        needs_tz_fix = cls._needs_timezone_fix(activity.id)
        tz_offset = cls.TIMEZONE_FIX_OFFSET if needs_tz_fix else timedelta(0)

        if needs_tz_fix:
            logger.info(
                f"Applying timezone fix (+8 hours) to activity {activity.id} "
                f"({activity.name})"
            )

        # Map activity type (initial mapping from Strava type)
        exercise_type = StravaActivityTypeMapper.map_type(activity.activity_type)

        # Determine indoor/outdoor
        indoor_outdoor = None
        if "Virtual" in activity.activity_type or "Indoor" in activity.activity_type:
            indoor_outdoor = "indoor"
        elif activity.start_latlng or (streams and "latlng" in streams):
            indoor_outdoor = "outdoor"
        else:
            indoor_outdoor = "unknown"

        # Build route data from streams
        route_data = None
        route_data_json = None
        if streams:
            route_data = cls._build_route_data(streams, activity.start_date, tz_offset)
            # Convert to JSON string for analysis
            if route_data:
                route_data_json = json.dumps(route_data)

        # Auto-detect onsen monitoring activities
        detection_reason = None
        should_classify, reason = should_classify_as_onsen_monitoring(
            activity.name, route_data_json
        )
        if should_classify:
            exercise_type = ExerciseType.ONSEN_MONITORING
            detection_reason = reason
            logger.info(
                f"Auto-detected onsen monitoring activity: '{activity.name}' "
                f"(reason: {reason})"
            )

        # Calculate elevation gain if not provided
        elevation_gain_m = activity.total_elevation_gain_m
        if elevation_gain_m is None and streams and "altitude" in streams:
            elevation_gain_m = cls._calculate_elevation_gain(streams["altitude"])

        # Calculate min heart rate from streams if available
        min_heart_rate = None
        if streams and "heartrate" in streams:
            hr_data = streams["heartrate"].data
            if hr_data:
                min_heart_rate = float(min(hr_data))

        # Calculate data hash for sync detection
        activity_dict = {
            "id": activity.id,
            "name": activity.name,
            "type": activity.activity_type,
            "start_date": activity.start_date.isoformat(),
            "distance_m": activity.distance_m,
            "elapsed_time_s": activity.elapsed_time_s,
            "moving_time_s": activity.moving_time_s,
        }
        data_hash = hashlib.sha256(
            json.dumps(activity_dict, sort_keys=True).encode()
        ).hexdigest()

        return ActivityData(
            strava_id=str(activity.id),
            start_time=activity.start_date_local + tz_offset,
            end_time=activity.start_date_local
            + timedelta(seconds=activity.elapsed_time_s)
            + tz_offset,
            activity_type=exercise_type.value,
            activity_name=activity.name,
            workout_type=activity.sport_type,
            distance_km=activity.distance_km,
            calories_burned=activity.calories,
            elevation_gain_m=elevation_gain_m,
            avg_heart_rate=activity.average_heartrate,
            min_heart_rate=min_heart_rate,
            max_heart_rate=activity.max_heartrate,
            indoor_outdoor=indoor_outdoor,
            weather_conditions=(
                f"{activity.average_temp}°C" if activity.average_temp else None
            ),
            route_data=route_data,
            notes=activity.description,
            strava_data_hash=data_hash,
        )

    @classmethod
    def _build_route_data(
        cls,
        streams: dict[str, StravaStream],
        start_time: datetime,
        tz_offset: timedelta = timedelta(0),
    ) -> list[dict]:
        """
        Build route data from Strava streams.

        Args:
            streams: Dictionary of stream data
            start_time: Activity start time
            tz_offset: Optional timezone offset to apply to all timestamps

        Returns:
            List of route point dictionaries
        """
        # Get time series for synchronization
        time_stream = streams.get("time")
        if not time_stream:
            return []

        route_points = []
        for i, timestamp_offset in enumerate(time_stream.data):
            point_time = start_time + timedelta(seconds=timestamp_offset) + tz_offset
            point_data = {"timestamp": point_time.isoformat()}

            # Add GPS coordinates if available
            if "latlng" in streams and i < len(streams["latlng"].data):
                lat, lng = streams["latlng"].data[i]
                point_data["lat"] = lat
                point_data["lon"] = lng

            # Add elevation if available
            if "altitude" in streams and i < len(streams["altitude"].data):
                point_data["elevation"] = streams["altitude"].data[i]

            # Add heart rate if available
            if "heartrate" in streams and i < len(streams["heartrate"].data):
                point_data["hr"] = streams["heartrate"].data[i]

            # Add speed if available
            if "velocity_smooth" in streams and i < len(
                streams["velocity_smooth"].data
            ):
                point_data["speed_mps"] = streams["velocity_smooth"].data[i]

            route_points.append(point_data)

        return route_points

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
        prev_altitude = altitude_stream.data[0]

        for altitude in altitude_stream.data[1:]:
            if altitude > prev_altitude:
                elevation_gain += altitude - prev_altitude
            prev_altitude = altitude

        return elevation_gain


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
            logger.info("No requested formats available, falling back to JSON export")

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
        gpx = ET.Element(
            "gpx",
            {
                "version": "1.1",
                "creator": "Onsendo Strava Integration",
                "xmlns": "http://www.topografix.com/GPX/1/1",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xsi:schemaLocation": "http://www.topografix.com/GPX/1/1 "
                "http://www.topografix.com/GPX/1/1/gpx.xsd",
            },
        )

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
            trkpt = ET.SubElement(
                trkseg,
                "trkpt",
                {
                    "lat": str(lat),
                    "lon": str(lon),
                },
            )

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

            rows.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "heart_rate": int(hr_value),
                }
            )

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
