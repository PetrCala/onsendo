"""
Integration tests for activity-visit pairing system.

Tests the complete pairing workflow with a real database, including:
- Creating test activities and visits
- Running pairing logic
- Verifying database linkages
- Testing edge cases
"""

import pytest
from datetime import datetime, timedelta

from src.db.models import Activity, Onsen, OnsenVisit
from src.lib.activity_manager import ActivityManager
from src.lib.activity_visit_pairer import (
    PairingConfig,
    pair_activities_to_visits,
)
from src.types.exercise import ExerciseType


@pytest.mark.integration
class TestActivityPairingIntegration:
    """Integration tests for activity-visit pairing."""

    def test_end_to_end_pairing_with_perfect_match(self, db_session, sample_onsen):
        """Test complete pairing workflow with perfect name and time match."""
        # Create onsen visit
        visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit = OnsenVisit(
            onsen_id=sample_onsen.id,
            visit_time=visit_time,
        )
        db_session.add(visit)
        db_session.flush()

        # Create activity with matching name and time
        activity = Activity(
            strava_id="12345",
            activity_type=ExerciseType.ONSEN_MONITORING.value,
            activity_name=f"Onsendo 9/88 - Test onsen ({sample_onsen.name})",
            recording_start=visit_time + timedelta(minutes=5),  # 5 min after visit
            recording_end=visit_time + timedelta(minutes=25),
            avg_heart_rate=85.0,
        )
        db_session.add(activity)
        db_session.flush()

        # Run pairing
        config = PairingConfig(auto_link_threshold=0.8)
        results = pair_activities_to_visits(db_session, [activity.id], config)

        # Verify results
        assert len(results.auto_linked) == 1
        assert len(results.manual_review) == 0
        assert len(results.no_match) == 0

        paired_activity, paired_visit, confidence = results.auto_linked[0]
        assert paired_activity.id == activity.id
        assert paired_visit.id == visit.id
        assert confidence >= 0.8

        # Apply pairing
        manager = ActivityManager(db_session)
        manager.link_to_visit(activity.id, visit.id)
        db_session.refresh(activity)

        # Verify database linkage
        assert activity.visit_id == visit.id

    def test_pairing_with_romanized_name_fallback(self, db_session, sample_onsen):
        """Test pairing with romanized name when no Japanese name in parentheses."""
        # Create visit
        visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit = OnsenVisit(
            onsen_id=sample_onsen.id,
            visit_time=visit_time,
        )
        db_session.add(visit)
        db_session.flush()

        # Activity without Japanese name in parentheses
        # This should use romanized fallback matching
        activity = Activity(
            strava_id="12346",
            activity_type=ExerciseType.ONSEN_MONITORING.value,
            activity_name="Onsendo 10/88 - Test onsen",  # No (Japanese) at end
            recording_start=visit_time + timedelta(minutes=10),
            recording_end=visit_time + timedelta(minutes=30),
            avg_heart_rate=90.0,
        )
        db_session.add(activity)
        db_session.flush()

        # Run pairing with lower threshold due to romanized matching
        config = PairingConfig(auto_link_threshold=0.7)
        results = pair_activities_to_visits(db_session, [activity.id], config)

        # Should find match (name similarity might be lower for romanized)
        assert len(results.auto_linked) + len(results.manual_review) >= 1

    def test_no_match_for_different_onsen(self, db_session):
        """Test that different onsen names don't match."""
        # Create first onsen and visit
        onsen1 = Onsen(
            ban_number="123",
            name="温泉A",
            region="Region A",
            latitude=33.279,
            longitude=131.500,
        )
        db_session.add(onsen1)
        db_session.flush()

        visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit1 = OnsenVisit(
            onsen_id=onsen1.id,
            visit_time=visit_time,
        )
        db_session.add(visit1)
        db_session.flush()

        # Create activity for different onsen
        activity = Activity(
            strava_id="12347",
            activity_type=ExerciseType.ONSEN_MONITORING.value,
            activity_name="Onsendo 11/88 - Different onsen (温泉B)",  # Different name
            recording_start=visit_time + timedelta(minutes=5),
            recording_end=visit_time + timedelta(minutes=25),
            avg_heart_rate=85.0,
        )
        db_session.add(activity)
        db_session.flush()

        # Run pairing
        config = PairingConfig(auto_link_threshold=0.8, review_threshold=0.6)
        results = pair_activities_to_visits(db_session, [activity.id], config)

        # Should not match (names too different)
        assert len(results.auto_linked) == 0
        # Might be in no_match or very low manual_review
        assert len(results.no_match) >= 1 or len(results.manual_review) == 0

    def test_time_window_filtering(self, db_session, sample_onsen):
        """Test that visits outside time window are excluded."""
        # Create visit 10 hours before activity
        visit_time = datetime(2025, 10, 30, 2, 0, 0)
        visit = OnsenVisit(
            onsen_id=sample_onsen.id,
            visit_time=visit_time,
        )
        db_session.add(visit)
        db_session.flush()

        # Activity 10 hours after visit (outside 4-hour window)
        activity = Activity(
            strava_id="12348",
            activity_type=ExerciseType.ONSEN_MONITORING.value,
            activity_name=f"Onsendo 12/88 - Test ({sample_onsen.name})",
            recording_start=visit_time + timedelta(hours=10),
            recording_end=visit_time + timedelta(hours=10, minutes=20),
            avg_heart_rate=85.0,
        )
        db_session.add(activity)
        db_session.flush()

        # Run pairing with 4-hour window
        config = PairingConfig(time_window_hours=4)
        results = pair_activities_to_visits(db_session, [activity.id], config)

        # Should not match (outside time window)
        assert len(results.no_match) == 1
        assert results.no_match[0].id == activity.id

    def test_multiple_candidates_sorted_by_score(self, db_session):
        """Test that multiple candidates are sorted by combined score."""
        # Create two onsens with similar names
        onsen1 = Onsen(
            ban_number="200",
            name="松原温泉",
            region="Region A",
            latitude=33.279,
            longitude=131.500,
        )
        onsen2 = Onsen(
            ban_number="201",
            name="松原",
            region="Region A",
            latitude=33.280,
            longitude=131.501,
        )
        db_session.add_all([onsen1, onsen2])
        db_session.flush()

        # Create visits at different times
        base_time = datetime(2025, 10, 30, 12, 0, 0)

        visit1 = OnsenVisit(
            onsen_id=onsen1.id,
            visit_time=base_time,  # Perfect time
        )
        visit2 = OnsenVisit(
            onsen_id=onsen2.id,
            visit_time=base_time + timedelta(hours=2),  # 2 hours away
        )
        db_session.add_all([visit1, visit2])
        db_session.flush()

        # Activity closer to visit2 in time but matches visit1 name better
        activity = Activity(
            strava_id="12349",
            activity_type=ExerciseType.ONSEN_MONITORING.value,
            activity_name="Onsendo 13/88 - Matsubara (松原温泉)",  # Matches onsen1 name
            recording_start=base_time + timedelta(minutes=5),
            recording_end=base_time + timedelta(minutes=25),
            avg_heart_rate=85.0,
        )
        db_session.add(activity)
        db_session.flush()

        # Run pairing
        config = PairingConfig(auto_link_threshold=0.8, review_threshold=0.6)
        results = pair_activities_to_visits(db_session, [activity.id], config)

        # Should pair with visit1 (better name match + close time)
        if results.auto_linked:
            assert results.auto_linked[0][1].id == visit1.id
        elif results.manual_review:
            # First candidate should be visit1
            assert results.manual_review[0][1][0].visit.id == visit1.id

    def test_skips_already_linked_activities(self, db_session, sample_onsen):
        """Test that already-linked activities are skipped."""
        # Create visit
        visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit = OnsenVisit(
            onsen_id=sample_onsen.id,
            visit_time=visit_time,
        )
        db_session.add(visit)
        db_session.flush()

        # Create activity already linked to visit
        activity = Activity(
            strava_id="12350",
            activity_type=ExerciseType.ONSEN_MONITORING.value,
            activity_name=f"Onsendo 14/88 - Test ({sample_onsen.name})",
            recording_start=visit_time + timedelta(minutes=5),
            recording_end=visit_time + timedelta(minutes=25),
            avg_heart_rate=85.0,
            visit_id=visit.id,  # Already linked
        )
        db_session.add(activity)
        db_session.flush()

        # Run pairing
        config = PairingConfig()
        results = pair_activities_to_visits(db_session, [activity.id], config)

        # Should not appear in any category (already linked)
        assert len(results.auto_linked) == 0
        assert len(results.manual_review) == 0
        assert len(results.no_match) == 0

    def test_skips_non_onsen_monitoring_activities(self, db_session, sample_onsen):
        """Test that non-onsen-monitoring activities are skipped."""
        # Create visit
        visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit = OnsenVisit(
            onsen_id=sample_onsen.id,
            visit_time=visit_time,
        )
        db_session.add(visit)
        db_session.flush()

        # Create running activity (not onsen monitoring)
        activity = Activity(
            strava_id="12351",
            activity_type=ExerciseType.RUNNING.value,  # Not onsen_monitoring
            activity_name="Morning run",
            recording_start=visit_time + timedelta(minutes=5),
            recording_end=visit_time + timedelta(minutes=35),
            avg_heart_rate=150.0,
        )
        db_session.add(activity)
        db_session.flush()

        # Run pairing
        config = PairingConfig()
        results = pair_activities_to_visits(db_session, [activity.id], config)

        # Should not appear in any category (wrong type)
        assert len(results.auto_linked) == 0
        assert len(results.manual_review) == 0
        assert len(results.no_match) == 0

    def test_batch_pairing_multiple_activities(self, db_session):
        """Test pairing multiple activities at once."""
        # Create multiple onsens and visits
        onsens_and_visits = []
        base_time = datetime(2025, 10, 30, 10, 0, 0)

        for i in range(3):
            onsen = Onsen(
                ban_number=f"30{i}",
                name=f"温泉{i}",
                region="Region A",
                latitude=33.279 + i * 0.001,
                longitude=131.500 + i * 0.001,
            )
            db_session.add(onsen)
            db_session.flush()

            visit = OnsenVisit(
                onsen_id=onsen.id,
                visit_time=base_time + timedelta(hours=i),
            )
            db_session.add(visit)
            db_session.flush()

            onsens_and_visits.append((onsen, visit))

        # Create matching activities
        activities = []
        for i, (onsen, visit) in enumerate(onsens_and_visits):
            activity = Activity(
                strava_id=f"1235{i}",
                activity_type=ExerciseType.ONSEN_MONITORING.value,
                activity_name=f"Onsendo {15+i}/88 - Onsen {i} ({onsen.name})",
                recording_start=visit.visit_time + timedelta(minutes=5),
                recording_end=visit.visit_time + timedelta(minutes=25),
                avg_heart_rate=85.0 + i * 5,
            )
            db_session.add(activity)
            db_session.flush()
            activities.append(activity)

        # Run batch pairing
        activity_ids = [a.id for a in activities]
        config = PairingConfig(auto_link_threshold=0.8)
        results = pair_activities_to_visits(db_session, activity_ids, config)

        # Should auto-link all 3
        assert len(results.auto_linked) == 3

        # Verify each pairing
        for activity, visit, confidence in results.auto_linked:
            assert activity.id in activity_ids
            assert confidence >= 0.8
