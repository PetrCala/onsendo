from typing import NamedTuple
from src.paths import PATHS


class CONST(NamedTuple):
    DATABASE_FOLDER: str = PATHS.DB_DIR
    DATABASE_NAME: str = "onsen.db"
    DATABASE_URL: str = f"sqlite:///{PATHS.DB_DIR}/{DATABASE_NAME}"
    MOCK_DATABASE_URL: str = "sqlite:///:memory:"


CONST = CONST()
"""
Constants for the project.
"""
