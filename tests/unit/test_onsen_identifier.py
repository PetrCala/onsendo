"""Unit tests for onsen identification functionality."""

import pytest
from unittest.mock import MagicMock

from src.lib.onsen_identifier import (
    _calculate_string_similarity,
    identify_by_name,
    identify_by_coordinates,
    identify_by_address,
    identify_by_region,
    identify_onsen,
    OnsenMatch,
)
from src.db.models import Onsen


class TestStringSimilarity:
    """Tests for string similarity calculation."""

    def test_exact_match(self):
        """Test that identical strings return 1.0 similarity."""
        assert _calculate_string_similarity("test", "test") == 1.0

    def test_case_insensitive(self):
        """Test that comparison is case-insensitive."""
        assert _calculate_string_similarity("Test", "test") == 1.0
        assert _calculate_string_similarity("TEST", "test") == 1.0

    def test_whitespace_normalized(self):
        """Test that leading/trailing whitespace is normalized."""
        assert _calculate_string_similarity("  test  ", "test") == 1.0

    def test_partial_match(self):
        """Test that partial matches return values between 0 and 1."""
        similarity = _calculate_string_similarity("testing", "test")
        assert 0.0 < similarity < 1.0

    def test_no_match(self):
        """Test that completely different strings return low similarity."""
        similarity = _calculate_string_similarity("abc", "xyz")
        assert similarity < 0.5

    def test_empty_strings(self):
        """Test that empty strings return 0.0 similarity."""
        assert _calculate_string_similarity("", "test") == 0.0
        assert _calculate_string_similarity("test", "") == 0.0
        assert _calculate_string_similarity("", "") == 0.0

    def test_none_strings(self):
        """Test that None strings are handled gracefully."""
        assert _calculate_string_similarity(None, "test") == 0.0
        assert _calculate_string_similarity("test", None) == 0.0


class TestIdentifyByName:
    """Tests for name-based identification."""

    def test_exact_match(self):
        """Test identification with exact name match."""
        # Create mock onsens
        onsen1 = Onsen(id=1, ban_number="001", name="Test Onsen")
        onsen2 = Onsen(id=2, ban_number="002", name="Other Onsen")

        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1, onsen2]

        # Test exact match
        matches = identify_by_name(mock_db, "Test Onsen", threshold=0.6, limit=5)

        assert len(matches) >= 1
        assert matches[0].onsen.name == "Test Onsen"
        assert matches[0].confidence == 1.0
        assert matches[0].match_type == "name"

    def test_fuzzy_match(self):
        """Test identification with fuzzy name match."""
        onsen1 = Onsen(id=1, ban_number="001", name="Beppu Onsen")
        onsen2 = Onsen(id=2, ban_number="002", name="Tokyo Onsen")

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1, onsen2]

        # Test fuzzy match
        matches = identify_by_name(mock_db, "Beppu", threshold=0.5, limit=5)

        assert len(matches) >= 1
        assert matches[0].onsen.name == "Beppu Onsen"
        assert 0.5 <= matches[0].confidence < 1.0

    def test_threshold_filtering(self):
        """Test that matches below threshold are filtered out."""
        onsen1 = Onsen(id=1, ban_number="001", name="Completely Different")
        onsen2 = Onsen(id=2, ban_number="002", name="Test")

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1, onsen2]

        # High threshold should filter out low matches
        matches = identify_by_name(mock_db, "Test", threshold=0.9, limit=5)

        assert len(matches) == 1
        assert matches[0].onsen.name == "Test"

    def test_limit_results(self):
        """Test that results are limited to specified count."""
        onsens = [
            Onsen(id=i, ban_number=f"{i:03d}", name=f"Test {i}") for i in range(10)
        ]

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = onsens

        # Limit to 3 results
        matches = identify_by_name(mock_db, "Test", threshold=0.5, limit=3)

        assert len(matches) <= 3

    def test_sorted_by_confidence(self):
        """Test that results are sorted by confidence (highest first)."""
        onsen1 = Onsen(id=1, ban_number="001", name="Test")
        onsen2 = Onsen(id=2, ban_number="002", name="Test Onsen")
        onsen3 = Onsen(id=3, ban_number="003", name="Testing Place")

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1, onsen2, onsen3]

        matches = identify_by_name(mock_db, "Test", threshold=0.5, limit=5)

        # Check that confidences are in descending order
        for i in range(len(matches) - 1):
            assert matches[i].confidence >= matches[i + 1].confidence


