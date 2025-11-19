"""Unit tests for statistics map generator."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import numpy as np

from src.lib.statistics_map_generator import StatisticsMapGenerator
from src.db.models import Onsen, OnsenVisit


class TestStatisticsMapGenerator:
    """Tests for StatisticsMapGenerator class."""

    def test_init_default_output_dir(self):
        """Test initialization with default output directory."""
        generator = StatisticsMapGenerator()
        assert generator.output_dir is not None
        assert isinstance(generator.output_dir, Path)

    def test_init_custom_output_dir(self):
        """Test initialization with custom output directory."""
        custom_dir = Path("/tmp/test_maps")
        generator = StatisticsMapGenerator(output_dir=custom_dir)
        assert generator.output_dir == custom_dir

    def test_get_visit_for_onsen_latest(self):
        """Test getting latest visit for onsen."""
        generator = StatisticsMapGenerator()
        mock_session = Mock()

        # Create mock visits
        visit1 = Mock(spec=OnsenVisit)
        visit1.visit_time = datetime(2025, 1, 1)
        visit2 = Mock(spec=OnsenVisit)
        visit2.visit_time = datetime(2025, 1, 15)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = visit2
        mock_session.query.return_value = mock_query

        result = generator._get_visit_for_onsen(mock_session, 1, "latest")

        assert result == visit2
        mock_query.filter.assert_called_once_with(OnsenVisit.onsen_id == 1)

    def test_get_visit_for_onsen_first(self):
        """Test getting first visit for onsen."""
        generator = StatisticsMapGenerator()
        mock_session = Mock()

        visit1 = Mock(spec=OnsenVisit)
        visit1.visit_time = datetime(2025, 1, 1)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = visit1
        mock_session.query.return_value = mock_query

        result = generator._get_visit_for_onsen(mock_session, 1, "first")

        assert result == visit1

    def test_get_visit_for_onsen_nth(self):
        """Test getting nth visit for onsen."""
        generator = StatisticsMapGenerator()
        mock_session = Mock()

        visit1 = Mock(spec=OnsenVisit)
        visit1.visit_time = datetime(2025, 1, 1)
        visit2 = Mock(spec=OnsenVisit)
        visit2.visit_time = datetime(2025, 1, 15)
        visit3 = Mock(spec=OnsenVisit)
        visit3.visit_time = datetime(2025, 1, 20)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            visit1,
            visit2,
            visit3,
        ]
        mock_session.query.return_value = mock_query

        # Test nth:2 (second visit)
        result = generator._get_visit_for_onsen(mock_session, 1, "nth:2")
        assert result == visit2

        # Test nth:1 (first visit)
        result = generator._get_visit_for_onsen(mock_session, 1, "nth:1")
        assert result == visit1

    def test_get_visit_for_onsen_nth_invalid(self):
        """Test nth visit with invalid number."""
        generator = StatisticsMapGenerator()
        mock_session = Mock()

        visit1 = Mock(spec=OnsenVisit)
        visit1.visit_time = datetime(2025, 1, 1)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [visit1]
        mock_session.query.return_value = mock_query

        # nth:5 when only 1 visit exists
        result = generator._get_visit_for_onsen(mock_session, 1, "nth:5")
        assert result is None

    def test_get_statistic_value(self):
        """Test extracting statistic value from visit."""
        generator = StatisticsMapGenerator()
        visit = Mock(spec=OnsenVisit)
        visit.personal_rating = 8
        visit.stay_length_minutes = 45
        visit.entry_fee_yen = 500
        visit.notes = "Some notes"  # Non-numeric, should return None

        assert generator._get_statistic_value(visit, "personal_rating") == 8.0
        assert generator._get_statistic_value(visit, "stay_length_minutes") == 45.0
        assert generator._get_statistic_value(visit, "entry_fee_yen") == 500.0
        assert generator._get_statistic_value(visit, "notes") is None
        assert generator._get_statistic_value(visit, "nonexistent") is None

    def test_calculate_bins(self):
        """Test bin calculation from values."""
        generator = StatisticsMapGenerator()

        # Test with simple values
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        bins = generator._calculate_bins(values)

        assert "min" in bins
        assert "q25" in bins
        assert "q50" in bins
        assert "q75" in bins
        assert "max" in bins
        assert bins["min"] == 1.0
        assert bins["max"] == 10.0
        assert bins["q25"] <= bins["q50"] <= bins["q75"]

    def test_calculate_bins_empty(self):
        """Test bin calculation with empty list."""
        generator = StatisticsMapGenerator()
        bins = generator._calculate_bins([])

        assert bins == {}

    def test_get_color_for_value(self):
        """Test color assignment based on bins."""
        generator = StatisticsMapGenerator()

        bins = {"min": 1.0, "q25": 3.0, "q50": 5.0, "q75": 7.0, "max": 10.0}

        # Test values in different bins
        assert generator._get_color_for_value(1.0, "test", bins) == "blue"  # <= q25
        assert generator._get_color_for_value(4.0, "test", bins) == "cyan"  # <= q50
        assert generator._get_color_for_value(6.0, "test", bins) == "green"  # <= q75
        assert generator._get_color_for_value(8.0, "test", bins) in [
            "yellow",
            "orange",
            "red",
        ]  # > q75

    def test_get_color_for_value_no_bins(self):
        """Test color assignment with no bins."""
        generator = StatisticsMapGenerator()
        color = generator._get_color_for_value(5.0, "test", {})
        assert color == "gray"

    @patch("src.lib.statistics_map_generator.folium")
    @patch("src.lib.statistics_map_generator._add_location_markers")
    def test_generate_map_basic(self, mock_add_locations, mock_folium):
        """Test basic map generation."""
        generator = StatisticsMapGenerator()
        mock_session = Mock()

        # Create mock onsen with coordinates
        mock_onsen = Mock(spec=Onsen)
        mock_onsen.id = 1
        mock_onsen.name = "Test Onsen"
        mock_onsen.latitude = 33.2794
        mock_onsen.longitude = 131.5006

        # Create mock visit
        mock_visit = Mock(spec=OnsenVisit)
        mock_visit.personal_rating = 8
        mock_visit.stay_length_minutes = 45
        mock_visit.visit_time = datetime(2025, 1, 1)
        mock_visit.entry_fee_yen = 500
        mock_visit.notes = None

        # Mock database queries
        mock_onsen_query = Mock()
        mock_onsen_query.join.return_value.filter.return_value.distinct.return_value.all.return_value = [
            mock_onsen
        ]

        mock_visit_query = Mock()
        mock_visit_query.filter.return_value.order_by.return_value.first.return_value = (
            mock_visit
        )

        def query_side_effect(model):
            if model == Onsen:
                return mock_onsen_query
            if model == OnsenVisit:
                return mock_visit_query
            return Mock()

        mock_session.query.side_effect = query_side_effect

        # Mock folium map
        mock_map = MagicMock()
        mock_folium.Map.return_value = mock_map

        # Execute
        with patch("src.lib.statistics_map_generator.np.mean", return_value=33.2794):
            result = generator.generate_map(
                session=mock_session,
                visit_selection="latest",
                show_locations=False,
            )

        # Verify
        assert result is not None
        mock_folium.Map.assert_called_once()
        mock_map.save.assert_called_once()

    @patch("src.lib.statistics_map_generator.folium")
    @patch("src.lib.statistics_map_generator._add_location_markers")
    def test_generate_map_no_visited_onsens(self, mock_add_locations, mock_folium):
        """Test map generation with no visited onsens."""
        generator = StatisticsMapGenerator()
        mock_session = Mock()

        # Mock empty query result
        mock_onsen_query = Mock()
        mock_onsen_query.join.return_value.filter.return_value.distinct.return_value.all.return_value = (
            []
        )

        mock_session.query.return_value = mock_onsen_query

        # Execute
        result = generator.generate_map(
            session=mock_session,
            visit_selection="latest",
            show_locations=False,
        )

        # Verify
        assert result is None

    def test_create_popup_html(self):
        """Test popup HTML creation."""
        generator = StatisticsMapGenerator()

        mock_onsen = Mock(spec=Onsen)
        mock_onsen.name = "Test Onsen"

        mock_visit = Mock(spec=OnsenVisit)
        mock_visit.visit_time = datetime(2025, 1, 1, 14, 30)
        mock_visit.stay_length_minutes = 45
        mock_visit.entry_fee_yen = 500
        mock_visit.notes = "Great visit!"

        statistics = {"personal_rating": 8.0, "stay_length_minutes": 45.0}

        html = generator._create_popup_html(mock_onsen, mock_visit, statistics)

        assert "Test Onsen" in html
        assert "2025-01-01 14:30" in html
        assert "45 min" in html
        assert "¥500" in html
        assert "Great visit!" in html
        assert "Personal Rating" in html
        assert "8.0/10" in html

    def test_create_legend_html(self):
        """Test legend HTML creation."""
        generator = StatisticsMapGenerator()

        bins = {"min": 1.0, "q25": 3.0, "q50": 5.0, "q75": 7.0, "max": 10.0}

        html = generator._create_legend_html("personal_rating", bins)

        assert "Personal Rating" in html
        assert "1.0" in html or "1" in html
        assert "10.0" in html or "10" in html

    def test_create_legend_html_no_bins(self):
        """Test legend HTML with no bins."""
        generator = StatisticsMapGenerator()
        html = generator._create_legend_html("personal_rating", {})
        assert html == ""

