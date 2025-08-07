"""
Test script for the onsen scraper functionality.
"""

import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from src.cli.commands.scrape_onsen_data.scraper import (
    setup_selenium_driver,
    extract_all_onsen_mapping,
    scrape_onsen_page_with_selenium,
)


def test_onsen_mapping_extraction():
    """Test the onsen mapping extraction functionality."""
    print("Testing onsen mapping extraction...")

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    try:
        driver = setup_selenium_driver()
        onsen_mapping = extract_all_onsen_mapping(driver)

        print(f"Successfully extracted {len(onsen_mapping)} onsens")

        # Print first few entries
        for i, (onsen_id, ban_number) in enumerate(list(onsen_mapping.items())[:5]):
            print(f"  Onsen ID: {onsen_id}, Ban: {ban_number}")

        driver.quit()
        return True

    except Exception as e:
        print(f"Error during mapping extraction: {e}")
        return False


def test_individual_onsen_scraping():
    """Test individual onsen page scraping."""
    print("\nTesting individual onsen scraping...")

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    try:
        # Test with a sample onsen ID (you might need to adjust this)
        test_onsen_id = "123"
        onsen_data = scrape_onsen_page_with_selenium(test_onsen_id)

        print(f"Successfully scraped onsen ID: {test_onsen_id}")
        print(f"Data keys: {list(onsen_data.keys())}")

        return True

    except Exception as e:
        print(f"Error during individual onsen scraping: {e}")
        return False


if __name__ == "__main__":
    print("Running onsen scraper tests...")

    # Test mapping extraction
    mapping_success = test_onsen_mapping_extraction()

    # Test individual scraping
    individual_success = test_individual_onsen_scraping()

    if mapping_success and individual_success:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")
        sys.exit(1)
