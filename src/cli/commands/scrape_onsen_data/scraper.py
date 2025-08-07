"""
Scraper module for onsen data extraction.
"""

import logging
import re
from typing import Dict, List, Any, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def setup_selenium_driver() -> webdriver.Chrome:
    """Setup Selenium Chrome driver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    return webdriver.Chrome(options=chrome_options)


def find_all_onsen_divs(driver: webdriver.Chrome) -> List:
    """
    Find all divs that contain onsen data.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        List of div elements that contain onsen data
    """
    onsen_divs = []

    try:
        # Wait for the main area div to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "areaDIV11"))
        )

        area_div = driver.find_element(By.ID, "areaDIV11")

        # Find all divs recursively that might contain onsens
        all_divs = area_div.find_elements(By.XPATH, ".//div")

        for div in all_divs:
            div_id = div.get_attribute("id")

            # Skip the main container div
            if div_id == "areaDIV11":
                continue

            # Check if this div contains a table (indicates it has onsens)
            try:
                tables = div.find_elements(By.TAG_NAME, "table")
                if tables:
                    # Verify this is actually an onsen div by checking for specific structure
                    if is_onsen_div(div):
                        onsen_divs.append(div)
                        logging.debug(f"Found onsen div: {div_id}")
            except Exception as e:
                logging.debug(f"Error checking div {div_id}: {e}")
                continue

    except TimeoutException:
        logging.error("Timeout waiting for areaDIV11 to load")
    except Exception as e:
        logging.error(f"Error finding onsen divs: {e}")

    return onsen_divs


def is_onsen_div(div_element) -> bool:
    """
    Check if a div element contains onsen data.

    Args:
        div_element: The div element to check

    Returns:
        True if the div contains onsen data, False otherwise
    """
    try:
        # Check for the specific structure that indicates an onsen
        # Look for ban number span
        ban_spans = div_element.find_elements(By.XPATH, ".//span")

        # Look for onclick attributes that contain details()
        onclick_elements = div_element.find_elements(By.XPATH, ".//*[@onclick]")

        return len(ban_spans) > 0 and len(onclick_elements) > 0

    except Exception:
        return False


def extract_onsen_data_from_div(div_element) -> Dict[str, str]:
    """
    Extract onsen ID and ban number from a div element.

    Args:
        div_element: The div element containing onsen data

    Returns:
        Dict mapping onsen ID to ban number
    """
    onsen_data = {}

    try:
        # Find all tables in this div
        tables = div_element.find_elements(By.TAG_NAME, "table")

        for table in tables:
            try:
                # Extract ban number using the provided XPath
                ban_elements = table.find_elements(
                    By.XPATH, ".//tbody/tr[1]/td/div/table/tbody/tr/td[1]/div/span"
                )

                if not ban_elements:
                    continue

                ban_number = ban_elements[0].text.strip()

                # Extract onsen ID from onclick attribute using the provided XPath
                onclick_elements = table.find_elements(
                    By.XPATH, ".//tbody/tr[2]/td/table/tbody/tr/td[1]/div"
                )

                if not onclick_elements:
                    continue

                onclick_attr = onclick_elements[0].get_attribute("onclick")

                if onclick_attr:
                    # Extract ID from details(123) format
                    match = re.search(r"details\((\d+)\)", onclick_attr)
                    if match:
                        onsen_id = match.group(1)
                        onsen_data[onsen_id] = ban_number
                        logging.debug(
                            f"Extracted onsen: ID={onsen_id}, Ban={ban_number}"
                        )

            except Exception as e:
                logging.debug(f"Error extracting data from table: {e}")
                continue

    except Exception as e:
        logging.debug(f"Error processing div: {e}")

    return onsen_data


def extract_all_onsen_mapping(driver: webdriver.Chrome) -> Dict[str, str]:
    """
    Extract all onsen ID to ban number mappings from the page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        Dict mapping onsen ID to ban number
    """
    onsen_mapping = {}

    # Find all divs that contain onsen data
    onsen_divs = find_all_onsen_divs(driver)

    logging.info(f"Found {len(onsen_divs)} divs containing onsen data")

    # Extract data from each div
    for div in onsen_divs:
        div_data = extract_onsen_data_from_div(div)
        onsen_mapping.update(div_data)

    logging.info(f"Total onsens extracted: {len(onsen_mapping)}")
    return onsen_mapping


def scrape_onsen_page_with_selenium(onsen_id: str) -> Dict[str, Any]:
    """
    Scrape individual onsen page using Selenium for better JavaScript handling.

    Args:
        onsen_id: The onsen ID to scrape

    Returns:
        Dict containing scraped onsen data
    """
    from src.const import CONST

    logging.info(f"Scraping onsen ID: {onsen_id}")

    url = CONST.ONSEN_DETAIL_URL_TEMPLATE.format(onsen_id=onsen_id)

    driver = setup_selenium_driver()

    try:
        driver.get(url)

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Get the page source after JavaScript execution
        page_source = driver.page_source

        # Placeholder for onsen data extraction
        # This will be filled in with specific paths when provided
        onsen_data = {
            "onsen_id": onsen_id,
            "url": url,
            "raw_html": page_source,
            "extracted_data": {
                # Placeholder for specific data fields
                "name": "TODO",
                "address": "TODO",
                "description": "TODO",
                # Add more fields as needed
            },
        }

        logging.info(f"Successfully scraped onsen ID: {onsen_id}")
        return onsen_data

    except Exception as e:
        logging.error(f"Error scraping onsen ID {onsen_id}: {e}")
        return {"onsen_id": onsen_id, "url": url, "error": str(e), "extracted_data": {}}
    finally:
        driver.quit()
