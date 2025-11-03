"""
Unit tests for activity-visit pairing system.

Tests cover:
- Name extraction from various activity title formats
- Name similarity calculations
- Candidate scoring algorithm
- Pairing logic and categorization
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from src.lib.activity_visit_pairer import (
    PairingConfig,
    PairingResults,
    ScoredCandidate,
    calculate_name_similarity,
    extract_onsen_name,
    find_visit_candidates,
    pair_activities_to_visits,
    score_visit_candidate,
)
from src.types.exercise import ExerciseType


class TestExtractOnsenName:
    """Test onsen name extraction from activity titles."""

    def test_extract_japanese_name_in_parentheses(self):
        """Should extract Japanese name from standard format."""
        activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        result = extract_onsen_name(activity_name)
        assert result == "湯屋えびす"

    def test_extract_japanese_name_with_complex_characters(self):
        """Should handle complex Japanese characters."""
        activity_name = "Onsendo 5/88 - Takegawara onsen (竹瓦温泉)"
        result = extract_onsen_name(activity_name)
        assert result == "竹瓦温泉"

    def test_extract_partial_japanese_name(self):
        """Should extract partial Japanese name."""
        activity_name = "Onsendo 8/88 - Matsubara onsen (松原)"
        result = extract_onsen_name(activity_name)
        assert result == "松原"

    def test_fallback_to_romanized_name(self):
        """Should fall back to romanized name if no parentheses."""
        activity_name = "Onsendo 5/88 - Takegawara onsen"
        result = extract_onsen_name(activity_name)
        assert result == "Takegawara"

    def test_fallback_removes_onsen_suffix(self):
        """Should remove 'onsen' suffix from romanized names."""
        activity_name = "Onsendo 10/88 - Myoban Onsen"
        result = extract_onsen_name(activity_name)
        assert result == "Myoban"

    def test_fallback_case_insensitive_onsen_removal(self):
        """Should remove 'onsen' suffix case-insensitively."""
        activity_name = "Onsendo 10/88 - Myoban ONSEN"
        result = extract_onsen_name(activity_name)
        assert result == "Myoban"

    def test_no_match_returns_none(self):
        """Should return None if no pattern matches."""
        activity_name = "Random running activity"
        result = extract_onsen_name(activity_name)
        assert result is None

    def test_empty_string_returns_none(self):
        """Should return None for empty string."""
        result = extract_onsen_name("")
        assert result is None

    def test_whitespace_handling(self):
        """Should handle extra whitespace correctly."""
        activity_name = "Onsendo 9/88 - Ebisuya onsen  (  湯屋えびす  )  "
        result = extract_onsen_name(activity_name)
        assert result == "湯屋えびす"

    def test_multiple_parentheses_uses_last(self):
        """Should use last parentheses pair for Japanese name."""
        activity_name = "Onsendo 9/88 (note) - Ebisuya onsen (湯屋えびす)"
        result = extract_onsen_name(activity_name)
        assert result == "湯屋えびす"


class TestCalculateNameSimilarity:
    """Test name similarity calculation."""

    def test_exact_match(self):
        """Should return 1.0 for identical names."""
        result = calculate_name_similarity("湯屋えびす", "湯屋えびす")
        assert result == 1.0

    def test_case_insensitive(self):
        """Should be case-insensitive for romanized names."""
        result = calculate_name_similarity("Takegawara", "takegawara")
        assert result == 1.0

    def test_partial_match(self):
        """Should return partial score for partial matches."""
        result = calculate_name_similarity("Matsubara", "Matsubara onsen")
        assert 0.7 < result < 1.0  # High but not perfect match

    def test_no_match(self):
        """Should return low score for completely different names."""
        result = calculate_name_similarity("湯屋えびす", "春日温泉")
        assert result < 0.5

    def test_whitespace_normalization(self):
        """Should normalize whitespace before comparison."""
        result = calculate_name_similarity("  Takegawara  ", "Takegawara")
        assert result == 1.0

    def test_different_scripts_no_match(self):
        """Should return low score for different scripts."""
        result = calculate_name_similarity("Takegawara", "竹瓦温泉")
        assert result < 0.3


class TestScoreVisitCandidate:
    """Test visit candidate scoring."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = PairingConfig(
            time_window_hours=4,
            name_weight=0.6,
            time_weight=0.4,
        )

    def test_perfect_match(self):
        """Should score 1.0 for perfect name match at exact same time."""
        # Create mock activity
        activity = Mock()
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)

        # Create mock visit
        visit = Mock()
        visit.visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit.onsen = Mock()
        visit.onsen.name = "湯屋えびす"

        result = score_visit_candidate(activity, visit, self.config)

        assert result.name_similarity == 1.0
        assert result.time_diff_minutes == 0.0
        assert result.combined_score == 1.0
        assert result.onsen_name == "湯屋えびす"

    def test_high_confidence_match(self):
        """Should score high for exact name match within reasonable time."""
        activity = Mock()
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.recording_start = datetime(2025, 10, 30, 12, 15, 0)

        visit = Mock()
        visit.visit_time = datetime(2025, 10, 30, 12, 7, 0)  # 8 minutes before
        visit.onsen = Mock()
        visit.onsen.name = "湯屋えびす"

        result = score_visit_candidate(activity, visit, self.config)

        assert result.name_similarity == 1.0
        assert result.time_diff_minutes == 8.0
        # Time score: 1.0 - (8 / 240) ≈ 0.967
        # Combined: 0.6 * 1.0 + 0.4 * 0.967 ≈ 0.987
        assert result.combined_score > 0.95

    def test_medium_confidence_match(self):
        """Should score medium for partial name match."""
        activity = Mock()
        activity.activity_name = "Onsendo 8/88 - Matsubara onsen (松原)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)

        visit = Mock()
        visit.visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit.onsen = Mock()
        visit.onsen.name = "松原温泉"  # Slightly different (has 温泉 suffix)

        result = score_visit_candidate(activity, visit, self.config)

        # Name similarity should be high but not perfect
        # 松原 vs 松原温泉 = 0.667 similarity (2/3)
        assert 0.65 < result.name_similarity < 1.0
        assert result.time_diff_minutes == 0.0
        # Combined score should be in medium range
        assert 0.65 < result.combined_score < 0.95

    def test_low_confidence_different_name(self):
        """Should score low for different onsen name."""
        activity = Mock()
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)

        visit = Mock()
        visit.visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit.onsen = Mock()
        visit.onsen.name = "春日温泉"  # Completely different onsen

        result = score_visit_candidate(activity, visit, self.config)

        assert result.name_similarity < 0.5
        # Even with perfect time match, combined score should be low
        assert result.combined_score < 0.6

    def test_time_proximity_scoring(self):
        """Should decrease score with increasing time difference."""
        activity = Mock()
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)

        visit = Mock()
        visit.onsen = Mock()
        visit.onsen.name = "湯屋えびす"

        # Test at different time offsets
        visit.visit_time = datetime(2025, 10, 30, 12, 0, 0)  # 0 min
        score_0min = score_visit_candidate(activity, visit, self.config)

        visit.visit_time = datetime(2025, 10, 30, 13, 0, 0)  # 60 min
        score_60min = score_visit_candidate(activity, visit, self.config)

        visit.visit_time = datetime(2025, 10, 30, 14, 0, 0)  # 120 min
        score_120min = score_visit_candidate(activity, visit, self.config)

        # Scores should decrease with time
        assert score_0min.combined_score > score_60min.combined_score
        assert score_60min.combined_score > score_120min.combined_score


