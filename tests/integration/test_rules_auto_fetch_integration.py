"""
Integration tests for rule revision auto-fetch functionality.

These tests interact with the actual database and are marked with @pytest.mark.integration.
"""

from datetime import datetime, timedelta

import pytest

from src.cli.commands.rules.revision_create import auto_fetch_week_statistics
from src.db.conn import get_db
from src.db.models import OnsenVisit, ExerciseSession, Onsen
from src.const import CONST
from src.types.exercise import ExerciseType, DataSource


@pytest.mark.integration
class TestAutoFetchWeekStatisticsIntegration:
    """Integration tests for auto_fetch_week_statistics function."""

    def test_auto_fetch_with_empty_database_range(self):
        """Test auto-fetch with a date range that has no data."""
        # Use a date range far in the past to ensure no data exists
        week_start = "2020-01-01"
        week_end = "2020-01-07"

        metrics = auto_fetch_week_statistics(week_start, week_end, database_url=CONST.DATABASE_URL)

        assert metrics is not None
        assert metrics.onsen_visits_count == 0
        assert metrics.sauna_sessions_count == 0
        assert metrics.total_soaking_hours is None
        assert metrics.running_distance_km is None
        assert metrics.gym_sessions_count is None
        assert metrics.long_exercise_completed is False
        assert metrics.rest_days_count is None

    def test_auto_fetch_with_test_data(self):
        """Test auto-fetch with comprehensive test data, then clean up."""
        week_start_dt = datetime.now() - timedelta(days=7)
        week_end_dt = datetime.now()
        week_start = week_start_dt.strftime("%Y-%m-%d")
        week_end = week_end_dt.strftime("%Y-%m-%d")

        with get_db(url=CONST.DATABASE_URL) as db:
            # Find or create a test onsen
            test_onsen = db.query(Onsen).first()
            if not test_onsen:
                pytest.skip("No onsens in database - cannot test without onsen data")

            # Create test visits
            visit1 = OnsenVisit(
                onsen_id=test_onsen.id,
                visit_time=week_start_dt + timedelta(days=1),
                stay_length_minutes=60,
                sauna_visited=True,
            )
            visit2 = OnsenVisit(
                onsen_id=test_onsen.id,
                visit_time=week_start_dt + timedelta(days=3),
                stay_length_minutes=45,
                sauna_visited=False,
            )
            visit3 = OnsenVisit(
                onsen_id=test_onsen.id,
                visit_time=week_start_dt + timedelta(days=5),
                stay_length_minutes=75,
                sauna_visited=True,
            )
            db.add_all([visit1, visit2, visit3])

            # Create exercise sessions
            run1 = ExerciseSession(
                exercise_type=ExerciseType.RUNNING.value,
                data_source=DataSource.MANUAL.value,
                recording_start=week_start_dt + timedelta(days=2),
                recording_end=week_start_dt + timedelta(days=2, hours=0, minutes=30),
                duration_minutes=30,
                distance_km=5.0,
                data_file_path="test_integration",
                data_hash="test_hash_1",
            )
            run2 = ExerciseSession(
                exercise_type=ExerciseType.RUNNING.value,
                data_source=DataSource.MANUAL.value,
                recording_start=week_start_dt + timedelta(days=4),
                recording_end=week_start_dt + timedelta(days=4, hours=0, minutes=48),
                duration_minutes=48,
                distance_km=8.0,
                data_file_path="test_integration",
                data_hash="test_hash_2",
            )
            gym = ExerciseSession(
                exercise_type=ExerciseType.GYM.value,
                data_source=DataSource.MANUAL.value,
                recording_start=week_start_dt + timedelta(days=3),
                recording_end=week_start_dt + timedelta(days=3, hours=1),
                duration_minutes=60,
                data_file_path="test_integration",
                data_hash="test_hash_3",
            )
            hike = ExerciseSession(
                exercise_type=ExerciseType.HIKING.value,
                data_source=DataSource.MANUAL.value,
                recording_start=week_start_dt + timedelta(days=6),
                recording_end=week_start_dt + timedelta(days=6, hours=3),
                duration_minutes=180,
                distance_km=12.0,
                data_file_path="test_integration",
                data_hash="test_hash_4",
            )
            db.add_all([run1, run2, gym, hike])
            db.commit()

        try:
            # Test auto-fetch
            metrics = auto_fetch_week_statistics(week_start, week_end, database_url=CONST.DATABASE_URL)

            assert metrics is not None
            assert metrics.onsen_visits_count == 3
            assert metrics.sauna_sessions_count == 2
            assert metrics.total_soaking_hours == 3.0  # (60 + 45 + 75) / 60
            assert metrics.running_distance_km == 13.0  # 5 + 8
            assert metrics.gym_sessions_count == 1
            assert metrics.long_exercise_completed is True

        finally:
            # Cleanup test data
            with get_db(url=CONST.DATABASE_URL) as db:
                # Delete test visits
                db.query(OnsenVisit).filter(
                    OnsenVisit.visit_time >= week_start_dt
                ).filter(
                    OnsenVisit.visit_time <= week_end_dt
                ).delete()

                # Delete test exercise sessions
                db.query(ExerciseSession).filter(
                    ExerciseSession.data_file_path == "test_integration"
                ).delete()

                db.commit()

    def test_auto_fetch_with_visits_outside_date_range(self):
        """Test that visits outside date range are not counted."""
        week_start_dt = datetime.now() - timedelta(days=14)
        week_end_dt = datetime.now() - timedelta(days=7)
        week_start = week_start_dt.strftime("%Y-%m-%d")
        week_end = week_end_dt.strftime("%Y-%m-%d")

        with get_db(url=CONST.DATABASE_URL) as db:
            # Find or create a test onsen
            test_onsen = db.query(Onsen).first()
            if not test_onsen:
                pytest.skip("No onsens in database - cannot test without onsen data")

            # Create visit BEFORE the week
            visit_before = OnsenVisit(
                onsen_id=test_onsen.id,
                visit_time=week_start_dt - timedelta(days=1),
                stay_length_minutes=60,
                sauna_visited=True,
            )

            # Create visit AFTER the week
            visit_after = OnsenVisit(
                onsen_id=test_onsen.id,
                visit_time=week_end_dt + timedelta(days=1),
                stay_length_minutes=60,
                sauna_visited=True,
            )

            # Create visit WITHIN the week
            visit_within = OnsenVisit(
                onsen_id=test_onsen.id,
                visit_time=week_start_dt + timedelta(days=3),
                stay_length_minutes=60,
                sauna_visited=True,
            )

            db.add_all([visit_before, visit_after, visit_within])
            db.commit()

        try:
            # Test auto-fetch
            metrics = auto_fetch_week_statistics(week_start, week_end, database_url=CONST.DATABASE_URL)

            assert metrics is not None
            assert metrics.onsen_visits_count == 1  # Only visit_within
            assert metrics.sauna_sessions_count == 1

        finally:
            # Cleanup
            with get_db(url=CONST.DATABASE_URL) as db:
                # Delete all three test visits
                db.query(OnsenVisit).filter(
                    OnsenVisit.visit_time >= week_start_dt - timedelta(days=2)
                ).filter(
                    OnsenVisit.visit_time <= week_end_dt + timedelta(days=2)
                ).delete()
                db.commit()

    def test_auto_fetch_handles_none_values(self):
        """Test auto-fetch handles visits with None/missing values gracefully."""
        week_start_dt = datetime.now() - timedelta(days=7)
        week_end_dt = datetime.now()
        week_start = week_start_dt.strftime("%Y-%m-%d")
        week_end = week_end_dt.strftime("%Y-%m-%d")

        with get_db(url=CONST.DATABASE_URL) as db:
            test_onsen = db.query(Onsen).first()
            if not test_onsen:
                pytest.skip("No onsens in database")

            # Create visit with None values
            visit = OnsenVisit(
                onsen_id=test_onsen.id,
                visit_time=week_start_dt + timedelta(days=1),
                stay_length_minutes=None,
                sauna_visited=None,
            )
            db.add(visit)
            db.commit()

        try:
            metrics = auto_fetch_week_statistics(week_start, week_end, database_url=CONST.DATABASE_URL)

            assert metrics is not None
            assert metrics.onsen_visits_count == 1
            assert metrics.sauna_sessions_count == 0  # None treated as False
            assert metrics.total_soaking_hours is None  # No valid times

        finally:
            # Cleanup
            with get_db(url=CONST.DATABASE_URL) as db:
                db.query(OnsenVisit).filter(
                    OnsenVisit.visit_time >= week_start_dt
                ).filter(
                    OnsenVisit.visit_time <= week_end_dt
                ).delete()
                db.commit()

    def test_auto_fetch_with_invalid_date_format(self):
        """Test auto-fetch handles invalid date format gracefully."""
        metrics = auto_fetch_week_statistics("invalid-date", "also-invalid", database_url=CONST.DATABASE_URL)

        # Should return None due to error
        assert metrics is None
