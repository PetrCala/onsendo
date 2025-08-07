"""
Fixtures for the project.
"""

import json
import os
import tempfile
from typing import Dict, Any
from unittest.mock import Mock, patch

import pytest
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from src.types import CustomStrEnum
from src.testing.mocks import get_mock_db
from src.testing.mocks.mock_onsen_data import (
    get_mock_complete_entry,
    get_mock_error_entry,
    get_mock_extracted_data,
    get_mock_mapped_data,
    get_mock_onsen_mapping,
    get_mock_onsen_detail_html,
    get_mock_onsen_list_html,
)


@pytest.fixture
def mock_db():
    """
    Fixture to create a mock database for testing.
    Automatically cleans up and deletes the database after the test.

    Usage:
    ```python
    def test_something(with_mock_db):
        assert True
    ```
    """
    with get_mock_db() as db:
        yield db
        db.close()


"""
Test fixtures for the scraper functionality.
"""


@pytest.fixture
def mock_selenium_driver():
    """Mock Selenium WebDriver for testing."""
    driver = Mock()

    # Mock driver methods
    driver.get = Mock()
    driver.page_source = get_mock_onsen_detail_html()
    driver.quit = Mock()

    # Mock find_element method
    def mock_find_element(by, value):
        element = Mock(spec=WebElement)

        if by == By.ID and value == "areaDIV11":
            # Mock the main area div
            element.find_elements = Mock(
                return_value=[
                    create_mock_div_element("areaDIV1"),
                    create_mock_div_element("areaDIV2"),
                ]
            )
        elif by == By.XPATH:
            if value == "/html/body/div[2]":
                element.text = "別府"  # This is now the region
            elif value == "/html/body/div[3]":
                element.text = (
                    "123 別府温泉 海地獄"  # This contains ban number and name
                )
            elif value == "/html/body/div[4]/iframe":
                element.get_attribute = Mock(
                    return_value="https://maps.google.co.jp/maps?q=33.2797,131.5011&z=15"
                )
            elif value == "/html/body/div[5]/table":
                element.find_elements = Mock(return_value=[create_mock_table_element()])

        return element

    driver.find_element = Mock(side_effect=mock_find_element)
    driver.find_elements = Mock(return_value=[])

    return driver


@pytest.fixture
def mock_webdriver_wait():
    """Mock WebDriverWait for testing."""
    wait = Mock()
    wait.until = Mock()
    return wait


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the output directory structure
        os.makedirs(temp_dir, exist_ok=True)
        yield temp_dir


