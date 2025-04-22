from typing import NamedTuple
from src.paths import PATHS


class CONST(NamedTuple):
    DATABASE_URL: str = f"sqlite:///{PATHS.DB_PATH}"


CONST = CONST()
"""
Constants for the project.
"""
