"""
Unit tests for distance calculation functionality.
"""

import pytest
import math
from unittest.mock import Mock

from src.lib.distance import (
    haversine_distance,
    calculate_distance_to_onsen,
    filter_onsens_by_distance,
    get_distance_category_name,
    _is_distance_in_category,
    DistanceCategory,
    DistanceMilestones,
    DISTANCE_CATEGORIES,
    DEFAULT_DISTANCE_CATEGORIES,
    update_distance_categories,
    reset_distance_categories,
)
from src.db.models import Location, Onsen


class TestHaversineDistance:
    """Test haversine distance calculation."""

    def test_haversine_distance_same_point(self):
        """Test distance calculation for same point."""
        lat, lon = 35.6762, 139.6503  # Tokyo
        distance = haversine_distance(lat, lon, lat, lon)
        assert distance == 0.0

    def test_haversine_distance_known_distance(self):
        """Test distance calculation for known coordinates."""
        # Tokyo to Osaka (approximately 400 km)
        tokyo_lat, tokyo_lon = 35.6762, 139.6503
        osaka_lat, osaka_lon = 34.6937, 135.5023
        distance = haversine_distance(tokyo_lat, tokyo_lon, osaka_lat, osaka_lon)

        # Should be approximately 400 km (allowing for some variance)
        assert 380 <= distance <= 420

    def test_haversine_distance_short_distance(self):
        """Test distance calculation for short distances."""
        # Two points about 1 km apart
        lat1, lon1 = 35.6762, 139.6503
        lat2, lon2 = 35.6762, 139.6603  # 0.01 degrees longitude difference
        distance = haversine_distance(lat1, lon1, lat2, lon2)

        # Should be approximately 1 km
        assert 0.8 <= distance <= 1.2


class TestCalculateDistanceToOnsen:
    """Test distance calculation between location and onsen."""

    def test_calculate_distance_to_onsen_valid_coordinates(self):
        """Test distance calculation with valid coordinates."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503

        onsen = Mock(spec=Onsen)
        onsen.latitude = 35.6762
        onsen.longitude = 139.6603

        distance = calculate_distance_to_onsen(location, onsen)
        assert distance is not None
        assert distance > 0

    def test_calculate_distance_to_onsen_missing_location_coordinates(self):
        """Test distance calculation with missing location coordinates."""
        location = Mock(spec=Location)
        location.latitude = None
        location.longitude = 139.6503

        onsen = Mock(spec=Onsen)
        onsen.latitude = 35.6762
        onsen.longitude = 139.6603

        distance = calculate_distance_to_onsen(location, onsen)
        assert distance is None

    def test_calculate_distance_to_onsen_missing_onsen_coordinates(self):
        """Test distance calculation with missing onsen coordinates."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503

        onsen = Mock(spec=Onsen)
        onsen.latitude = 35.6762
        onsen.longitude = None

        distance = calculate_distance_to_onsen(location, onsen)
        assert distance is None


class TestDistanceCategories:
    """Test distance category functionality."""

    def test_distance_category_creation(self):
        """Test DistanceCategory creation."""
        category = DistanceCategory("test", 10.0, "Test category")
        assert category.name == "test"
        assert category.max_distance_km == 10.0
        assert category.description == "Test category"

    def test_distance_milestones_creation(self):
        """Test DistanceMilestones creation."""
        milestones = DistanceMilestones(1.0, 5.0, 15.0, 15.0)
        assert milestones.very_close_max == 1.0
        assert milestones.close_max == 5.0
        assert milestones.medium_max == 15.0
        assert milestones.far_min == 15.0

    def test_distance_milestones_to_categories(self):
        """Test conversion of milestones to categories."""
        milestones = DistanceMilestones(1.0, 5.0, 15.0, 15.0)
        categories = milestones.to_categories()

        assert "very_close" in categories
        assert "close" in categories
        assert "medium" in categories
        assert "far" in categories
        assert "any" in categories

        assert categories["very_close"].max_distance_km == 1.0
        assert categories["close"].max_distance_km == 5.0
        assert categories["medium"].max_distance_km == 15.0
        assert categories["far"].max_distance_km == float("inf")
        assert categories["any"].max_distance_km == float("inf")


class TestDistanceCategoryFiltering:
    """Test distance category filtering logic."""

    def test_is_distance_in_category_very_close(self):
        """Test very_close category filtering."""
        # Test with default categories
        assert _is_distance_in_category(0.5, "very_close") == True
        assert _is_distance_in_category(10.0, "very_close") == False

    def test_is_distance_in_category_close(self):
        """Test close category filtering."""
        # Test with default categories
        assert _is_distance_in_category(0.5, "close") == False  # Too close
        assert _is_distance_in_category(10.0, "close") == True  # In range
        assert _is_distance_in_category(20.0, "close") == False  # Too far

    def test_is_distance_in_category_medium(self):
        """Test medium category filtering."""
        # Test with default categories
        assert _is_distance_in_category(10.0, "medium") == False  # Too close
        assert _is_distance_in_category(30.0, "medium") == True  # In range
        assert _is_distance_in_category(60.0, "medium") == False  # Too far

    def test_is_distance_in_category_far(self):
        """Test far category filtering."""
        # Test with default categories
        assert _is_distance_in_category(30.0, "far") == False  # Too close
        assert _is_distance_in_category(60.0, "far") == True  # In range

    def test_is_distance_in_category_any(self):
        """Test any category filtering."""
        # Test with any category - should accept all distances
        assert _is_distance_in_category(0.5, "any") == True
        assert _is_distance_in_category(10.0, "any") == True
        assert _is_distance_in_category(100.0, "any") == True
        assert _is_distance_in_category(1000.0, "any") == True


