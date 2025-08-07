"""
scrape_onsen_data.py

Scrape onsen data from the web.
"""

import argparse
import json
import logging
import os
import time
from typing import Dict, Any

from src.const import CONST
from src.paths import PATHS
from .scraper import (
    setup_selenium_driver,
    extract_all_onsen_mapping,
    scrape_onsen_page_with_selenium,
)


def setup_logging() -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(PATHS.OUTPUT_DIR, "scraping.log")),
        ],
    )


def ensure_output_directory() -> None:
    """Ensure the output directory exists."""
    os.makedirs(PATHS.OUTPUT_DIR, exist_ok=True)


def load_existing_data() -> Dict[str, Any]:
    """Load existing scraped data if it exists."""
    if os.path.exists(PATHS.SCRAPED_ONSEN_DATA_FILE):
        with open(PATHS.SCRAPED_ONSEN_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data: Dict[str, Any], filepath: str) -> None:
    """Save data to JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def scrape_onsen_data(args: argparse.Namespace) -> None:
    """
    Scrape onsen data from the web.
    """
    setup_logging()
    ensure_output_directory()

    logging.info("Starting onsen data scraping process...")

    # Load existing data
    existing_data = load_existing_data()
    logging.info(f"Loaded {len(existing_data)} existing onsen records")

    # Extract onsen mapping
    driver = setup_selenium_driver()
    try:
        onsen_mapping = extract_all_onsen_mapping(driver)
    finally:
        driver.quit()

    # Save the mapping
    save_data(onsen_mapping, PATHS.ONSEN_MAPPING_FILE)
    logging.info(f"Saved onsen mapping to {PATHS.ONSEN_MAPPING_FILE}")

    # Scrape individual onsens
    scraped_count = 0
    skipped_count = 0

    for onsen_id, ban_number in onsen_mapping.items():
        if onsen_id in existing_data:
            logging.debug(f"Skipping onsen ID {onsen_id} (already scraped)")
            skipped_count += 1
            continue

        logging.info(f"Scraping new onsen ID: {onsen_id} (Ban: {ban_number})")
        onsen_data = scrape_onsen_page_with_selenium(onsen_id)
        existing_data[onsen_id] = onsen_data
        scraped_count += 1

        # Save progress after each onsen
        save_data(existing_data, PATHS.SCRAPED_ONSEN_DATA_FILE)

        # Add delay to be respectful to the server
        time.sleep(1)

    logging.info(
        f"Scraping completed. Scraped: {scraped_count}, Skipped: {skipped_count}"
    )
    logging.info(f"Total onsens in database: {len(existing_data)}")
    logging.info(f"Data saved to: {PATHS.SCRAPED_ONSEN_DATA_FILE}")
