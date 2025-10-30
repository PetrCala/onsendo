"""Unit tests for map generator with location markers."""

from unittest.mock import Mock, patch, MagicMock, call
import pytest

from src.lib.map_generator import (
    _add_location_markers,
    generate_recommendation_map,
    generate_all_onsens_map,
)


class TestAddLocationMarkers:
    """Tests for _add_location_markers helper function."""

    def test_no_locations_in_database(self):
        """Test that function handles empty location list gracefully."""
        # Setup
        mock_map = Mock()
        mock_session = Mock()
        mock_session.query.return_value.all.return_value = []

        # Execute
        _add_location_markers(mock_map, mock_session, reference_location_id=None)

        # Verify
        mock_session.query.assert_called_once()
        # No markers should be added
        assert not mock_map.method_calls  # map should not have any method calls

    def test_single_location_no_reference(self):
        """Test adding a single location without reference."""
        # Setup
        mock_map = Mock()
        mock_session = Mock()

        mock_location = Mock()
        mock_location.id = 1
        mock_location.name = "Home"
        mock_location.latitude = 33.2794
        mock_location.longitude = 131.5006
        mock_location.description = "My home location"

        mock_session.query.return_value.all.return_value = [mock_location]

        with patch('src.lib.map_generator.folium') as mock_folium, \
             patch('src.lib.map_generator.IFrame'):
            # Execute
            _add_location_markers(mock_map, mock_session, reference_location_id=None)

            # Verify
            mock_session.query.assert_called_once()
            # Should create one marker with pink color
            mock_folium.Icon.assert_called_once()
            call_kwargs = mock_folium.Icon.call_args[1]
            assert call_kwargs['color'] == 'pink'
            assert call_kwargs['icon'] == 'home'

    def test_single_location_with_reference(self):
        """Test adding a single location that is the reference location."""
        # Setup
        mock_map = Mock()
        mock_session = Mock()

        mock_location = Mock()
        mock_location.id = 1
        mock_location.name = "Home"
        mock_location.latitude = 33.2794
        mock_location.longitude = 131.5006
        mock_location.description = "My home location"

        mock_session.query.return_value.all.return_value = [mock_location]

        with patch('src.lib.map_generator.folium') as mock_folium, \
             patch('src.lib.map_generator.IFrame'):
            # Execute
            _add_location_markers(mock_map, mock_session, reference_location_id=1)

            # Verify
            # Should create one marker with red color (reference)
            mock_folium.Icon.assert_called_once()
            call_kwargs = mock_folium.Icon.call_args[1]
            assert call_kwargs['color'] == 'red'
            assert call_kwargs['icon'] == 'home'

    def test_multiple_locations_with_reference(self):
        """Test adding multiple locations with one as reference."""
        # Setup
        mock_map = Mock()
        mock_session = Mock()

        mock_location1 = Mock()
        mock_location1.id = 1
        mock_location1.name = "Home"
        mock_location1.latitude = 33.2794
        mock_location1.longitude = 131.5006
        mock_location1.description = "Home"

        mock_location2 = Mock()
        mock_location2.id = 2
        mock_location2.name = "Work"
        mock_location2.latitude = 33.2800
        mock_location2.longitude = 131.5010
        mock_location2.description = "Work"

        mock_session.query.return_value.all.return_value = [mock_location1, mock_location2]

        with patch('src.lib.map_generator.folium') as mock_folium, \
             patch('src.lib.map_generator.IFrame'):
            # Execute
            _add_location_markers(mock_map, mock_session, reference_location_id=1)

            # Verify
            # Should create two markers
            assert mock_folium.Icon.call_count == 2

            # First should be red (reference)
            first_call_kwargs = mock_folium.Icon.call_args_list[0][1]
            assert first_call_kwargs['color'] == 'red'

            # Second should be pink
            second_call_kwargs = mock_folium.Icon.call_args_list[1][1]
            assert second_call_kwargs['color'] == 'pink'

    def test_location_without_coordinates_skipped(self):
        """Test that locations without coordinates are skipped."""
        # Setup
        mock_map = Mock()
        mock_session = Mock()

        mock_location1 = Mock()
        mock_location1.id = 1
        mock_location1.name = "Invalid"
        mock_location1.latitude = None  # Missing latitude
        mock_location1.longitude = 131.5006
        mock_location1.description = None

        mock_location2 = Mock()
        mock_location2.id = 2
        mock_location2.name = "Valid"
        mock_location2.latitude = 33.2800
        mock_location2.longitude = 131.5010
        mock_location2.description = "Valid location"

        mock_session.query.return_value.all.return_value = [mock_location1, mock_location2]

        with patch('src.lib.map_generator.folium') as mock_folium, \
             patch('src.lib.map_generator.IFrame'):
            # Execute
            _add_location_markers(mock_map, mock_session, reference_location_id=None)

            # Verify
            # Should only create one marker (for valid location)
            assert mock_folium.Icon.call_count == 1

    def test_database_error_handled_gracefully(self):
        """Test that database errors are handled without crashing."""
        # Setup
        mock_map = Mock()
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")

        # Execute - should not raise
        _add_location_markers(mock_map, mock_session, reference_location_id=None)

        # Verify function completed without error
        assert True  # If we reach here, error was handled