class TestFindVisitCandidates:
    """Test finding and scoring visit candidates."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = PairingConfig(
            time_window_hours=4,
            review_threshold=0.6,
            max_candidates=5,
        )

    def test_finds_candidates_within_time_window(self):
        """Should find visits within time window."""
        # Mock activity
        activity = Mock()
        activity.id = 1
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)

        # Mock visits
        visit1 = Mock()
        visit1.visit_time = datetime(2025, 10, 30, 11, 55, 0)  # Within window
        visit1.onsen = Mock()
        visit1.onsen.name = "湯屋えびす"

        visit2 = Mock()
        visit2.visit_time = datetime(2025, 10, 30, 12, 5, 0)  # Within window
        visit2.onsen = Mock()
        visit2.onsen.name = "春日温泉"

        # Mock database query
        db_session = Mock()
        query_mock = db_session.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.all.return_value = [visit1, visit2]

        results = find_visit_candidates(db_session, activity, self.config)

        # Should only return visit1 (high name similarity)
        assert len(results) == 1
        assert results[0].onsen_name == "湯屋えびす"
        assert results[0].name_similarity == 1.0

    def test_sorts_by_combined_score(self):
        """Should sort candidates by combined score (highest first)."""
        activity = Mock()
        activity.id = 1
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)

        # Visit with perfect name but worse time
        visit1 = Mock()
        visit1.visit_time = datetime(2025, 10, 30, 10, 0, 0)  # 120 min away
        visit1.onsen = Mock()
        visit1.onsen.name = "湯屋えびす"

        # Visit with good name and perfect time
        visit2 = Mock()
        visit2.visit_time = datetime(2025, 10, 30, 12, 0, 0)  # 0 min away
        visit2.onsen = Mock()
        visit2.onsen.name = "湯屋えびす温泉"  # Slightly different

        db_session = Mock()
        query_mock = db_session.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.all.return_value = [visit1, visit2]

        results = find_visit_candidates(db_session, activity, self.config)

        # Both should be included, sorted by score
        assert len(results) >= 2
        # First result should have higher combined score
        assert results[0].combined_score > results[1].combined_score

    def test_limits_to_max_candidates(self):
        """Should limit results to max_candidates."""
        activity = Mock()
        activity.id = 1
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)

        # Create 10 visits with similar names
        visits = []
        for i in range(10):
            visit = Mock()
            visit.visit_time = datetime(2025, 10, 30, 12, i, 0)
            visit.onsen = Mock()
            visit.onsen.name = "湯屋えびす"
            visits.append(visit)

        db_session = Mock()
        query_mock = db_session.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.all.return_value = visits

        config = PairingConfig(max_candidates=3)
        results = find_visit_candidates(db_session, activity, config)

        assert len(results) == 3

    def test_filters_by_review_threshold(self):
        """Should filter out candidates below review_threshold."""
        activity = Mock()
        activity.id = 1
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)

        # Good match
        visit1 = Mock()
        visit1.visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit1.onsen = Mock()
        visit1.onsen.name = "湯屋えびす"

        # Poor match
        visit2 = Mock()
        visit2.visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit2.onsen = Mock()
        visit2.onsen.name = "完全に異なる温泉"

        db_session = Mock()
        query_mock = db_session.query.return_value
        join_mock = query_mock.join.return_value
        filter_mock = join_mock.filter.return_value
        filter_mock.all.return_value = [visit1, visit2]

        results = find_visit_candidates(db_session, activity, self.config)

        # Should only include visit1 (above threshold)
        assert len(results) == 1
        assert results[0].onsen_name == "湯屋えびす"


class TestPairActivitiesToVisits:
    """Test end-to-end pairing logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = PairingConfig(
            auto_link_threshold=0.8,
            review_threshold=0.6,
            time_window_hours=4,
        )

    def test_auto_links_high_confidence_matches(self):
        """Should auto-link activities with confidence ≥ threshold."""
        # Mock activity with perfect match
        activity = Mock()
        activity.id = 1
        activity.activity_type = ExerciseType.ONSEN_MONITORING.value
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)
        activity.visit_id = None

        # Mock visit
        visit = Mock()
        visit.id = 10
        visit.visit_time = datetime(2025, 10, 30, 12, 0, 0)
        visit.onsen = Mock()
        visit.onsen.name = "湯屋えびす"

        # Mock database
        db_session = Mock()

        # Track which model is being queried
        query_call_count = [0]

        def query_side_effect(_model):
            query_call_count[0] += 1
            if query_call_count[0] == 1:
                # First call: Activity query
                activity_query = Mock()
                activity_filter = activity_query.filter.return_value
                activity_filter.all.return_value = [activity]
                return activity_query
            else:
                # Subsequent calls: OnsenVisit query
                visit_query = Mock()
                join_mock = visit_query.join.return_value
                filter_mock = join_mock.filter.return_value
                filter_mock.all.return_value = [visit]
                return visit_query

        db_session.query.side_effect = query_side_effect

        results = pair_activities_to_visits(db_session, [1], self.config)

        assert len(results.auto_linked) == 1
        assert len(results.manual_review) == 0
        assert len(results.no_match) == 0

        linked_activity, linked_visit, confidence = results.auto_linked[0]
        assert linked_activity.id == 1
        assert linked_visit.id == 10
        assert confidence >= 0.8

    def test_flags_medium_confidence_for_review(self):
        """Should flag medium confidence matches for manual review."""
        # Mock activity with partial match
        activity = Mock()
        activity.id = 2
        activity.activity_type = ExerciseType.ONSEN_MONITORING.value
        activity.activity_name = "Onsendo 8/88 - Matsubara onsen (松原)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)
        activity.visit_id = None

        # Mock visit with slightly different name
        visit = Mock()
        visit.id = 11
        visit.visit_time = datetime(2025, 10, 30, 14, 0, 0)  # 2 hours away
        visit.onsen = Mock()
        visit.onsen.name = "松原温泉"

        # Mock database
        db_session = Mock()

        query_call_count = [0]

        def query_side_effect(_model):
            query_call_count[0] += 1
            if query_call_count[0] == 1:
                # First call: Activity query
                activity_query = Mock()
                activity_filter = activity_query.filter.return_value
                activity_filter.all.return_value = [activity]
                return activity_query
            else:
                # Subsequent calls: OnsenVisit query
                visit_query = Mock()
                join_mock = visit_query.join.return_value
                filter_mock = join_mock.filter.return_value
                filter_mock.all.return_value = [visit]
                return visit_query

        db_session.query.side_effect = query_side_effect

        results = pair_activities_to_visits(db_session, [2], self.config)

        # Should be in manual_review (not auto_linked)
        assert len(results.manual_review) == 1
        assert len(results.auto_linked) == 0

    def test_handles_no_match(self):
        """Should categorize as no_match when no candidates found."""
        activity = Mock()
        activity.id = 3
        activity.activity_type = ExerciseType.ONSEN_MONITORING.value
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.recording_start = datetime(2025, 10, 30, 12, 0, 0)
        activity.visit_id = None

        # Mock database with no visits
        db_session = Mock()

        query_call_count = [0]

        def query_side_effect(_model):
            query_call_count[0] += 1
            if query_call_count[0] == 1:
                # First call: Activity query
                activity_query = Mock()
                activity_filter = activity_query.filter.return_value
                activity_filter.all.return_value = [activity]
                return activity_query
            else:
                # Subsequent calls: OnsenVisit query (returns empty)
                visit_query = Mock()
                join_mock = visit_query.join.return_value
                filter_mock = join_mock.filter.return_value
                filter_mock.all.return_value = []  # No visits
                return visit_query

        db_session.query.side_effect = query_side_effect

        results = pair_activities_to_visits(db_session, [3], self.config)

        assert len(results.no_match) == 1
        assert results.no_match[0].id == 3

    def test_skips_non_onsen_monitoring_activities(self):
        """Should skip activities not flagged as onsen_monitoring."""
        activity = Mock()
        activity.id = 4
        activity.activity_type = ExerciseType.RUNNING.value  # Not onsen_monitoring
        activity.activity_name = "Morning run"
        activity.visit_id = None

        db_session = Mock()
        activity_query = db_session.query.return_value
        activity_filter = activity_query.filter.return_value
        activity_filter.all.return_value = [activity]

        results = pair_activities_to_visits(db_session, [4], self.config)

        # Should not appear in any category
        assert len(results.auto_linked) == 0
        assert len(results.manual_review) == 0
        assert len(results.no_match) == 0

    def test_skips_already_linked_activities(self):
        """Should skip activities that already have visit_id set."""
        activity = Mock()
        activity.id = 5
        activity.activity_type = ExerciseType.ONSEN_MONITORING.value
        activity.activity_name = "Onsendo 9/88 - Ebisuya onsen (湯屋えびす)"
        activity.visit_id = 10  # Already linked

        db_session = Mock()
        activity_query = db_session.query.return_value
        activity_filter = activity_query.filter.return_value
        activity_filter.all.return_value = [activity]

        results = pair_activities_to_visits(db_session, [5], self.config)

        # Should not appear in any category
        assert len(results.auto_linked) == 0
        assert len(results.manual_review) == 0
        assert len(results.no_match) == 0


class TestPairingResults:
    """Test PairingResults helper methods."""

    def test_total_activities(self):
        """Should calculate total activities correctly."""
        results = PairingResults()

        activity1 = Mock()
        activity2 = Mock()
        activity3 = Mock()
        visit = Mock()

        results.auto_linked = [(activity1, visit, 0.9)]
        results.manual_review = [(activity2, [])]
        results.no_match = [activity3]

        assert results.total_activities() == 3

    def test_summary_stats(self):
        """Should return correct summary statistics."""
        results = PairingResults()

        activity1 = Mock()
        activity2 = Mock()
        activity3 = Mock()
        activity4 = Mock()
        visit = Mock()

        results.auto_linked = [(activity1, visit, 0.9), (activity2, visit, 0.85)]
        results.manual_review = [(activity3, [])]
        results.no_match = [activity4]

        stats = results.summary_stats()

        assert stats['auto_linked'] == 2
        assert stats['manual_review'] == 1
        assert stats['no_match'] == 1
        assert stats['total'] == 4
