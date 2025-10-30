"""
Integration tests for Activity heart rate time-series storage and retrieval.
"""

import json
from datetime import datetime, timezone

import pytest

from src.db.conn import get_db
from src.db.models import Activity
from src.lib.activity_manager import ActivityManager, ActivityData
from src.config import get_database_url


@pytest.mark.integration
class TestActivityHRStorage:
    """Test Activity HR time-series database operations."""

    def test_store_activity_with_hr_timeseries(self):
        """Test storing Activity with HR time-series to database."""
        with get_db(url=get_database_url()) as db:
            manager = ActivityManager(db)

            # Create activity data with HR time-series in route_data
            activity_data = ActivityData(
                strava_id="test_hr_12345",
                start_time=datetime(2025, 10, 30, 10, 0, 0),
                end_time=datetime(2025, 10, 30, 10, 30, 0),
                activity_type="running",
                activity_name="Test Morning Run with HR",
                distance_km=5.0,
                elevation_gain_m=50.0,
                avg_heart_rate=145.0,
                min_heart_rate=120.0,
                max_heart_rate=165.0,
                route_data=[
                    {
                        "timestamp": "2025-10-30T10:00:00",
                        "lat": 33.279,
                        "lon": 131.500,
                        "elevation": 10.0,
                        "hr": 120,
                        "speed_mps": 3.0,
                    },
                    {
                        "timestamp": "2025-10-30T10:05:00",
                        "lat": 33.280,
                        "lon": 131.501,
                        "elevation": 20.0,
                        "hr": 135,
                        "speed_mps": 3.2,
                    },
                    {
                        "timestamp": "2025-10-30T10:10:00",
                        "lat": 33.281,
                        "lon": 131.502,
                        "elevation": 30.0,
                        "hr": 145,
                        "speed_mps": 3.5,
                    },
                    {
                        "timestamp": "2025-10-30T10:15:00",
                        "lat": 33.282,
                        "lon": 131.503,
                        "elevation": 40.0,
                        "hr": 155,
                        "speed_mps": 3.8,
                    },
                ],
                strava_data_hash="test_hash_123",
            )

            # Store activity
            stored = manager.store_activity(activity_data)

            # Verify storage
            assert stored.id is not None
            assert stored.strava_id == "test_hr_12345"
            assert stored.route_data is not None

            # Verify HR data in route_data JSON
            route_data = json.loads(stored.route_data)
            assert len(route_data) == 4
            assert route_data[0]["hr"] == 120
            assert route_data[1]["hr"] == 135
            assert route_data[2]["hr"] == 145
            assert route_data[3]["hr"] == 155

            # Cleanup
            db.delete(stored)
            db.commit()

    def test_retrieve_activity_hr_timeseries(self):
        """Test retrieving and parsing HR time-series from stored activity."""
        with get_db(url=get_database_url()) as db:
            manager = ActivityManager(db)

            # Create and store activity
            activity_data = ActivityData(
                strava_id="test_hr_retrieve_67890",
                start_time=datetime(2025, 10, 30, 15, 0, 0),
                end_time=datetime(2025, 10, 30, 15, 45, 0),
                activity_type="cycling",
                activity_name="Test Bike Ride with HR",
                distance_km=20.0,
                avg_heart_rate=130.0,
                route_data=[
                    {"timestamp": "2025-10-30T15:00:00", "hr": 110},
                    {"timestamp": "2025-10-30T15:15:00", "hr": 125},
                    {"timestamp": "2025-10-30T15:30:00", "hr": 140},
                    {"timestamp": "2025-10-30T15:45:00", "hr": 135},
                ],
                strava_data_hash="test_hash_456",
            )

            stored = manager.store_activity(activity_data)

            # Retrieve activity
            retrieved = manager.get_by_strava_id("test_hr_retrieve_67890")
            assert retrieved is not None

            # Parse and verify HR time-series
            route_data = json.loads(retrieved.route_data)
            hr_values = [point["hr"] for point in route_data]
            timestamps = [point["timestamp"] for point in route_data]

            assert len(hr_values) == 4
            assert hr_values == [110, 125, 140, 135]
            assert len(timestamps) == 4

            # Verify summary statistics
            assert retrieved.avg_heart_rate == 130.0

            # Cleanup
            db.delete(stored)
            db.commit()

    def test_store_activity_without_hr_data(self):
        """Test storing activity without HR data (should work gracefully)."""
        with get_db(url=get_database_url()) as db:
            manager = ActivityManager(db)

            # Create activity without HR
            activity_data = ActivityData(
                strava_id="test_no_hr_11111",
                start_time=datetime(2025, 10, 30, 8, 0, 0),
                end_time=datetime(2025, 10, 30, 8, 30, 0),
                activity_type="yoga",
                activity_name="Morning Yoga (No HR)",
                route_data=[
                    {"timestamp": "2025-10-30T08:00:00"},
                    {"timestamp": "2025-10-30T08:15:00"},
                    {"timestamp": "2025-10-30T08:30:00"},
                ],
                strava_data_hash="test_hash_789",
            )

            stored = manager.store_activity(activity_data)

            # Verify storage without HR
            assert stored.id is not None
            assert stored.avg_heart_rate is None

            # Verify route data exists but has no HR
            route_data = json.loads(stored.route_data)
            for point in route_data:
                assert "hr" not in point

            # Cleanup
            db.delete(stored)
            db.commit()

    def test_store_activity_with_partial_hr_data(self):
        """Test storing activity where only some points have HR data."""
        with get_db(url=get_database_url()) as db:
            manager = ActivityManager(db)

            # Create activity with partial HR
            activity_data = ActivityData(
                strava_id="test_partial_hr_22222",
                start_time=datetime(2025, 10, 30, 12, 0, 0),
                end_time=datetime(2025, 10, 30, 12, 20, 0),
                activity_type="running",
                activity_name="Run with Partial HR Data",
                avg_heart_rate=140.0,
                route_data=[
                    {"timestamp": "2025-10-30T12:00:00", "hr": 130},
                    {"timestamp": "2025-10-30T12:05:00", "hr": 145},
                    {"timestamp": "2025-10-30T12:10:00"},  # Missing HR
                    {"timestamp": "2025-10-30T12:15:00", "hr": 150},
                    {"timestamp": "2025-10-30T12:20:00"},  # Missing HR
                ],
                strava_data_hash="test_hash_partial",
            )

            stored = manager.store_activity(activity_data)

            # Verify partial HR storage
            route_data = json.loads(stored.route_data)
            assert len(route_data) == 5

            # Check which points have HR
            assert "hr" in route_data[0] and route_data[0]["hr"] == 130
            assert "hr" in route_data[1] and route_data[1]["hr"] == 145
            assert "hr" not in route_data[2]
            assert "hr" in route_data[3] and route_data[3]["hr"] == 150
            assert "hr" not in route_data[4]

            # Cleanup
            db.delete(stored)
            db.commit()

    def test_activity_hr_timeseries_with_indoor_activity(self):
        """Test HR time-series for indoor activity (HR but no GPS)."""
        with get_db(url=get_database_url()) as db:
            manager = ActivityManager(db)

            # Create indoor activity with HR only
            activity_data = ActivityData(
                strava_id="test_indoor_hr_33333",
                start_time=datetime(2025, 10, 30, 18, 0, 0),
                end_time=datetime(2025, 10, 30, 19, 0, 0),
                activity_type="gym",
                activity_name="Indoor Workout with HR",
                indoor_outdoor="indoor",
                avg_heart_rate=125.0,
                route_data=[
                    {"timestamp": "2025-10-30T18:00:00", "hr": 100},
                    {"timestamp": "2025-10-30T18:15:00", "hr": 120},
                    {"timestamp": "2025-10-30T18:30:00", "hr": 140},
                    {"timestamp": "2025-10-30T18:45:00", "hr": 130},
                    {"timestamp": "2025-10-30T19:00:00", "hr": 110},
                ],
                strava_data_hash="test_hash_indoor",
            )

            stored = manager.store_activity(activity_data)

            # Verify HR-only data (no GPS)
            route_data = json.loads(stored.route_data)
            assert len(route_data) == 5

            for point in route_data:
                assert "hr" in point
                assert "lat" not in point
                assert "lon" not in point

            # Verify HR values
            hr_values = [point["hr"] for point in route_data]
            assert hr_values == [100, 120, 140, 130, 110]

            # Cleanup
            db.delete(stored)
            db.commit()

    def test_query_activities_by_hr_availability(self):
        """Test querying activities based on HR data availability."""
        with get_db(url=get_database_url()) as db:
            manager = ActivityManager(db)

            # Create activities with and without HR
            activity_with_hr = ActivityData(
                strava_id="test_query_hr_44444",
                start_time=datetime(2025, 10, 30, 10, 0, 0),
                end_time=datetime(2025, 10, 30, 10, 30, 0),
                activity_type="running",
                activity_name="Run with HR",
                avg_heart_rate=140.0,
                route_data=[{"timestamp": "2025-10-30T10:00:00", "hr": 140}],
                strava_data_hash="test_hash_with_hr",
            )

            activity_without_hr = ActivityData(
                strava_id="test_query_no_hr_55555",
                start_time=datetime(2025, 10, 30, 11, 0, 0),
                end_time=datetime(2025, 10, 30, 11, 30, 0),
                activity_type="walking",
                activity_name="Walk without HR",
                route_data=[{"timestamp": "2025-10-30T11:00:00"}],
                strava_data_hash="test_hash_no_hr",
            )

            stored_with_hr = manager.store_activity(activity_with_hr)
            stored_without_hr = manager.store_activity(activity_without_hr)

            # Query activities with HR data
            activities_with_hr = (
                db.query(Activity)
                .filter(Activity.avg_heart_rate.isnot(None))
                .filter(Activity.strava_id.in_(["test_query_hr_44444", "test_query_no_hr_55555"]))
                .all()
            )

            assert len(activities_with_hr) == 1
            assert activities_with_hr[0].strava_id == "test_query_hr_44444"

            # Cleanup
            db.delete(stored_with_hr)
            db.delete(stored_without_hr)
            db.commit()

    def test_large_hr_timeseries_storage(self):
        """Test storing activity with large HR time-series (realistic workout size)."""
        with get_db(url=get_database_url()) as db:
            manager = ActivityManager(db)

            # Simulate 30-minute workout with 1 sample per 5 seconds = 360 points
            route_data = []
            start_hr = 120
            for i in range(360):
                # Simulate varying HR (120-160 bpm)
                hr = start_hr + (i % 40)
                timestamp_offset = i * 5  # 5 seconds apart
                route_data.append({
                    "timestamp": f"2025-10-30T14:00:{timestamp_offset % 60:02d}",
                    "hr": hr,
                })

            activity_data = ActivityData(
                strava_id="test_large_hr_66666",
                start_time=datetime(2025, 10, 30, 14, 0, 0),
                end_time=datetime(2025, 10, 30, 14, 30, 0),
                activity_type="running",
                activity_name="Long Run with Dense HR Data",
                avg_heart_rate=140.0,
                route_data=route_data,
                strava_data_hash="test_hash_large",
            )

            stored = manager.store_activity(activity_data)

            # Verify large dataset storage
            assert stored.id is not None
            parsed_route = json.loads(stored.route_data)
            assert len(parsed_route) == 360

            # Spot check HR values
            assert parsed_route[0]["hr"] == 120
            assert parsed_route[100]["hr"] == start_hr + 100 % 40

            # Cleanup
            db.delete(stored)
            db.commit()
