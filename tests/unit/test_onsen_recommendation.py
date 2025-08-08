"""
Unit tests for onsen recommendation functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from src.lib.recommendation import OnsenRecommendationEngine
from src.db.models import Location, Onsen, OnsenVisit
from src.lib.distance import DistanceMilestones


class TestOnsenRecommendationEngine:
    """Test the OnsenRecommendationEngine class."""

    def test_engine_initialization_without_location(self):
        """Test engine initialization without location."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        assert engine.db_session == mock_session
        assert engine.location is None
        assert engine._distance_milestones is None

    def test_engine_initialization_with_location(self):
        """Test engine initialization with location."""
        mock_session = Mock(spec=Session)
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503

        with patch("src.lib.recommendation.calculate_location_milestones") as mock_calc:
            mock_calc.return_value = DistanceMilestones(1.0, 3.0, 5.0, 5.0)

            engine = OnsenRecommendationEngine(mock_session, location)

        assert engine.db_session == mock_session
        assert engine.location == location
        assert engine._distance_milestones is not None

    def test_update_location(self):
        """Test updating the engine's location."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        location = Mock(spec=Location)
        location.name = "New Location"
        location.latitude = 35.6762
        location.longitude = 139.6503

        with patch("src.lib.recommendation.calculate_location_milestones") as mock_calc:
            mock_calc.return_value = DistanceMilestones(1.0, 3.0, 5.0, 5.0)

            engine.update_location(location)

        assert engine.location == location
        assert engine._distance_milestones is not None

    def test_get_distance_milestones(self):
        """Test getting distance milestones."""
        mock_session = Mock(spec=Session)
        location = Mock(spec=Location)

        milestones = DistanceMilestones(1.0, 3.0, 5.0, 5.0)

        with patch("src.lib.recommendation.calculate_location_milestones") as mock_calc:
            mock_calc.return_value = milestones
            engine = OnsenRecommendationEngine(mock_session, location)

        result = engine.get_distance_milestones()
        assert result == milestones

    def test_print_distance_milestones_with_milestones(self, capsys):
        """Test printing distance milestones when available."""
        mock_session = Mock(spec=Session)
        location = Mock(spec=Location)
        location.name = "Test Location"

        milestones = DistanceMilestones(1.0, 3.0, 5.0, 5.0)

        with patch("src.lib.recommendation.calculate_location_milestones") as mock_calc:
            mock_calc.return_value = milestones
            engine = OnsenRecommendationEngine(mock_session, location)

        engine.print_distance_milestones()
        captured = capsys.readouterr()

        assert "Test Location" in captured.out
        assert "Very Close: <= 1.00 km" in captured.out
        assert "Close:      <= 3.00 km" in captured.out
        assert "Medium:     <= 5.00 km" in captured.out
        assert "Far:        >  5.00 km" in captured.out

    def test_print_distance_milestones_without_milestones(self, capsys):
        """Test printing distance milestones when not available."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        engine.print_distance_milestones()
        captured = capsys.readouterr()

        assert "No distance milestones calculated" in captured.out

    def test_get_distance_category_name_with_milestones(self):
        """Test distance category name determination with milestones."""
        mock_session = Mock(spec=Session)
        location = Mock(spec=Location)

        milestones = DistanceMilestones(1.0, 3.0, 5.0, 5.0)

        with patch("src.lib.recommendation.calculate_location_milestones") as mock_calc:
            mock_calc.return_value = milestones
            engine = OnsenRecommendationEngine(mock_session, location)

        assert engine._get_distance_category_name(0.5) == "very_close"
        assert engine._get_distance_category_name(2.0) == "close"
        assert engine._get_distance_category_name(4.0) == "medium"
        assert engine._get_distance_category_name(6.0) == "far"

    def test_get_distance_category_name_without_milestones(self):
        """Test distance category name determination without milestones."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        # Should use default categories
        assert engine._get_distance_category_name(0.5) == "very_close"
        assert engine._get_distance_category_name(10.0) == "close"
        assert engine._get_distance_category_name(30.0) == "medium"
        assert engine._get_distance_category_name(100.0) == "far"

    def test_has_been_visited_true(self):
        """Test checking if onsen has been visited (true case)."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        onsen = Mock(spec=Onsen)
        onsen.id = 1

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = Mock()
        mock_session.query.return_value = mock_query

        result = engine._has_been_visited(onsen)
        assert result == True

    def test_has_been_visited_false(self):
        """Test checking if onsen has been visited (false case)."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        onsen = Mock(spec=Onsen)
        onsen.id = 1

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        result = engine._has_been_visited(onsen)
        assert result == False

    def test_get_unvisited_onsens(self):
        """Test filtering out visited onsens."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        # Create mock onsens
        onsens = []
        for i in range(5):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsens.append(onsen)

        # Mock visited onsen IDs
        mock_query = Mock()
        mock_query.distinct.return_value.all.return_value = [
            (1,),
            (3,),
        ]  # IDs 1 and 3 visited
        mock_session.query.return_value = mock_query

        result = engine.get_unvisited_onsens(onsens)

        # Should return onsens with IDs 2, 4, 5
        assert len(result) == 3
        assert result[0].id == 2
        assert result[1].id == 4
        assert result[2].id == 5

    def test_get_location_by_name_or_id_by_id(self):
        """Test getting location by ID."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        location = Mock(spec=Location)
        location.id = 1
        location.name = "Test Location"

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = location
        mock_session.query.return_value = mock_query

        result = engine.get_location_by_name_or_id("1")
        assert result == location

    def test_get_location_by_name_or_id_by_name(self):
        """Test getting location by name."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        location = Mock(spec=Location)
        location.id = 1
        location.name = "Test Location"

        # Mock the query to return None for ID lookup, then location for name lookup
        mock_query = Mock()
        mock_query.filter.return_value.first.side_effect = [None, location]
        mock_session.query.return_value = mock_query

        result = engine.get_location_by_name_or_id("Test Location")
        assert result == location

    def test_get_location_by_name_or_id_not_found(self):
        """Test getting location that doesn't exist."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        result = engine.get_location_by_name_or_id("Nonexistent")
        assert result is None

    def test_list_locations(self):
        """Test listing all locations."""
        mock_session = Mock(spec=Session)
        engine = OnsenRecommendationEngine(mock_session)

        locations = [
            Mock(spec=Location, name="Location A"),
            Mock(spec=Location, name="Location B"),
            Mock(spec=Location, name="Location C"),
        ]

        mock_query = Mock()
        mock_query.order_by.return_value.all.return_value = locations
        mock_session.query.return_value = mock_query

        result = engine.list_locations()
        assert result == locations


class TestRecommendOnsens:
    """Test onsen recommendation functionality."""

    def test_recommend_onsens_basic(self):
        """Test basic onsen recommendation."""
        mock_session = Mock(spec=Session)
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503

        # Create mock onsens
        onsens = []
        for i in range(3):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsen.name = f"Onsen {i+1}"
            onsen.latitude = 35.6762 + (i * 0.001)
            onsen.longitude = 139.6503
            onsens.append(onsen)

        mock_query = Mock()
        mock_query.all.return_value = onsens
        mock_session.query.return_value = mock_query

        milestones = DistanceMilestones(1.0, 3.0, 5.0, 5.0)

        with patch("src.lib.recommendation.calculate_location_milestones") as mock_calc:
            mock_calc.return_value = milestones
            engine = OnsenRecommendationEngine(mock_session, location)

        with patch("src.lib.recommendation.filter_onsens_by_distance") as mock_filter:
            mock_filter.return_value = [(onsens[0], 0.5), (onsens[1], 2.0)]

            with patch.object(engine, "_is_onsen_available") as mock_available:
                mock_available.return_value = True

                recommendations = engine.recommend_onsens(
                    location=location,
                    distance_category="close",
                    exclude_closed=False,
                    exclude_visited=False,
                )

        assert len(recommendations) == 2
        assert recommendations[0][0] == onsens[0]  # First onsen
        assert recommendations[0][1] == 0.5  # Distance
        assert "distance_category" in recommendations[0][2]  # Metadata

    def test_recommend_onsens_with_limit(self):
        """Test onsen recommendation with limit."""
        mock_session = Mock(spec=Session)
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503

        # Create mock onsens
        onsens = []
        for i in range(5):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsen.name = f"Onsen {i+1}"
            onsen.latitude = 35.6762 + (i * 0.001)
            onsen.longitude = 139.6503
            onsens.append(onsen)

        mock_query = Mock()
        mock_query.all.return_value = onsens
        mock_session.query.return_value = mock_query

        milestones = DistanceMilestones(1.0, 3.0, 5.0, 5.0)

        with patch("src.lib.recommendation.calculate_location_milestones") as mock_calc:
            mock_calc.return_value = milestones
            engine = OnsenRecommendationEngine(mock_session, location)

        with patch("src.lib.recommendation.filter_onsens_by_distance") as mock_filter:
            mock_filter.return_value = [
                (onsen, i * 0.5) for i, onsen in enumerate(onsens)
            ]

            with patch.object(engine, "_is_onsen_available") as mock_available:
                mock_available.return_value = True

                recommendations = engine.recommend_onsens(
                    location=location,
                    distance_category="close",
                    exclude_closed=False,
                    exclude_visited=False,
                    limit=3,
                )

        assert len(recommendations) == 3

    def test_recommend_onsens_exclude_closed(self):
        """Test onsen recommendation with closed onsens excluded."""
        mock_session = Mock(spec=Session)
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503

        # Create mock onsens
        onsens = []
        for i in range(3):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsen.name = f"Onsen {i+1}"
            onsen.latitude = 35.6762 + (i * 0.001)
            onsen.longitude = 139.6503
            onsens.append(onsen)

        mock_query = Mock()
        mock_query.all.return_value = onsens
        mock_session.query.return_value = mock_query

        milestones = DistanceMilestones(1.0, 3.0, 5.0, 5.0)

        with patch("src.lib.recommendation.calculate_location_milestones") as mock_calc:
            mock_calc.return_value = milestones
            engine = OnsenRecommendationEngine(mock_session, location)

        with patch.object(engine, "get_available_onsens") as mock_available:
            mock_available.return_value = [
                onsens[0],
                onsens[2],
            ]  # Only first and third available

            with patch(
                "src.lib.recommendation.filter_onsens_by_distance"
            ) as mock_filter:
                mock_filter.return_value = [(onsens[0], 0.5), (onsens[2], 2.0)]

                recommendations = engine.recommend_onsens(
                    location=location,
                    distance_category="close",
                    exclude_closed=True,
                    exclude_visited=False,
                )

        assert len(recommendations) == 2
        assert recommendations[0][0] == onsens[0]
        assert recommendations[1][0] == onsens[2]

    def test_recommend_onsens_exclude_visited(self):
        """Test onsen recommendation with visited onsens excluded."""
        mock_session = Mock(spec=Session)
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503

        # Create mock onsens
        onsens = []
        for i in range(3):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsen.name = f"Onsen {i+1}"
            onsen.latitude = 35.6762 + (i * 0.001)
            onsen.longitude = 139.6503
            onsens.append(onsen)

        mock_query = Mock()
        mock_query.all.return_value = onsens
        mock_session.query.return_value = mock_query

        milestones = DistanceMilestones(1.0, 3.0, 5.0, 5.0)

        with patch("src.lib.recommendation.calculate_location_milestones") as mock_calc:
            mock_calc.return_value = milestones
            engine = OnsenRecommendationEngine(mock_session, location)

        with patch.object(engine, "get_unvisited_onsens") as mock_unvisited:
            mock_unvisited.return_value = [
                onsens[0],
                onsens[2],
            ]  # Only first and third unvisited

            with patch(
                "src.lib.recommendation.filter_onsens_by_distance"
            ) as mock_filter:
                mock_filter.return_value = [(onsens[0], 0.5), (onsens[2], 2.0)]

                recommendations = engine.recommend_onsens(
                    location=location,
                    distance_category="close",
                    exclude_closed=False,
                    exclude_visited=True,
                )

        assert len(recommendations) == 2
        assert recommendations[0][0] == onsens[0]
        assert recommendations[1][0] == onsens[2]

    def test_recommend_onsens_metadata(self):
        """Test that recommendations include proper metadata."""
        mock_session = Mock(spec=Session)
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503

        onsen = Mock(spec=Onsen)
        onsen.id = 1
        onsen.name = "Test Onsen"
        onsen.latitude = 35.6762 + 0.001
        onsen.longitude = 139.6503

        mock_query = Mock()
        mock_query.all.return_value = [onsen]
        mock_session.query.return_value = mock_query

        milestones = DistanceMilestones(1.0, 3.0, 5.0, 5.0)

        with patch("src.lib.recommendation.calculate_location_milestones") as mock_calc:
            mock_calc.return_value = milestones
            engine = OnsenRecommendationEngine(mock_session, location)

        with patch("src.lib.recommendation.filter_onsens_by_distance") as mock_filter:
            mock_filter.return_value = [(onsen, 0.5)]

            with patch.object(engine, "_has_been_visited") as mock_visited:
                mock_visited.return_value = False

                recommendations = engine.recommend_onsens(
                    location=location,
                    distance_category="very_close",
                    exclude_closed=False,
                    exclude_visited=False,
                )

        assert len(recommendations) == 1
        metadata = recommendations[0][2]

        assert "distance_category" in metadata
        assert "is_available" in metadata
        assert "has_been_visited" in metadata
        assert metadata["distance_category"] == "very_close"
        assert metadata["is_available"] == True
        assert metadata["has_been_visited"] == False
