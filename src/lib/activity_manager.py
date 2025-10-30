"""
Unified activity management system for Strava-sourced activities.

This module replaces the separate heart rate and exercise management systems
with a single unified approach where all activities come from Strava.

Activities are automatically classified by type (including "onsen_monitoring")
and can be linked to onsen visits for heart rate analysis.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from loguru import logger

from src.db.models import Activity as ActivityModel, OnsenVisit
from src.types.exercise import ExerciseType


@dataclass
class ActivityData:
    """
    Data class for activity information before database storage.

    This class has many attributes to comprehensively represent
    activity data from Strava.

    Attributes:
        strava_id: Strava activity ID (unique identifier)
        start_time: Activity start timestamp
        end_time: Activity end timestamp
        activity_type: Type of activity (running, cycling, etc.)
        activity_name: Name/title of the activity
        workout_type: Strava workout type classification
        distance_km: Total distance covered in kilometers
        calories_burned: Estimated calories burned
        elevation_gain_m: Total elevation gain in meters
        avg_heart_rate: Average heart rate during activity
        min_heart_rate: Minimum heart rate recorded
        max_heart_rate: Maximum heart rate recorded
        indoor_outdoor: Location type (indoor/outdoor/unknown)
        weather_conditions: Weather description (e.g., "15°C")
        route_data: Time-series GPS and physiological data as list of dictionaries.
            Each point contains:
            - timestamp (str): ISO 8601 timestamp
            - lat (float, optional): Latitude coordinate
            - lon (float, optional): Longitude coordinate
            - elevation (float, optional): Elevation in meters
            - hr (int, optional): Heart rate in beats per minute
            - speed_mps (float, optional): Speed in meters per second
            Example:
                [
                    {
                        "timestamp": "2025-10-30T10:00:00",
                        "lat": 33.279, "lon": 131.500,
                        "elevation": 50.0, "hr": 120, "speed_mps": 3.5
                    },
                    ...
                ]
        notes: Optional activity notes/description
        strava_data_hash: SHA-256 hash for sync detection
    """

    # pylint: disable=too-many-instance-attributes

    strava_id: str
    start_time: datetime
    end_time: datetime
    activity_type: str
    activity_name: str
    workout_type: Optional[str] = None
    distance_km: Optional[float] = None
    calories_burned: Optional[int] = None
    elevation_gain_m: Optional[float] = None
    avg_heart_rate: Optional[float] = None
    min_heart_rate: Optional[float] = None
    max_heart_rate: Optional[float] = None
    indoor_outdoor: Optional[str] = None
    weather_conditions: Optional[str] = None
    route_data: Optional[list[dict]] = None
    notes: Optional[str] = None
    strava_data_hash: str = None

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def route_data_json(self) -> Optional[str]:
        """Serialize route data to JSON string for database storage."""
        if not self.route_data:
            return None
        return json.dumps(self.route_data)


@dataclass
class ActivitySummary:
    """Weekly or monthly aggregated activity statistics."""

    total_activities: int
    total_duration_minutes: int
    total_distance_km: float
    total_elevation_gain_m: float
    total_calories: int
    avg_heart_rate: Optional[float]
    activities_by_type: dict[str, int]
    onsen_monitoring_count: int
    linked_visit_count: int


class ActivityManager:
    """Manages all Strava-sourced activities in the database."""

    def __init__(self, db_session: Session):
        """
        Initialize the activity manager.

        Args:
            db_session: SQLAlchemy database session
        """
        if db_session is None:
            raise ValueError("db_session is required")
        self.db_session = db_session

    def store_activity(
        self,
        activity: ActivityData,
        visit_id: Optional[int] = None,
    ) -> ActivityModel:
        """
        Store a Strava activity in the database.

        Args:
            activity: ActivityData object with activity details
            visit_id: Optional visit ID to link to (only for onsen monitoring activities)

        Returns:
            ActivityModel: The stored activity model

        Raises:
            ValueError: If visit_id is provided for non-onsen-monitoring activity
            ValueError: If activity with this strava_id already exists
        """
        # Validate visit_id only for onsen monitoring activities
        is_onsen = activity.activity_type == ExerciseType.ONSEN_MONITORING.value
        if visit_id is not None and not is_onsen:
            raise ValueError("visit_id can only be set for onsen monitoring activities")

        # Check for duplicates
        existing = self.get_by_strava_id(activity.strava_id)
        if existing:
            raise ValueError(
                f"Activity with strava_id {activity.strava_id} already exists (ID: {existing.id})"
            )

        # Create database model
        activity_model = ActivityModel(
            strava_id=activity.strava_id,
            visit_id=visit_id,
            recording_start=activity.start_time,
            recording_end=activity.end_time,
            duration_minutes=activity.duration_minutes,
            activity_type=activity.activity_type,
            activity_name=activity.activity_name,
            workout_type=activity.workout_type,
            distance_km=activity.distance_km,
            calories_burned=activity.calories_burned,
            elevation_gain_m=activity.elevation_gain_m,
            avg_heart_rate=activity.avg_heart_rate,
            min_heart_rate=activity.min_heart_rate,
            max_heart_rate=activity.max_heart_rate,
            indoor_outdoor=activity.indoor_outdoor,
            weather_conditions=activity.weather_conditions,
            route_data=activity.route_data_json,
            strava_data_hash=activity.strava_data_hash,
            last_synced_at=datetime.utcnow(),
            notes=activity.notes,
        )

        try:
            self.db_session.add(activity_model)
            self.db_session.commit()
            self.db_session.refresh(activity_model)
            logger.info(
                f"Stored activity {activity.strava_id} (ID: {activity_model.id}, "
                f"Type: {activity.activity_type})"
            )
            return activity_model
        except Exception as e:
            logger.error(f"Error storing activity: {e}")
            self.db_session.rollback()
            raise

    def link_to_visit(self, activity_id: int, visit_id: int) -> bool:
        """
        Link an onsen monitoring activity to a visit.

        Args:
            activity_id: Database ID of the activity
            visit_id: Database ID of the visit

        Returns:
            bool: True if successful, False otherwise
        """
        activity = self.get_by_id(activity_id)
        if not activity:
            logger.error(f"Activity with ID {activity_id} not found")
            return False

        # Check if activity is onsen monitoring type
        if activity.activity_type != ExerciseType.ONSEN_MONITORING.value:
            logger.error(
                f"Cannot link activity {activity_id} to visit: "
                f"activity type is '{activity.activity_type}', not 'onsen_monitoring'"
            )
            return False

        # Verify visit exists
        visit = (
            self.db_session.query(OnsenVisit).filter(OnsenVisit.id == visit_id).first()
        )
        if not visit:
            logger.error(f"Visit with ID {visit_id} not found")
            return False

        try:
            activity.visit_id = visit_id
            self.db_session.commit()
            logger.info(f"Linked activity {activity_id} to visit {visit_id}")
            return True
        except Exception as e:
            logger.error(f"Error linking activity to visit: {e}")
            self.db_session.rollback()
            return False

    def unlink_from_visit(self, activity_id: int) -> bool:
        """
        Unlink an activity from its visit.

        Args:
            activity_id: Database ID of the activity

        Returns:
            bool: True if successful, False otherwise
        """
        activity = self.get_by_id(activity_id)
        if not activity:
            logger.error(f"Activity with ID {activity_id} not found")
            return False

        try:
            activity.visit_id = None
            self.db_session.commit()
            logger.info(f"Unlinked activity {activity_id} from visit")
            return True
        except Exception as e:
            logger.error(f"Error unlinking activity from visit: {e}")
            self.db_session.rollback()
            return False

    def get_by_id(self, activity_id: int) -> Optional[ActivityModel]:
        """Get activity by database ID."""
        return (
            self.db_session.query(ActivityModel)
            .filter(ActivityModel.id == activity_id)
            .first()
        )

    def get_by_strava_id(self, strava_id: str) -> Optional[ActivityModel]:
        """Get activity by Strava ID."""
        return (
            self.db_session.query(ActivityModel)
            .filter(ActivityModel.strava_id == strava_id)
            .first()
        )

    def get_by_visit(self, visit_id: int) -> list[ActivityModel]:
        """Get all activities linked to a specific visit."""
        return (
            self.db_session.query(ActivityModel)
            .filter(ActivityModel.visit_id == visit_id)
            .order_by(ActivityModel.recording_start)
            .all()
        )

    def get_unlinked(self) -> list[ActivityModel]:
        """
        Get all activities that are not linked to visits.

        This includes both:
        - Activities not tagged as onsen monitoring
        - Onsen monitoring activities without a visit link
        """
        return (
            self.db_session.query(ActivityModel)
            .filter(ActivityModel.visit_id.is_(None))
            .order_by(ActivityModel.recording_start.desc())
            .all()
        )

    def get_onsen_monitoring_activities(self) -> list[ActivityModel]:
        """Get all activities with type onsen_monitoring."""
        return (
            self.db_session.query(ActivityModel)
            .filter(ActivityModel.activity_type == ExerciseType.ONSEN_MONITORING.value)
            .order_by(ActivityModel.recording_start.desc())
            .all()
        )

    def get_by_type(
        self, activity_type: str, date_range: Optional[tuple[datetime, datetime]] = None
    ) -> list[ActivityModel]:
        """
        Get activities filtered by type and optional date range.

        Args:
            activity_type: Activity type (running, cycling, etc.)
            date_range: Optional tuple of (start_date, end_date)

        Returns:
            List of activities matching the criteria
        """
        query = self.db_session.query(ActivityModel).filter(
            ActivityModel.activity_type == activity_type
        )

        if date_range:
            start_date, end_date = date_range
            query = query.filter(
                ActivityModel.recording_start >= start_date,
                ActivityModel.recording_start <= end_date,
            )

        return query.order_by(ActivityModel.recording_start.desc()).all()

    def get_weekly_summary(
        self, week_start: datetime, week_end: datetime
    ) -> ActivitySummary:
        """
        Get aggregated activity statistics for a week (for rule revisions).

        Args:
            week_start: Start of the week (inclusive)
            week_end: End of the week (inclusive)

        Returns:
            ActivitySummary with aggregated statistics
        """
        activities = (
            self.db_session.query(ActivityModel)
            .filter(
                ActivityModel.recording_start >= week_start,
                ActivityModel.recording_start <= week_end,
            )
            .all()
        )

        # Aggregate statistics
        total_activities = len(activities)
        total_duration = sum(a.duration_minutes for a in activities)
        total_distance = sum(a.distance_km or 0 for a in activities)
        total_elevation = sum(a.elevation_gain_m or 0 for a in activities)
        total_calories = sum(a.calories_burned or 0 for a in activities)

        # Average heart rate (only for activities with HR data)
        hr_activities = [a for a in activities if a.avg_heart_rate is not None]
        avg_hr = (
            sum(a.avg_heart_rate for a in hr_activities) / len(hr_activities)
            if hr_activities
            else None
        )

        # Activities by type
        activities_by_type = {}
        for activity in activities:
            activities_by_type[activity.activity_type] = (
                activities_by_type.get(activity.activity_type, 0) + 1
            )

        # Onsen monitoring counts
        onsen_monitoring = [
            a for a in activities
            if a.activity_type == ExerciseType.ONSEN_MONITORING.value
        ]
        linked_visits = [a for a in activities if a.visit_id is not None]

        return ActivitySummary(
            total_activities=total_activities,
            total_duration_minutes=total_duration,
            total_distance_km=total_distance,
            total_elevation_gain_m=total_elevation,
            total_calories=total_calories,
            avg_heart_rate=avg_hr,
            activities_by_type=activities_by_type,
            onsen_monitoring_count=len(onsen_monitoring),
            linked_visit_count=len(linked_visits),
        )

    def delete_activity(self, activity_id: int) -> bool:
        """
        Delete an activity from the database.

        Args:
            activity_id: Database ID of the activity

        Returns:
            bool: True if successful, False otherwise
        """
        activity = self.get_by_id(activity_id)
        if not activity:
            logger.error(f"Activity with ID {activity_id} not found")
            return False

        try:
            self.db_session.delete(activity)
            self.db_session.commit()
            logger.info(
                f"Deleted activity {activity_id} (Strava: {activity.strava_id})"
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting activity: {e}")
            self.db_session.rollback()
            return False

    def suggest_visit_links(
        self, activity_id: int, time_window_hours: int = 2
    ) -> list[tuple[int, str, int]]:
        """
        Suggest potential onsen visits to link based on timestamps.

        Searches for visits within a time window of the activity end time.

        Args:
            activity_id: Database ID of the activity
            time_window_hours: Hours before/after activity end to search (default: 2)

        Returns:
            List of tuples: (visit_id, description, minutes_difference)
            Sorted by time proximity
        """
        activity = self.get_by_id(activity_id)
        if not activity:
            logger.error(f"Activity with ID {activity_id} not found")
            return []

        # Search for visits within time window
        time_window = timedelta(hours=time_window_hours)
        search_start = activity.recording_end - time_window
        search_end = activity.recording_end + time_window

        nearby_visits = (
            self.db_session.query(OnsenVisit)
            .filter(
                OnsenVisit.visit_time >= search_start,
                OnsenVisit.visit_time <= search_end,
            )
            .all()
        )

        # Build suggestions with time differences
        suggestions = []
        for visit in nearby_visits:
            time_diff = abs(
                (visit.visit_time - activity.recording_end).total_seconds() / 60
            )
            # Get onsen name from relationship
            onsen_name = visit.onsen.name if visit.onsen else "Unknown"
            description = (
                f"Visit at {visit.visit_time.strftime('%Y-%m-%d %H:%M')} "
                f"to {onsen_name}"
            )
            suggestions.append((visit.id, description, int(time_diff)))

        # Sort by time proximity
        suggestions.sort(key=lambda x: x[2])
        return suggestions

    def calculate_data_hash(self, strava_data: dict) -> str:
        """
        Calculate SHA-256 hash of Strava activity data for sync detection.

        Args:
            strava_data: Dictionary of Strava activity data

        Returns:
            Hexadecimal hash string
        """
        # Convert to JSON string and hash
        json_str = json.dumps(strava_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
