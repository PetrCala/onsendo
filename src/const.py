from typing import NamedTuple
from src.paths import PATHS


class CONST(NamedTuple):
    DATABASE_FOLDER: str = PATHS.DB_DIR
    DATABASE_NAME: str = "onsen.db"
    DATABASE_URL: str = f"sqlite:///{PATHS.DB_DIR}/{DATABASE_NAME}"
    MOCK_DATABASE_URL: str = "sqlite:///:memory:"
    ONSEN_URL: str = (
        "https://onsen-hunter.oita-apc.co.jp/dhunter/list_onsen.jsp?d=f8a23e58-f16b-4bb0-8b22-2e6acc46c5d5&o=onsendo&e=onsendo"
    )


CONST = CONST()
"""
Constants for the project.
"""
