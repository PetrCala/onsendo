import os
from src.types import CustomStrEnum


class PATHS(CustomStrEnum):
    """Paths for the project."""

    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(APP_ROOT)
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    TMP_DATA_DIR = os.path.join(DATA_DIR, "tmp")
    DB_DIR = os.path.join(DATA_DIR, "db")
    OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

    # Files
    DB_PATH = os.path.join(DB_DIR, "onsen.db")
    SCRAPED_ONSEN_DATA_FILE = os.path.join(OUTPUT_DIR, "scraped_onsen_data.json")
    ONSEN_MAPPING_FILE = os.path.join(OUTPUT_DIR, "onsen_mapping.json")

    FIXTURES_PATH_REL = "src.testing.testutils.fixtures"
    """Path to the fixtures directory relative to the app root."""
