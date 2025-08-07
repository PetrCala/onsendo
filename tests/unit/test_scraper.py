"""
Unit tests for the scraper functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.cli.commands.scrape_onsen_data.scraper import (
    setup_selenium_driver,
    find_all_onsen_divs,
    is_onsen_div,
    extract_onsen_data_from_div,
    extract_all_onsen_mapping,
    scrape_onsen_page_with_selenium,
    extract_detailed_onsen_data,
    extract_table_data,
)
from src.testing.mocks.mock_onsen_data import (
    get_mock_onsen_mapping,
    get_mock_extracted_data,
    get_mock_onsen_detail_html,
)


class TestScraper:
    """Test cases for scraper functionality."""

    @patch("src.cli.commands.scrape_onsen_data.scraper.Options")
    @patch("src.cli.commands.scrape_onsen_data.scraper.webdriver")
    def test_setup_selenium_driver(self, mock_webdriver, mock_options):
        """Test setting up Selenium driver."""
        mock_options_instance = Mock()
        mock_options.return_value = mock_options_instance
        mock_driver = Mock()
        mock_webdriver.Chrome.return_value = mock_driver

        result = setup_selenium_driver()

        # Check that options were configured
        mock_options_instance.add_argument.assert_called()
        assert (
            mock_options_instance.add_argument.call_count >= 5
        )  # Multiple arguments added

        # Check that Chrome driver was created
        mock_webdriver.Chrome.assert_called_once_with(options=mock_options_instance)
        assert result == mock_driver

    def test_find_all_onsen_divs_success(self, mock_selenium_driver):
        """Test finding all onsen divs successfully."""
        result = find_all_onsen_divs(mock_selenium_driver)

        # Should find the mock divs we created
        assert len(result) == 2
        assert all(hasattr(div, "get_attribute") for div in result)

    def test_find_all_onsen_divs_timeout(self, mock_selenium_driver):
        """Test finding onsen divs with timeout error."""
        # Mock timeout exception
        mock_selenium_driver.find_element.side_effect = TimeoutException("Timeout")

        result = find_all_onsen_divs(mock_selenium_driver)

        assert result == []

    def test_find_all_onsen_divs_exception(self, mock_selenium_driver):
        """Test finding onsen divs with general exception."""
        # Mock general exception
        mock_selenium_driver.find_element.side_effect = Exception("General error")

        result = find_all_onsen_divs(mock_selenium_driver)

        assert result == []

    def test_is_onsen_div_valid(self, mock_selenium_driver):
        """Test checking if a div is a valid onsen div."""
        # Create a mock div with the required structure
        mock_div = Mock()
        mock_span = Mock()
        mock_onclick = Mock()

        mock_div.find_elements.side_effect = lambda xpath: {
            ".//span": [mock_span],
            ".//*[@onclick]": [mock_onclick],
        }.get(xpath, [])

        result = is_onsen_div(mock_div)

        assert result is True

    def test_is_onsen_div_invalid(self, mock_selenium_driver):
        """Test checking if a div is not a valid onsen div."""
        # Create a mock div without the required structure
        mock_div = Mock()
        mock_div.find_elements.return_value = []

        result = is_onsen_div(mock_div)

        assert result is False

    def test_is_onsen_div_exception(self, mock_selenium_driver):
        """Test checking onsen div with exception."""
        mock_div = Mock()
        mock_div.find_elements.side_effect = Exception("Error")

        result = is_onsen_div(mock_div)

        assert result is False

    def test_extract_onsen_data_from_div_success(self):
        """Test extracting onsen data from a div successfully."""
        # Create a mock table with the required structure
        mock_table = Mock()
        mock_ban_span = Mock()
        mock_ban_span.text = "001"
        mock_onclick_div = Mock()
        mock_onclick_div.get_attribute.return_value = "details(123)"

        # Mock the table structure
        mock_ban_cell = Mock()
        mock_ban_cell.find_elements.return_value = [mock_ban_span]
        mock_onclick_cell = Mock()
        mock_onclick_cell.find_elements.return_value = [mock_onclick_div]

        mock_row1 = Mock()
        mock_row1.find_elements.return_value = [mock_ban_cell]
        mock_row2 = Mock()
        mock_row2.find_elements.return_value = [mock_onclick_cell]

        mock_table.find_elements.return_value = [mock_row1, mock_row2]

        result = extract_onsen_data_from_div(mock_table)

        assert result == {"123": "001"}

    def test_extract_onsen_data_from_div_no_ban(self):
        """Test extracting onsen data when ban number is missing."""
        mock_table = Mock()
        mock_table.find_elements.return_value = []

        result = extract_onsen_data_from_div(mock_table)

        assert result == {}

    def test_extract_onsen_data_from_div_no_onclick(self):
        """Test extracting onsen data when onclick is missing."""
        mock_table = Mock()
        mock_ban_span = Mock()
        mock_ban_span.text = "001"
        mock_ban_cell = Mock()
        mock_ban_cell.find_elements.return_value = [mock_ban_span]

        mock_row = Mock()
        mock_row.find_elements.return_value = [mock_ban_cell]

        mock_table.find_elements.return_value = [mock_row]

        result = extract_onsen_data_from_div(mock_table)

        assert result == {}

    def test_extract_all_onsen_mapping_success(self, mock_selenium_driver):
        """Test extracting all onsen mappings successfully."""
        result = extract_all_onsen_mapping(mock_selenium_driver)

        # Should extract the mock mappings
        assert isinstance(result, dict)
        assert len(result) > 0

    @patch("src.cli.commands.scrape_onsen_data.scraper.setup_selenium_driver")
    @patch("src.cli.commands.scrape_onsen_data.scraper.extract_detailed_onsen_data")
    def test_scrape_onsen_page_with_selenium_success(
        self, mock_extract_data, mock_setup_driver
    ):
        """Test scraping individual onsen page successfully."""
        # Setup mocks
        mock_driver = Mock()
        mock_setup_driver.return_value = mock_driver
        mock_extract_data.return_value = get_mock_extracted_data()

        result = scrape_onsen_page_with_selenium("123")

        # Check that driver was used correctly
        mock_driver.get.assert_called_once()
        mock_driver.quit.assert_called_once()

        # Check result structure
        assert result["onsen_id"] == "123"
        assert "url" in result
        assert "raw_html" in result
        assert "extracted_data" in result

    @patch("src.cli.commands.scrape_onsen_data.scraper.setup_selenium_driver")
    def test_scrape_onsen_page_with_selenium_error(self, mock_setup_driver):
        """Test scraping individual onsen page with error."""
        # Setup mock to raise exception
        mock_driver = Mock()
        mock_driver.get.side_effect = Exception("Scraping error")
        mock_setup_driver.return_value = mock_driver

        result = scrape_onsen_page_with_selenium("123")

        # Check error result structure
        assert result["onsen_id"] == "123"
        assert "error" in result
        assert result["error"] == "Scraping error"
        assert result["extracted_data"] == {}

        # Check that driver was cleaned up
        mock_driver.quit.assert_called_once()

    def test_extract_detailed_onsen_data_success(self, mock_selenium_driver):
        """Test extracting detailed onsen data successfully."""
        result = extract_detailed_onsen_data(mock_selenium_driver)

        # Check that all expected fields are extracted
        assert "name" in result
        assert "ban_number_and_name" in result
        assert "latitude" in result
        assert "longitude" in result
        assert "map_url" in result

        # Check specific values
        assert result["name"] == "別府温泉 海地獄"
        assert result["ban_number_and_name"] == "123 別府温泉 海地獄"
        assert result["latitude"] == 33.2797
        assert result["longitude"] == 131.5011

    def test_extract_detailed_onsen_data_missing_name(self, mock_selenium_driver):
        """Test extracting detailed data when name is missing."""

        # Mock missing name element
        def mock_find_element(by, value):
            if by == By.XPATH and value == "/html/body/div[2]":
                raise NoSuchElementException("Element not found")
            # Return other elements normally
            element = Mock()
            if by == By.XPATH and value == "/html/body/div[3]":
                element.text = "123 温泉名"
            elif by == By.XPATH and value == "/html/body/div[4]/iframe":
                element.get_attribute.return_value = (
                    "https://maps.google.co.jp/maps?q=33.2797,131.5011&z=15"
                )
            return element

        mock_selenium_driver.find_element.side_effect = mock_find_element

        result = extract_detailed_onsen_data(mock_selenium_driver)

        assert result["name"] == ""

    def test_extract_detailed_onsen_data_missing_coordinates(
        self, mock_selenium_driver
    ):
        """Test extracting detailed data when coordinates are missing."""

        # Mock missing iframe
        def mock_find_element(by, value):
            if by == By.XPATH and value == "/html/body/div[4]/iframe":
                raise NoSuchElementException("Element not found")
            # Return other elements normally
            element = Mock()
            if by == By.XPATH and value == "/html/body/div[2]":
                element.text = "温泉名"
            elif by == By.XPATH and value == "/html/body/div[3]":
                element.text = "123 温泉名"
            return element

        mock_selenium_driver.find_element.side_effect = mock_find_element

        result = extract_detailed_onsen_data(mock_selenium_driver)

        assert result["latitude"] is None
        assert result["longitude"] is None
        assert result["map_url"] == ""

    def test_extract_table_data_success(self):
        """Test extracting table data successfully."""
        # Create mock table with rows
        mock_table = Mock()

        # Create mock rows with key-value pairs
        mock_rows = []
        table_data = {
            "住所": "大分県別府市鉄輪559-1",
            "電話": "0977-66-1577",
            "営業形態": "日帰り入浴",
        }

        for key, value in table_data.items():
            mock_row = Mock()
            mock_key_cell = Mock()
            mock_key_cell.text = key
            mock_value_cell = Mock()
            mock_value_cell.text = value
            mock_row.find_elements.return_value = [mock_key_cell, mock_value_cell]
            mock_rows.append(mock_row)

        mock_table.find_elements.return_value = mock_rows

        result = extract_table_data(mock_table)

        # Check that all data was extracted
        for key, value in table_data.items():
            assert result[key] == value

    def test_extract_table_data_empty_table(self):
        """Test extracting table data from empty table."""
        mock_table = Mock()
        mock_table.find_elements.return_value = []

        result = extract_table_data(mock_table)

        assert result == {}

    def test_extract_table_data_malformed_rows(self):
        """Test extracting table data with malformed rows."""
        mock_table = Mock()

        # Create rows with insufficient cells
        mock_row1 = Mock()
        mock_row1.find_elements.return_value = [Mock()]  # Only one cell
        mock_row2 = Mock()
        mock_row2.find_elements.return_value = []  # No cells

        mock_table.find_elements.return_value = [mock_row1, mock_row2]

        result = extract_table_data(mock_table)

        assert result == {}

    def test_extract_table_data_empty_cells(self):
        """Test extracting table data with empty cells."""
        mock_table = Mock()

        # Create row with empty cells
        mock_row = Mock()
        mock_key_cell = Mock()
        mock_key_cell.text = ""
        mock_value_cell = Mock()
        mock_value_cell.text = ""
        mock_row.find_elements.return_value = [mock_key_cell, mock_value_cell]

        mock_table.find_elements.return_value = [mock_row]

        result = extract_table_data(mock_table)

        assert result == {}

    def test_extract_table_data_exception(self):
        """Test extracting table data with exception."""
        mock_table = Mock()
        mock_table.find_elements.side_effect = Exception("Table error")

        result = extract_table_data(mock_table)

        assert result == {}
