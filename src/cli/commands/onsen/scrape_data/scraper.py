"""
Web scraping functionality for onsen data.
"""

import re
from typing import Dict, Any, List

from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.const import CONST


def setup_selenium_driver() -> webdriver.Chrome:
    """
    Setup and configure Selenium Chrome driver.

    Returns:
        Configured Chrome WebDriver instance
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def find_all_onsen_divs(driver: webdriver.Chrome) -> List:
    """
    Find all divs that contain onsen data by recursively searching through all areaDIV elements.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        List of div elements containing onsen data
    """
    onsen_divs = []
    processed_area_divs = set()  # Track processed areaDIVs to avoid infinite loops

    def search_area_div_recursively(area_div_element, depth=0):
        """
        Recursively search through an areaDIV element for onsen data.

        Args:
            area_div_element: The areaDIV element to search
            depth: Current nesting depth (for logging)
        """
        if depth > 5:  # Safety limit to prevent infinite recursion
            logger.warning(
                f"Reached maximum recursion depth ({depth}) for areaDIV search"
            )
            return

        try:
            area_div_id = area_div_element.get_attribute("id")
            if area_div_id in processed_area_divs:
                logger.debug(f"Skipping already processed areaDIV: {area_div_id}")
                return

            processed_area_divs.add(area_div_id)
            logger.debug(f"Searching areaDIV: {area_div_id} (depth: {depth})")

            # Find all divs within this areaDIV
            all_divs = area_div_element.find_elements(By.TAG_NAME, "div")

            for div in all_divs:
                try:
                    div_id = div.get_attribute("id")

                    # Check if this is another areaDIV (recursive case)
                    if div_id and div_id.startswith("areaDIV"):
                        logger.debug(
                            f"Found nested areaDIV: {div_id} within {area_div_id}"
                        )
                        search_area_div_recursively(div, depth + 1)
                        continue

                    # Check if this div contains onsen data
                    if is_onsen_div(div):
                        onsen_divs.append(div)
                        logger.debug(f"Found onsen div: {div_id} in {area_div_id}")

                except Exception as e:
                    logger.debug(f"Error checking div {div_id}: {e}")
                    continue

        except Exception as e:
            logger.debug(f"Error processing areaDIV: {e}")

    try:
        # Find all areaDIV elements on the page
        area_divs = driver.find_elements(By.CSS_SELECTOR, "[id^='areaDIV']")
        logger.info(f"Found {len(area_divs)} areaDIV elements on the page")

        # Sort by ID to process in a predictable order
        area_divs.sort(key=lambda x: x.get_attribute("id"))

        # Search through each areaDIV recursively
        for area_div in area_divs:
            search_area_div_recursively(area_div)

    except Exception as e:
        logger.error(f"Error finding onsen divs: {e}")

    logger.info(f"Total onsen divs found: {len(onsen_divs)}")
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
                        logger.debug(
                            f"Extracted onsen: ID={onsen_id}, Ban={ban_number}"
                        )

            except Exception as e:
                logger.debug(f"Error extracting data from table: {e}")
                continue

    except Exception as e:
        logger.debug(f"Error processing div: {e}")

    return onsen_data


def extract_all_onsen_mapping(driver: webdriver.Chrome) -> Dict[str, str]:
    """
    Extract all onsen ID to ban number mappings from the page.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        Dict mapping onsen ID to ban number
    """
    from src.const import CONST

    onsen_mapping = {}

    # Navigate to the main onsen list page
    logger.info(f"Navigating to onsen list page: {CONST.ONSEN_URL}")
    driver.get(CONST.ONSEN_URL)

    # Wait for the page to load - wait for any areaDIV element to appear
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[id^='areaDIV']"))
        )
        logger.info("Page loaded successfully")
    except Exception as e:
        logger.error(f"Timeout waiting for page to load: {e}")
        return onsen_mapping

    # Find all divs that contain onsen data
    onsen_divs = find_all_onsen_divs(driver)

    logger.info(f"Found {len(onsen_divs)} divs containing onsen data")

    # Extract data from each div
    for div in onsen_divs:
        div_data = extract_onsen_data_from_div(div)
        onsen_mapping.update(div_data)

    logger.info(f"Total onsens extracted: {len(onsen_mapping)}")
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

    logger.info(f"Scraping onsen ID: {onsen_id}")

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

        # Extract detailed onsen data
        extracted_data = extract_detailed_onsen_data(driver)

        onsen_data = {
            "onsen_id": onsen_id,
            "url": url,
            "raw_html": page_source,
            "extracted_data": extracted_data,
        }

        logger.info(f"Successfully scraped onsen ID: {onsen_id}")
        return onsen_data

    except Exception as e:
        logger.error(f"Error scraping onsen ID {onsen_id}: {e}")
        return {"onsen_id": onsen_id, "url": url, "error": str(e), "extracted_data": {}}
    finally:
        driver.quit()


def extract_detailed_onsen_data(driver) -> Dict[str, Any]:
    """
    Extract detailed onsen data using the provided XPath selectors.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        Dict containing extracted onsen data
    """
    extracted_data = {}

    try:
        # 1. Extract region from /html/body/div[2]
        try:
            region_element = driver.find_element(By.XPATH, "/html/body/div[2]")
            extracted_data["region"] = region_element.text.strip()
            logger.debug(f"Extracted region: {extracted_data['region']}")
        except Exception as e:
            logger.debug(f"Error extracting region: {e}")
            extracted_data["region"] = ""

        # 2. Extract ban number and name from /html/body/div[3]
        try:
            ban_element = driver.find_element(By.XPATH, "/html/body/div[3]")
            ban_number_and_name_text = ban_element.text.strip()

            # Split the ban number and name
            import re

            # Pattern to match: number + 番 + space + name
            match = re.match(r"^(\d+)番\s+(.+)$", ban_number_and_name_text)
            if match:
                extracted_data["ban_number"] = match.group(1)
                extracted_data["name"] = match.group(2).strip()
            else:
                # Fallback: try to extract just the number (without 番)
                number_match = re.match(r"^(\d+)", ban_number_and_name_text)
                if number_match:
                    extracted_data["ban_number"] = number_match.group(1)
                    # Remove the number, 番 character, and any spaces
                    extracted_data["name"] = re.sub(
                        r"^\d+番\s*", "", ban_number_and_name_text
                    )
                else:
                    extracted_data["ban_number"] = ""
                    extracted_data["name"] = ban_number_and_name_text

            logger.debug(f"Extracted ban number: {extracted_data['ban_number']}")
            logger.debug(f"Extracted name: {extracted_data['name']}")
        except Exception as e:
            logger.debug(f"Error extracting ban number and name: {e}")
            extracted_data["ban_number"] = ""
            extracted_data["name"] = ""

        # 3. Check if onsen is deleted by looking for deleted.jpg image
        try:
            img_element = driver.find_element(By.XPATH, "/html/body/div[4]/div[1]/img")
            img_src = img_element.get_attribute("src")
            extracted_data["deleted"] = CONST.DELETED_IMAGE_SUBSTRING in img_src
            logger.debug(f"Onsen deleted status: {extracted_data['deleted']}")
        except Exception as e:
            logger.debug(f"Error checking deleted status: {e}")
            extracted_data["deleted"] = False

        # 4. Extract map iframe and coordinates from /html/body/div[4]/iframe
        try:
            iframe_element = driver.find_element(By.XPATH, "/html/body/div[4]/iframe")
            iframe_src = iframe_element.get_attribute("src")

            if iframe_src:
                extracted_data["map_url"] = iframe_src

                # Extract coordinates from the URL
                # Look for &q=xx.xx,yy.yy pattern
                import re

                coord_match = re.search(r"&q=([\d.-]+),([\d.-]+)", iframe_src)
                if coord_match:
                    lat = float(coord_match.group(1))
                    lon = float(coord_match.group(2))
                    extracted_data["latitude"] = lat
                    extracted_data["longitude"] = lon
                    logger.debug(f"Extracted coordinates: {lat}, {lon}")
                else:
                    extracted_data["latitude"] = None
                    extracted_data["longitude"] = None
                    logger.debug("No coordinates found in map URL")
            else:
                extracted_data["map_url"] = ""
                extracted_data["latitude"] = None
                extracted_data["longitude"] = None

        except Exception as e:
            logger.debug(f"Error extracting map data: {e}")
            extracted_data["map_url"] = ""
            extracted_data["latitude"] = None
            extracted_data["longitude"] = None

        # 5. Extract table data from /html/body/div[5]/table
        try:
            table_element = driver.find_element(By.XPATH, "/html/body/div[5]/table")
            table_data = extract_table_data(table_element)
            extracted_data.update(table_data)
            logger.debug(f"Extracted {len(table_data)} table entries")
        except Exception as e:
            logger.debug(f"Error extracting table data: {e}")

    except Exception as e:
        logger.error(f"Error in detailed data extraction: {e}")

    return extracted_data


def extract_table_data(table_element) -> Dict[str, str]:
    """
    Extract key-value pairs from the onsen information table.

    Args:
        table_element: The table element containing onsen information

    Returns:
        Dict mapping table keys to values
    """
    table_data = {}

    try:
        # Find all rows in the table
        rows = table_element.find_elements(By.XPATH, ".//tbody/tr")

        for row in rows:
            try:
                # Each row has two td elements: key and value
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()

                    if key and value:  # Only add non-empty key-value pairs
                        # Clean up the key (remove any special characters or formatting)
                        clean_key = key.replace(":", "").strip()
                        table_data[clean_key] = value
                        logger.debug(f"Table entry: {clean_key} = {value}")

            except Exception as e:
                logger.debug(f"Error extracting row data: {e}")
                continue

    except Exception as e:
        logger.debug(f"Error processing table: {e}")

    return table_data
