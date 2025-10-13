"""
Integration tests for the scraper functionality.

Optimized for speed: < 2 seconds total runtime.
"""

import json
import os
from unittest.mock import patch, Mock

import pytest

from src.cli.commands.onsen.scrape_data import (
    scrape_onsen_data,
    save_data,
    process_scraped_onsen_data,
    print_summary_statistics,
)
from src.testing.mocks.mock_onsen_data import (
    get_mock_complete_entry,
    get_mock_error_entry,
    get_mock_extracted_data,
)


@pytest.fixture(scope="class")
def shared_mocks():
    """Shared mocks for all tests in the class to reduce setup overhead."""
    return {
        "complete_entry": get_mock_complete_entry(),
        "error_entry": get_mock_error_entry(),
        "extracted_data": get_mock_extracted_data(),
        "onsen_mapping": {"123": "001", "456": "002"},
    }


class TestScraperIntegration:
    """Integration tests for the scraper functionality."""

    @pytest.fixture(autouse=True)
    def setup_class_mocks(self, tmp_path, shared_mocks):  # pylint: disable=redefined-outer-name
        """Set up shared mocks for all tests to avoid repeated patching."""
        self.temp_dir = tmp_path
        self.mocks = shared_mocks

    def test_save_and_load_data(self):
        """Test saving and loading data (combined test for speed)."""
        test_data = {"test": "data", "number": 123}
        file_path = os.path.join(self.temp_dir, "test.json")

        # Test save
        save_data(test_data, file_path)
        assert os.path.exists(file_path)

        # Test load
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

    def test_process_scraped_onsen_data(self):
        """Test processing scraped onsen data (with and without errors)."""
        # Test with valid extracted data
        raw_data = {
            "onsen_id": "123",
            "url": "https://example.com",
            "extracted_data": self.mocks["extracted_data"],
        }

        result = process_scraped_onsen_data(raw_data)
        assert "mapped_data" in result
        assert "mapping_summary" in result
        assert result["mapped_data"]["name"] == "別府温泉 海地獄"
        assert result["mapped_data"]["ban_number"] == "123"
        assert result["mapping_summary"]["required_fields_present"] is True

        # Test without extracted data (error case)
        error_data = {"onsen_id": "123", "error": "Some error"}
        error_result = process_scraped_onsen_data(error_data)
        assert error_result == error_data
        assert "mapped_data" not in error_result

    def test_print_summary_statistics(self):
        """Test printing summary statistics (combined empty and populated)."""
        # Test with data
        data = {"123": self.mocks["complete_entry"], "456": self.mocks["error_entry"]}
        print_summary_statistics(data)  # Should not raise

        # Test with empty data
        print_summary_statistics({})  # Should not raise

    def test_scrape_onsen_data_flows(self):
        """Test scraping flows: full, incremental, and error handling (consolidated for speed)."""
        with patch(
            "src.cli.commands.onsen.scrape_data.setup_logging"
        ) as mock_setup, patch(
            "src.cli.commands.onsen.scrape_data.ensure_output_directory"
        ) as mock_ensure, patch(
            "src.cli.commands.onsen.scrape_data.load_existing_data"
        ) as mock_load, patch(
            "src.cli.commands.onsen.scrape_data.extract_all_onsen_mapping"
        ) as mock_extract, patch(
            "src.cli.commands.onsen.scrape_data.save_data"
        ) as mock_save, patch(
            "src.cli.commands.onsen.scrape_data.scrape_onsen_page_with_selenium"
        ) as mock_scrape, patch(
            "src.cli.commands.onsen.scrape_data.process_scraped_onsen_data"
        ) as mock_process, patch(
            "src.cli.commands.onsen.scrape_data.print_summary_statistics"
        ) as mock_print, patch(
            "src.cli.commands.onsen.scrape_data.setup_selenium_driver"
        ) as mock_driver, patch(
            "time.sleep"
        ) as mock_sleep:  # pylint: disable=unused-variable

            # Configure driver mock to return a mock driver with quit method
            mock_driver_instance = Mock()
            mock_driver_instance.quit = Mock()
            mock_driver.return_value = mock_driver_instance

            # Scenario 1: Full flow with no existing data
            mock_load.return_value = {}
            mock_extract.return_value = self.mocks["onsen_mapping"]
            mock_scrape.return_value = self.mocks["complete_entry"]
            mock_process.return_value = self.mocks["complete_entry"]

            args = Mock(fetch_mapping_only=False, scrape_individual_only=False)
            scrape_onsen_data(args)

            assert mock_setup.called and mock_ensure.called and mock_extract.called
            assert mock_scrape.call_count == 2  # Two onsens in mapping

            # Scenario 2: Incremental (skip existing)
            mock_scrape.reset_mock()
            existing_data = {"123": self.mocks["complete_entry"]}
            mock_load.return_value = existing_data

            scrape_onsen_data(args)
            assert mock_scrape.call_count == 1  # Only scrape new onsen (456)
            mock_scrape.assert_called_with("456")

            # Scenario 3: Error handling
            mock_scrape.reset_mock()
            mock_load.return_value = {}
            mock_extract.return_value = {"123": "001"}
            mock_scrape.return_value = self.mocks["error_entry"]
            mock_process.return_value = self.mocks["error_entry"]

            scrape_onsen_data(args)  # Should not raise
            assert mock_save.called and mock_print.called

    def test_coordinate_and_region_extraction(self):
        """Test coordinate and region extraction (consolidated for speed)."""
        # Test coordinate extraction
        test_data = {
            "name": "別府温泉 海地獄",
            "region": "別府",
            "ban_number": "123",
            "map_url": "https://maps.google.co.jp/maps?q=33.2797,131.5011&z=15",
            "latitude": 33.2797,
            "longitude": 131.5011,
            "住所": "大分県別府市鉄輪559-1",
        }

        result = process_scraped_onsen_data(
            {"onsen_id": "123", "extracted_data": test_data}
        )
        mapped = result["mapped_data"]

        # Check coordinates
        assert mapped["latitude"] == 33.2797
        assert mapped["longitude"] == 131.5011

        # Check region
        assert mapped["region"] == "別府"

    def test_scrape_onsen_data_flag_modes(self):
        """Test different flag modes: fetch_mapping_only, scrape_individual_only, conflicting flags."""
        with patch(
            "src.cli.commands.onsen.scrape_data.setup_logging"
        ) as mock_setup, patch(  # pylint: disable=unused-variable
            "src.cli.commands.onsen.scrape_data.ensure_output_directory"
        ) as mock_ensure, patch(  # pylint: disable=unused-variable
            "src.cli.commands.onsen.scrape_data.load_existing_data"
        ) as mock_load, patch(
            "src.cli.commands.onsen.scrape_data.extract_all_onsen_mapping"
        ) as mock_extract, patch(
            "src.cli.commands.onsen.scrape_data.save_data"
        ) as mock_save, patch(
            "src.cli.commands.onsen.scrape_data.print_summary_statistics"
        ) as mock_print, patch(
            "src.cli.commands.onsen.scrape_data.scrape_onsen_page_with_selenium"
        ) as mock_scrape, patch(
            "src.cli.commands.onsen.scrape_data.process_scraped_onsen_data"
        ) as mock_process, patch(
            "os.path.exists"
        ) as mock_exists, patch(
            "builtins.open", create=True
        ) as mock_file, patch(
            "time.sleep"
        ) as mock_sleep:  # pylint: disable=unused-variable

            # Scenario 1: fetch_mapping_only
            mock_load.return_value = {}
            mock_extract.return_value = self.mocks["onsen_mapping"]
            args = Mock(fetch_mapping_only=True, scrape_individual_only=False)
            scrape_onsen_data(args)
            assert mock_extract.called and mock_save.called
            assert not mock_print.called  # No summary for mapping only

            # Scenario 2: scrape_individual_only (with mapping file)
            mock_exists.return_value = True
            mock_file.return_value.__enter__.return_value.read.return_value = (
                '{"123": "001"}'
            )
            mock_scrape.return_value = self.mocks["complete_entry"]
            mock_process.return_value = self.mocks["complete_entry"]
            args = Mock(fetch_mapping_only=False, scrape_individual_only=True)
            scrape_onsen_data(args)
            assert mock_scrape.called and mock_print.called

            # Scenario 3: scrape_individual_only (no mapping file)
            mock_exists.return_value = False
            scrape_onsen_data(args)  # Should return early

            # Scenario 4: conflicting flags
            mock_load.reset_mock()
            args = Mock(fetch_mapping_only=True, scrape_individual_only=True)
            scrape_onsen_data(args)
            assert not mock_load.called  # Should return before loading