@pytest.fixture
def sample_scraped_data_file(temp_output_dir):
    """Create a sample scraped data file for testing."""
    sample_data = {"123": get_mock_complete_entry(), "456": get_mock_error_entry()}

    file_path = os.path.join(temp_output_dir, "scraped_onsen_data.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)

    return file_path


@pytest.fixture
def mock_onsen_mapping():
    """Get mock onsen mapping data."""
    return get_mock_onsen_mapping()


@pytest.fixture
def mock_extracted_data():
    """Get mock extracted onsen data."""
    return get_mock_extracted_data()


@pytest.fixture
def mock_mapped_data():
    """Get mock mapped onsen data."""
    return get_mock_mapped_data()


@pytest.fixture
def mock_complete_entry():
    """Get mock complete onsen entry."""
    return get_mock_complete_entry()


@pytest.fixture
def mock_error_entry():
    """Get mock error onsen entry."""
    return get_mock_error_entry()


@pytest.fixture
def mock_onsen_list_html():
    """Get mock onsen list HTML."""
    return get_mock_onsen_list_html()


@pytest.fixture
def mock_onsen_detail_html():
    """Get mock onsen detail HTML."""
    return get_mock_onsen_detail_html()


def create_mock_div_element(div_id: str) -> Mock:
    """Create a mock div element for testing."""
    div = Mock()
    div.get_attribute = Mock(return_value=div_id)
    div.find_elements = Mock(return_value=[create_mock_table_element()])
    return div


def create_mock_table_element() -> Mock:
    """Create a mock table element for testing."""
    table = Mock()

    # Create mock rows with key-value pairs
    rows = []
    table_data = {
        "住所": "大分県別府市鉄輪559-1",
        "電話": "0977-66-1577",
        "営業形態": "日帰り入浴",
        "入浴料金": "大人400円、小人200円",
        "利用時間": "8:30～17:00（年中無休）",
        "定休日ほか": "年中無休",
        "家族湯(貸切湯)": "あり（要予約）",
        "泉質": "含硫黄-ナトリウム-塩化物泉",
        "最寄バス停": "海地獄前（徒歩1分）",
        "最寄駅(徒歩)": "別府駅（バス15分）",
        "駐車場": "あり（無料）",
        "備考": "観光地としても人気の温泉施設",
    }

    for key, value in table_data.items():
        row = Mock()
        key_cell = Mock()
        key_cell.text = key
        value_cell = Mock()
        value_cell.text = value
        row.find_elements = Mock(return_value=[key_cell, value_cell])
        rows.append(row)

    table.find_elements = Mock(return_value=rows)
    return table


@pytest.fixture
def mock_selenium_patch():
    """Patch Selenium imports for testing."""
    with patch(
        "src.cli.commands.scrape_onsen_data.scraper.webdriver"
    ) as mock_webdriver, patch(
        "src.cli.commands.scrape_onsen_data.scraper.WebDriverWait"
    ) as mock_wait, patch(
        "src.cli.commands.scrape_onsen_data.scraper.EC"
    ) as mock_ec:

        # Mock Chrome driver
        mock_driver = Mock()
        mock_driver.get = Mock()
        mock_driver.page_source = get_mock_onsen_detail_html()
        mock_driver.quit = Mock()

        # Mock find_element method
        def mock_find_element(by, value):
            element = Mock(spec=WebElement)

            if by == By.ID and value == "areaDIV11":
                element.find_elements = Mock(
                    return_value=[
                        create_mock_div_element("areaDIV1"),
                        create_mock_div_element("areaDIV2"),
                    ]
                )
            elif by == By.XPATH:
                if value == "/html/body/div[2]":
                    element.text = "別府温泉 海地獄"
                elif value == "/html/body/div[3]":
                    element.text = "123 別府温泉 海地獄"
                elif value == "/html/body/div[4]/iframe":
                    element.get_attribute = Mock(
                        return_value="https://maps.google.co.jp/maps?q=33.2797,131.5011&z=15"
                    )
                elif value == "/html/body/div[5]/table":
                    element.find_elements = Mock(
                        return_value=[create_mock_table_element()]
                    )

            return element

        mock_driver.find_element = Mock(side_effect=mock_find_element)
        mock_driver.find_elements = Mock(return_value=[])

        mock_webdriver.Chrome.return_value = mock_driver
        mock_wait.return_value.until = Mock()
        mock_ec.presence_of_element_located = Mock()

        yield {
            "webdriver": mock_webdriver,
            "wait": mock_wait,
            "ec": mock_ec,
            "driver": mock_driver,
        }


@pytest.fixture
def mock_requests_patch():
    """Patch requests for testing."""
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = get_mock_onsen_detail_html().encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        yield mock_get


@pytest.fixture
def mock_logging_patch():
    """Patch loguru for testing."""
    with patch("loguru.logger.info") as mock_info, patch(
        "loguru.logger.debug"
    ) as mock_debug, patch("loguru.logger.error") as mock_error, patch(
        "loguru.logger.remove"
    ) as mock_remove, patch(
        "loguru.logger.add"
    ) as mock_add:

        yield {
            "info": mock_info,
            "debug": mock_debug,
            "error": mock_error,
            "remove": mock_remove,
            "add": mock_add,
        }


class Fixtures(CustomStrEnum):
    """Fixtures for the project."""

    MOCK_DB = "mock_db"
    MOCK_SELENIUM_DRIVER = "mock_selenium_driver"
    MOCK_WEBDRIVER_WAIT = "mock_webdriver_wait"
    TEMP_OUTPUT_DIR = "temp_output_dir"
    SAMPLE_SCRAPED_DATA_FILE = "sample_scraped_data_file"
    MOCK_ONSEN_MAPPING = "mock_onsen_mapping"
    MOCK_EXTRACTED_DATA = "mock_extracted_data"
    MOCK_MAPPED_DATA = "mock_mapped_data"
    MOCK_COMPLETE_ENTRY = "mock_complete_entry"
    MOCK_ERROR_ENTRY = "mock_error_entry"