class TestIdentifyByCoordinates:
    """Tests for location-based identification."""

    def test_closest_match(self):
        """Test that closest onsen is returned first."""
        # Create onsens at different distances
        onsen1 = Onsen(
            id=1, ban_number="001", name="Close", latitude=33.28, longitude=131.50
        )
        onsen2 = Onsen(
            id=2, ban_number="002", name="Far", latitude=35.68, longitude=139.65
        )

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1, onsen2]

        # Search near onsen1's location
        matches = identify_by_coordinates(
            mock_db, latitude=33.28, longitude=131.50, limit=5
        )

        assert len(matches) >= 1
        assert matches[0].onsen.name == "Close"
        assert matches[0].match_type == "location"

    def test_max_distance_filter(self):
        """Test that max_distance parameter filters results."""
        onsen1 = Onsen(
            id=1, ban_number="001", name="Near", latitude=33.28, longitude=131.50
        )
        onsen2 = Onsen(
            id=2, ban_number="002", name="Far", latitude=35.68, longitude=139.65
        )

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1, onsen2]

        # Search with small max distance
        matches = identify_by_coordinates(
            mock_db,
            latitude=33.28,
            longitude=131.50,
            max_distance_km=10.0,
            limit=5,
        )

        # Only nearby onsen should be returned
        assert len(matches) == 1
        assert matches[0].onsen.name == "Near"

    def test_skip_onsens_without_coordinates(self):
        """Test that onsens without coordinates are skipped."""
        onsen1 = Onsen(id=1, ban_number="001", name="No coords", latitude=None, longitude=None)
        onsen2 = Onsen(
            id=2, ban_number="002", name="Has coords", latitude=33.28, longitude=131.50
        )

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1, onsen2]

        matches = identify_by_coordinates(
            mock_db, latitude=33.28, longitude=131.50, limit=5
        )

        # Only onsen with coordinates should be returned
        assert len(matches) == 1
        assert matches[0].onsen.name == "Has coords"


class TestIdentifyByAddress:
    """Tests for address-based identification."""

    def test_address_match(self):
        """Test identification by address."""
        onsen1 = Onsen(
            id=1,
            ban_number="001",
            name="Test",
            address="123 Beppu Street, Beppu City",
        )
        onsen2 = Onsen(
            id=2, ban_number="002", name="Other", address="456 Tokyo Street, Tokyo"
        )

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1, onsen2]

        matches = identify_by_address(mock_db, "Beppu Street", threshold=0.5, limit=5)

        assert len(matches) >= 1
        assert matches[0].onsen.address == "123 Beppu Street, Beppu City"

    def test_skip_onsens_without_address(self):
        """Test that onsens without addresses are skipped."""
        onsen1 = Onsen(id=1, ban_number="001", name="No address", address=None)
        onsen2 = Onsen(
            id=2, ban_number="002", name="Has address", address="123 Main St"
        )

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1, onsen2]

        matches = identify_by_address(mock_db, "Main", threshold=0.5, limit=5)

        assert len(matches) == 1
        assert matches[0].onsen.name == "Has address"


class TestIdentifyByRegion:
    """Tests for region-based identification."""

    def test_region_match(self):
        """Test identification by region."""
        onsen1 = Onsen(id=1, ban_number="001", name="Test", region="Hamawaki")
        onsen2 = Onsen(id=2, ban_number="002", name="Other", region="Kannawa")

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1, onsen2]

        matches = identify_by_region(mock_db, "Hamawaki", threshold=0.6, limit=5)

        assert len(matches) >= 1
        assert matches[0].onsen.region == "Hamawaki"


class TestIdentifyOnsen:
    """Tests for combined identification."""

    def test_single_criterion(self):
        """Test identification with single criterion."""
        onsen1 = Onsen(id=1, ban_number="001", name="Test Onsen")

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1]

        # Use lower threshold to match "Test" against "Test Onsen"
        matches = identify_onsen(mock_db, name="Test", name_threshold=0.5, limit=5)

        assert len(matches) >= 1
        assert matches[0].onsen.name == "Test Onsen"

    def test_multiple_criteria(self):
        """Test identification combining multiple criteria."""
        onsen1 = Onsen(
            id=1,
            ban_number="001",
            name="Beppu Onsen",
            latitude=33.28,
            longitude=131.50,
            region="Hamawaki",
        )

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1]

        # Use multiple criteria
        matches = identify_onsen(
            mock_db,
            name="Beppu",
            latitude=33.28,
            longitude=131.50,
            region="Hamawaki",
            limit=5,
        )

        assert len(matches) >= 1
        # Multiple matching criteria should boost confidence
        assert matches[0].match_type == "combined"

    def test_no_criteria(self):
        """Test that no criteria returns empty list."""
        mock_db = MagicMock()

        matches = identify_onsen(mock_db, limit=5)

        assert len(matches) == 0

    def test_consolidate_duplicate_matches(self):
        """Test that the same onsen matched by different criteria is consolidated."""
        onsen1 = Onsen(
            id=1,
            ban_number="001",
            name="Beppu Onsen",
            latitude=33.28,
            longitude=131.50,
            region="Hamawaki",
        )

        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [onsen1]

        # Match by both name and location
        matches = identify_onsen(
            mock_db,
            name="Beppu Onsen",
            latitude=33.28,
            longitude=131.50,
            limit=5,
        )

        # Should only return one match (consolidated)
        assert len(matches) == 1
        # Confidence should be averaged
        assert matches[0].match_type == "combined"
