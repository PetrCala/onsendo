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
from .data_mapper import map_scraped_data_to_onsen_model, get_mapping_summary


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


def process_scraped_onsen_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process scraped onsen data to include mapped data for database insertion.

    Args:
        raw_data: Raw scraped data

    Returns:
        Processed data with mapped fields
    """
    processed_data = raw_data.copy()

    # Add mapped data for database insertion
    if "extracted_data" in raw_data:
        mapped_data = map_scraped_data_to_onsen_model(raw_data["extracted_data"])
        processed_data["mapped_data"] = mapped_data

        # Add mapping summary
        summary = get_mapping_summary(raw_data["extracted_data"])
        processed_data["mapping_summary"] = summary

        logging.info(
            f"Mapped data for onsen {raw_data.get('onsen_id', 'unknown')}: "
            f"{summary['filled_fields']}/{summary['total_fields']} fields filled, "
            f"coordinates: {summary['has_coordinates']}"
        )

    return processed_data


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
        raw_onsen_data = scrape_onsen_page_with_selenium(onsen_id)

        # Process the data to include mapped fields
        processed_onsen_data = process_scraped_onsen_data(raw_onsen_data)

        existing_data[onsen_id] = processed_onsen_data
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

    # Print summary statistics
    print_summary_statistics(existing_data)


def print_summary_statistics(data: Dict[str, Any]) -> None:
    """
    Print summary statistics about the scraped data.

    Args:
        data: Scraped data dictionary
    """
    total_onsens = len(data)
    successful_scrapes = sum(1 for onsen in data.values() if "error" not in onsen)
    failed_scrapes = total_onsens - successful_scrapes

    # Count mapping statistics
    total_fields_filled = 0
    total_coordinates = 0
    total_table_entries = 0

    for onsen in data.values():
        if "mapping_summary" in onsen:
            summary = onsen["mapping_summary"]
            total_fields_filled += summary.get("filled_fields", 0)
            if summary.get("has_coordinates", False):
                total_coordinates += 1
            total_table_entries += summary.get("table_entries_mapped", 0)

    avg_fields_per_onsen = total_fields_filled / total_onsens if total_onsens > 0 else 0
    avg_table_entries_per_onsen = (
        total_table_entries / total_onsens if total_onsens > 0 else 0
    )

    print("\n" + "=" * 50)
    print("SCRAPING SUMMARY STATISTICS")
    print("=" * 50)
    print(f"Total onsens processed: {total_onsens}")
    print(f"Successful scrapes: {successful_scrapes}")
    print(f"Failed scrapes: {failed_scrapes}")
    print(
        f"Success rate: {(successful_scrapes/total_onsens)*100:.1f}%"
        if total_onsens > 0
        else "N/A"
    )
    print(f"Onsens with coordinates: {total_coordinates}")
    print(f"Average fields filled per onsen: {avg_fields_per_onsen:.1f}")
    print(f"Average table entries per onsen: {avg_table_entries_per_onsen:.1f}")
    print("=" * 50)
