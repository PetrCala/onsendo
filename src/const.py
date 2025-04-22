from typing import NamedTuple
from src.paths import PATHS


class CONST(NamedTuple):
    DATABASE_URL: str = f"sqlite:///{PATHS.DB_PATH}"
    MOCK_DATABASE_URL: str = "sqlite:///:memory:"


CONST = CONST()
"""
Constants for the project.
"""
