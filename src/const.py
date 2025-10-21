from typing import NamedTuple
from src.paths import PATHS


class CONST(NamedTuple):
    DATABASE_FOLDER: str = PATHS.DB_DIR

    # Legacy database configuration (deprecated - use src.config instead)
    DATABASE_NAME: str = "onsen.db"
    DATABASE_URL: str = f"sqlite:///{PATHS.DB_DIR}/{DATABASE_NAME}"

    # Environment-specific database URLs
    DEV_DATABASE_URL: str = f"sqlite:///{PATHS.DB_DIR}/onsen.dev.db"
    PROD_DATABASE_URL: str = f"sqlite:///{PATHS.DB_DIR}/onsen.prod.db"
    MOCK_DATABASE_URL: str = "sqlite:///:memory:"
    HOLIDAY_SERVICE_URL: str = "https://holidays-jp.github.io/api/v1"
    ONSEN_URL: str = (
        "https://onsen-hunter.oita-apc.co.jp/dhunter/list_onsen.jsp?d=f8a23e58-f16b-4bb0-8b22-2e6acc46c5d5&o=onsendo&e=onsendo"
    )
    ONSEN_DETAIL_URL_TEMPLATE: str = (
        "https://onsen-hunter.oita-apc.co.jp/dhunter/details_onsen.jsp?d=f8a23e58-f16b-4bb0-8b22-2e6acc46c5d5&o=onsendo&e=onsendo&f=list_onsen.jsp%3Fd%3Df8a23e58-f16b-4bb0-8b22-2e6acc46c5d5%26o%3Donsendo%26e%3Donsendo&t={onsen_id}"
    )
    DELETED_IMAGE_URL: str = (
        "https://onsen-hunter.oita-apc.co.jp/dhunter/thumbnail/deleted.jpg"
    )
    DELETED_IMAGE_SUBSTRING: str = (
        "thumbnail/deleted.jpg"  # If found in the image URL, an image is marked as deleted
    )


CONST = CONST()
"""
Constants for the project.
"""
