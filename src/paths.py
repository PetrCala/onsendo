import os
from src.types import CustomStrEnum


class PATHS(CustomStrEnum):
    """Paths for the project."""

    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(APP_ROOT, "data")

    # Files
    DB_PATH = os.path.join(DATA_DIR, "onsen.db")
