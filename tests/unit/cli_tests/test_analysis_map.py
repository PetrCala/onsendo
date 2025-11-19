"""Unit tests for analysis map CLI command."""

from unittest.mock import Mock, patch, MagicMock
import pytest

from src.cli.commands.analysis.map import generate_statistics_map, list_statistics


class TestGenerateStatisticsMap:
    """Tests for generate_statistics_map command."""

    @patch("src.cli.commands.analysis.map.get_database_config")
    @patch("src.cli.commands.analysis.map.get_db")
    @patch("src.cli.commands.analysis.map.StatisticsMapGenerator")
    @patch("src.cli.commands.analysis.map.webbrowser")
    def test_generate_map_success(self, mock_webbrowser, mock_generator_class, mock_get_db, mock_config):
        """Test successful map generation."""
        # Setup
        mock_config.return_value.url = "sqlite:///test.db"
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_generator = MagicMock()
        mock_output_path = Mock()
        mock_output_path.absolute.return_value = "/tmp/test_map.html"
        mock_generator.generate_map.return_value = mock_output_path
        mock_generator_class.return_value = mock_generator

        # Create args
        args = Mock()
        args.env = None
        args.database = None
        args.visit_selection = "latest"
        args.no_show_locations = False
        args.output = None
        args.no_open = False

        # Execute
        result = generate_statistics_map(args)

        # Verify
        assert result == 0
        mock_generator.generate_map.assert_called_once()
        mock_webbrowser.open.assert_called_once()

    @patch("src.cli.commands.analysis.map.get_database_config")
    @patch("src.cli.commands.analysis.map.get_db")
    @patch("src.cli.commands.analysis.map.StatisticsMapGenerator")
    def test_generate_map_no_open(self, mock_generator_class, mock_get_db, mock_config):
        """Test map generation without opening browser."""
        # Setup
        mock_config.return_value.url = "sqlite:///test.db"
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_generator = MagicMock()
        mock_output_path = Mock()
        mock_generator.generate_map.return_value = mock_output_path
        mock_generator_class.return_value = mock_generator

        # Create args
        args = Mock()
        args.env = None
        args.database = None
        args.visit_selection = "latest"
        args.no_show_locations = False
        args.output = None
        args.no_open = True

        # Execute
        with patch("src.cli.commands.analysis.map.webbrowser") as mock_webbrowser:
            result = generate_statistics_map(args)

            # Verify
            assert result == 0
            mock_webbrowser.open.assert_not_called()

    @patch("src.cli.commands.analysis.map.get_database_config")
    def test_generate_map_invalid_visit_selection(self, mock_config):
        """Test map generation with invalid visit selection."""
        # Setup
        mock_config.return_value.url = "sqlite:///test.db"

        # Create args with invalid selection
        args = Mock()
        args.env = None
        args.database = None
        args.visit_selection = "invalid"
        args.no_show_locations = False
        args.output = None
        args.no_open = False

        # Execute
        result = generate_statistics_map(args)

        # Verify
        assert result == 1

    @patch("src.cli.commands.analysis.map.get_database_config")
    def test_generate_map_invalid_nth(self, mock_config):
        """Test map generation with invalid nth format."""
        # Setup
        mock_config.return_value.url = "sqlite:///test.db"

        # Create args with invalid nth
        args = Mock()
        args.env = None
        args.database = None
        args.visit_selection = "nth:0"  # Invalid: must be >= 1
        args.no_show_locations = False
        args.output = None
        args.no_open = False

        # Execute
        result = generate_statistics_map(args)

        # Verify
        assert result == 1

    @patch("src.cli.commands.analysis.map.get_database_config")
    @patch("src.cli.commands.analysis.map.get_db")
    @patch("src.cli.commands.analysis.map.StatisticsMapGenerator")
    def test_generate_map_failure(self, mock_generator_class, mock_get_db, mock_config):
        """Test map generation failure handling."""
        # Setup
        mock_config.return_value.url = "sqlite:///test.db"
        mock_session = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_session

        mock_generator = MagicMock()
        mock_generator.generate_map.return_value = None  # Failure
        mock_generator_class.return_value = mock_generator

        # Create args
        args = Mock()
        args.env = None
        args.database = None
        args.visit_selection = "latest"
        args.no_show_locations = False
        args.output = None
        args.no_open = False

        # Execute
        result = generate_statistics_map(args)

        # Verify
        assert result == 1


class TestListStatistics:
    """Tests for list_statistics command."""

    @patch("src.cli.commands.analysis.map.StatisticsRegistry")
    def test_list_statistics(self, mock_registry_class):
        """Test listing statistics."""
        # Setup
        mock_registry = MagicMock()
        mock_stat = {
            "field_name": "personal_rating",
            "display_name": "Personal Rating",
            "type": "rating",
            "description": "Overall personal rating (1-10)",
        }
        mock_registry.get_all_statistics.return_value = [mock_stat]
        mock_registry_class.return_value = mock_registry

        # Create args
        args = Mock()

        # Execute
        result = list_statistics(args)

        # Verify
        assert result == 0
        mock_registry.get_all_statistics.assert_called_once()

