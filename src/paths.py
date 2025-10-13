import os
from src.types import CustomStrEnum


class PATHS(CustomStrEnum):
    """Paths for the project."""

    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(APP_ROOT)
    LOCAL_DIR = os.path.join(PROJECT_ROOT, "local")
    CACHE_DIR = os.path.join(LOCAL_DIR, "cache")
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    TMP_DATA_DIR = os.path.join(DATA_DIR, "tmp")
    DB_DIR = os.path.join(DATA_DIR, "db")
    OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
    MAPS_DIR = os.path.join(OUTPUT_DIR, "maps")
    ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")
    ARTIFACTS_DB_DIR = os.path.join(ARTIFACTS_DIR, "db")
    ARTIFACTS_DB_BACKUPS_DIR = os.path.join(ARTIFACTS_DB_DIR, "backups")
    GDRIVE_DIR = os.path.join(LOCAL_DIR, "gdrive")

    # Files
    DB_PATH = os.path.join(DB_DIR, "onsen.db")
    RECOMMENDATION_CACHE_DB = os.path.join(CACHE_DIR, "recommendation_cache.sqlite3")
    SCRAPED_ONSEN_DATA_FILE = os.path.join(OUTPUT_DIR, "scraped_onsen_data.json")
    ONSEN_MAPPING_FILE = os.path.join(OUTPUT_DIR, "onsen_mapping.json")
    ONSEN_LATEST_ARTIFACT = os.path.join(ARTIFACTS_DB_DIR, "onsen_latest.db")
    GDRIVE_CREDENTIALS_FILE = os.path.join(GDRIVE_DIR, "credentials.json")
    GDRIVE_TOKEN_FILE = os.path.join(GDRIVE_DIR, "token.json")

    FIXTURES_PATH_REL = "src.testing.testutils.fixtures"
    """Path to the fixtures directory relative to the app root."""