class TestGetDistanceCategoryName:
    """Test distance category name determination."""

    def test_get_distance_category_name_default_categories(self):
        """Test category name determination with default categories."""
        assert get_distance_category_name(0.5) == "very_close"
        assert get_distance_category_name(10.0) == "close"
        assert get_distance_category_name(30.0) == "medium"
        assert get_distance_category_name(100.0) == "far"


class TestDistanceCategoryManagement:
    """Test distance category management functions."""

    def test_update_distance_categories(self):
        """Test updating distance categories."""
        milestones = DistanceMilestones(2.0, 8.0, 20.0, 20.0)
        categories = milestones.to_categories()

        # Test that the categories are created correctly
        assert categories["very_close"].max_distance_km == 2.0
        assert categories["close"].max_distance_km == 8.0
        assert categories["medium"].max_distance_km == 20.0
        assert categories["far"].max_distance_km == float("inf")

    def test_reset_distance_categories(self):
        """Test resetting distance categories to defaults."""
        original_categories = DISTANCE_CATEGORIES.copy()

        try:
            # First update with custom categories
            milestones = DistanceMilestones(2.0, 8.0, 20.0, 20.0)
            update_distance_categories(milestones)

            # Then reset
            reset_distance_categories()

            assert DISTANCE_CATEGORIES["very_close"].max_distance_km == 5.0
            assert DISTANCE_CATEGORIES["close"].max_distance_km == 15.0
            assert DISTANCE_CATEGORIES["medium"].max_distance_km == 50.0
        finally:
            # Restore original categories
            globals()["DISTANCE_CATEGORIES"] = original_categories

    def test_update_distance_categories_preserves_any(self):
        """Test that 'any' category is preserved after dynamic milestone updates."""
        original_categories = DISTANCE_CATEGORIES.copy()

        try:
            # Update with custom milestones
            milestones = DistanceMilestones(2.0, 8.0, 20.0, 20.0)
            update_distance_categories(milestones)

            # Verify 'any' category still exists
            assert "any" in DISTANCE_CATEGORIES
            assert DISTANCE_CATEGORIES["any"].max_distance_km == float("inf")
            assert DISTANCE_CATEGORIES["any"].description == "Any distance"
        finally:
            # Restore original categories
            globals()["DISTANCE_CATEGORIES"] = original_categories


class TestFilterOnsensByDistance:
    """Test filtering onsens by distance."""

    def test_filter_onsens_by_distance_valid_category(self):
        """Test filtering with valid distance category."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503

        onsens = []
        for i in range(3):
            onsen = Mock(spec=Onsen)
            onsen.latitude = 35.6762 + (i * 0.01)  # Increasing distance
            onsen.longitude = 139.6503
            onsens.append(onsen)

        # Use default categories for testing
        result = filter_onsens_by_distance(onsens, location, "very_close")

        # Should return onsens within 5km (default very_close)
        assert len(result) > 0
        for onsen, distance in result:
            assert distance <= 5.0

    def test_filter_onsens_by_distance_invalid_category(self):
        """Test filtering with invalid distance category."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503

        onsens = [Mock(spec=Onsen)]

        with pytest.raises(ValueError, match="Invalid distance category"):
            filter_onsens_by_distance(onsens, location, "invalid_category")

    def test_filter_onsens_by_distance_empty_list(self):
        """Test filtering with empty onsen list."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503

        result = filter_onsens_by_distance([], location, "very_close")
        assert result == []

    def test_filter_onsens_by_distance_sorted_results(self):
        """Test that filtered results are sorted by distance."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503

        onsens = []
        # Create onsens at increasing distances
        for i in range(3):
            onsen = Mock(spec=Onsen)
            onsen.latitude = 35.6762 + (i * 0.01)
            onsen.longitude = 139.6503
            onsens.append(onsen)

        result = filter_onsens_by_distance(onsens, location, "close")

        # Check that results are sorted by distance (closest first)
        if len(result) >= 2:
            assert result[0][1] <= result[1][1]

    def test_filter_onsens_by_distance_with_limit(self):
        """The filter should honor the provided limit and keep closest results."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503

        onsens = []
        for i in range(5):
            onsen = Mock(spec=Onsen)
            onsen.latitude = 35.6762 + (i * 0.01)
            onsen.longitude = 139.6503
            onsens.append(onsen)

        result = filter_onsens_by_distance(onsens, location, "very_close", limit=2)

        assert len(result) <= 2
        distances = [distance for _, distance in result]
        assert distances == sorted(distances)

    def test_filter_onsens_by_distance_any_category(self):
        """Test filtering with 'any' distance category."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503

        onsens = []
        # Create onsens at various distances including very far ones
        distances_degrees = [0.01, 0.1, 0.5, 1.0, 2.0]  # From close to very far
        for i, degree_offset in enumerate(distances_degrees):
            onsen = Mock(spec=Onsen)
            onsen.latitude = 35.6762 + degree_offset
            onsen.longitude = 139.6503
            onsens.append(onsen)

        result = filter_onsens_by_distance(onsens, location, "any")

        # Should return all onsens regardless of distance
        assert len(result) == len(onsens)

        # Results should still be sorted by distance (closest first)
        distances = [distance for _, distance in result]
        assert distances == sorted(distances)