class TestGenerateRecommendationMap:
    """Tests for generate_recommendation_map function."""

    @patch('src.lib.map_generator.os.makedirs')
    @patch('src.lib.map_generator.folium')
    @patch('src.lib.map_generator._add_location_markers')
    def test_show_locations_true_calls_helper(self, mock_add_locations, mock_folium, mock_makedirs):
        """Test that show_locations=True calls the helper function."""
        # Setup
        mock_location = Mock()
        mock_location.id = 1
        mock_location.name = "Home"
        mock_location.latitude = 33.2794
        mock_location.longitude = 131.5006

        mock_db_session = Mock()
        recommendations = []  # Empty list is fine for this test

        mock_map = Mock()
        mock_folium.Map.return_value = mock_map

        # Execute
        generate_recommendation_map(
            recommendations,
            mock_location,
            mock_db_session,
            show_locations=True
        )

        # Verify
        mock_add_locations.assert_called_once()
        # Check it was called with correct reference location
        call_args = mock_add_locations.call_args
        assert call_args[0][0] == mock_map  # First arg is the map
        assert call_args[0][1] == mock_db_session  # Second arg is db_session
        assert call_args[1]['reference_location_id'] == 1  # Keyword arg

    @patch('src.lib.map_generator.os.makedirs')
    @patch('src.lib.map_generator.folium')
    @patch('src.lib.map_generator._add_location_markers')
    def test_show_locations_false_skips_helper(self, mock_add_locations, mock_folium, mock_makedirs):
        """Test that show_locations=False does not call the helper function."""
        # Setup
        mock_location = Mock()
        mock_location.id = 1
        mock_location.name = "Home"
        mock_location.latitude = 33.2794
        mock_location.longitude = 131.5006

        mock_db_session = Mock()
        recommendations = []

        mock_map = Mock()
        mock_folium.Map.return_value = mock_map

        # Execute
        generate_recommendation_map(
            recommendations,
            mock_location,
            mock_db_session,
            show_locations=False
        )

        # Verify
        mock_add_locations.assert_not_called()


class TestGenerateAllOnsensMap:
    """Tests for generate_all_onsens_map function."""

    @patch('src.lib.map_generator.os.makedirs')
    @patch('src.lib.map_generator.folium')
    @patch('src.lib.map_generator._add_location_markers')
    def test_show_locations_true_calls_helper(self, mock_add_locations, mock_folium, mock_makedirs):
        """Test that show_locations=True calls the helper function."""
        # Setup
        mock_db_session = Mock()
        mock_db_session.query.return_value.distinct.return_value.all.return_value = []

        onsens = []  # Empty list is fine for this test

        mock_map = Mock()
        mock_folium.Map.return_value = mock_map

        # Execute
        generate_all_onsens_map(
            onsens,
            mock_db_session,
            show_locations=True
        )

        # Verify
        mock_add_locations.assert_called_once()
        # Check it was called with no reference location
        call_args = mock_add_locations.call_args
        assert call_args[0][0] == mock_map  # First arg is the map
        assert call_args[0][1] == mock_db_session  # Second arg is db_session
        assert call_args[1]['reference_location_id'] is None  # No reference

    @patch('src.lib.map_generator.os.makedirs')
    @patch('src.lib.map_generator.folium')
    @patch('src.lib.map_generator._add_location_markers')
    def test_show_locations_false_skips_helper(self, mock_add_locations, mock_folium, mock_makedirs):
        """Test that show_locations=False does not call the helper function."""
        # Setup
        mock_db_session = Mock()
        mock_db_session.query.return_value.distinct.return_value.all.return_value = []

        onsens = []

        mock_map = Mock()
        mock_folium.Map.return_value = mock_map

        # Execute
        generate_all_onsens_map(
            onsens,
            mock_db_session,
            show_locations=False
        )

        # Verify
        mock_add_locations.assert_not_called()
