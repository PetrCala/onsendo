"""
fill_db.py

Fill the database with onsen data from JSON files.
"""

import argparse
import os
from pathlib import Path
from loguru import logger
from src.db.conn import get_db_from_args
from src.db.import_data import import_onsen_data


def find_scraped_data_files() -> list[str]:
    """
    Search for scraped onsen data files in the artifacts/scraping folder.
    Returns a list of file paths that contain 'scraped_onsen_data' in their name.
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    scraping_dir = project_root / "artifacts" / "scraping"

    if not scraping_dir.exists():
        return []

    # Search for files containing 'scraped_onsen_data' in their name
    pattern = "**/*scraped_onsen_data*"
    matching_files = list(scraping_dir.glob(pattern))

    # Filter to only include JSON files and sort by modification time (newest first)
    json_files = [str(f) for f in matching_files if f.suffix.lower() == ".json"]
    json_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    return json_files


def interactive_file_selection() -> str:
    """
    Interactive file selection for scraped data files.
    Returns the selected file path or empty string if cancelled.
    """
    scraped_files = find_scraped_data_files()

    if not scraped_files:
        logger.warning("No scraped data files found in artifacts/scraping folder.")
        logger.info("Please run scraping first, or provide the JSON path manually.")
        return ""

    logger.info("Found the following scraped data files:")
    for i, file_path in enumerate(scraped_files, 1):
        # Get relative path for display
        rel_path = os.path.relpath(file_path, os.getcwd())
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        logger.info(f"  {i}. {rel_path} ({file_size:.2f} MB)")

    while True:
        try:
            choice = input(
                f"\nSelect a file (1-{len(scraped_files)}) or enter a custom path: "
            ).strip()

            if not choice:
                logger.info("No selection made.")
                return ""

            # Check if it's a numeric choice
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(scraped_files):
                    return scraped_files[choice_num - 1]
                else:
                    logger.error(
                        f"Invalid choice. Please enter a number between 1 and {len(scraped_files)}."
                    )
                    continue

            # Check if it's a custom path
            if os.path.exists(choice):
                return choice
            else:
                logger.error(f"File not found: {choice}")
                continue

        except KeyboardInterrupt:
            logger.info("\nOperation cancelled by user.")
            return ""
        except Exception as e:
            logger.error(f"Error during file selection: {e}")
            return ""


def fill_db(args: argparse.Namespace) -> None:
    """
    Fill the database with onsen data from JSON files.
    """
    database_path = config.url.replace("sqlite:///", "")
    if not os.path.exists(database_path):
        logger.error(
            f"Database file {database_path} does not exist! Run `database init` first to create it."
        )
        return

    # Determine the JSON file path
    json_path = args.json_path

    if not json_path and not args.no_interactive:
        logger.info("No JSON path provided. Entering interactive mode...")
        json_path = interactive_file_selection()
        if not json_path:
            logger.info("No file selected. Exiting.")
            return

    if not json_path:
        logger.error("JSON file path is required when running in non-interactive mode.")
        return

    # Convert to absolute path if relative
    if not os.path.isabs(json_path):
        json_path = os.path.abspath(json_path)

    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        return

    logger.info(
        f"Importing onsen data from JSON at {json_path} into {config.url}..."
    )

    database_url = config.url
    with get_db(url=database_url) as db:
        summary = import_onsen_data(db, json_path)
        logger.info(
            f"Import finished. Inserted={summary['inserted']}, Updated={summary['updated']}, Skipped={summary['skipped']}"
        )
