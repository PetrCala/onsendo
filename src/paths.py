import os
from src.types import CustomStrEnum


class PATHS(CustomStrEnum):
    """Paths for the project."""

    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(APP_ROOT, "data")
    TMP_DATA_DIR = os.path.join(DATA_DIR, "tmp")

    # Files
    DB_PATH = os.path.join(DATA_DIR, "onsen.db")
