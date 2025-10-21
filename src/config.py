"""Database environment configuration.

This module provides database environment management with support for:
- Multiple environments (dev, prod, test)
- Environment selection via CLI flags or environment variables
- Production database safety guardrails
- Test isolation

Environment Selection Priority:
1. Explicit path override (--database /path/to/db.db)
2. CLI flag (--env prod)
3. Environment variable (ONSENDO_ENV=prod)
4. Default (dev)
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from loguru import logger

from src.paths import PATHS

# Legacy constant - kept for backwards compatibility
CLI_NAME = "Onsen CLI"


class DatabaseEnvironment(Enum):
    """Database environment types."""

    DEV = "dev"
    PROD = "prod"
    TEST = "test"


@dataclass
class DatabaseConfig:
    """Database configuration for a specific environment.

    Attributes:
        env: The database environment (dev, prod, test)
        url: SQLAlchemy database URL
        path: Filesystem path to database file (None for in-memory)
        is_prod: Whether this is the production environment
    """

    env: DatabaseEnvironment
    url: str
    path: Optional[str]
    is_prod: bool

    def get_display_name(self) -> str:
        """Get human-readable display name for this environment.

        Returns:
            Display name (e.g., "PRODUCTION", "DEV", "TEST")
        """
        return "PRODUCTION" if self.is_prod else self.env.value.upper()


def get_database_path(env: DatabaseEnvironment) -> Optional[str]:
    """Get filesystem path for a database environment.

    Args:
        env: Database environment

    Returns:
        Absolute path to database file, or None for in-memory (test)
    """
    if env == DatabaseEnvironment.DEV:
        return os.path.join(PATHS.DB_DIR, "onsen.dev.db")
    elif env == DatabaseEnvironment.PROD:
        return os.path.join(PATHS.DB_DIR, "onsen.prod.db")
    elif env == DatabaseEnvironment.TEST:
        return None  # In-memory database
    else:
        raise ValueError(f"Unknown environment: {env}")


def get_database_url_for_env(env: DatabaseEnvironment) -> str:
    """Get SQLAlchemy database URL for an environment.

    Args:
        env: Database environment

    Returns:
        SQLAlchemy database URL
    """
    if env == DatabaseEnvironment.TEST:
        return "sqlite:///:memory:"

    path = get_database_path(env)
    if path is None:
        raise ValueError(f"No database path for environment: {env}")

    return f"sqlite:///{path}"


def get_database_config(
    env_override: Optional[str] = None,
    path_override: Optional[str] = None,
    allow_prod: bool = True,
) -> DatabaseConfig:
    """Resolve database configuration with priority handling.

    Priority order:
    1. path_override (explicit database path)
    2. env_override (explicit environment: dev/prod)
    3. ONSENDO_ENV environment variable
    4. Default to 'dev'

    Args:
        env_override: Explicit environment selection (from --env flag)
        path_override: Explicit database path (from --database flag)
        allow_prod: Whether to allow production database access

    Returns:
        DatabaseConfig for the resolved environment

    Raises:
        ValueError: If prod is not allowed but would be selected
        ValueError: If invalid environment name is provided
    """
    # Priority 1: Explicit path override
    if path_override:
        # Custom database path - treat as dev-like environment
        abs_path = os.path.abspath(path_override)
        url = f"sqlite:///{abs_path}"
        logger.debug(f"Using explicit database path: {abs_path}")
        return DatabaseConfig(
            env=DatabaseEnvironment.DEV, url=url, path=abs_path, is_prod=False
        )

    # Priority 2: Explicit environment override (--env flag)
    if env_override:
        try:
            env = DatabaseEnvironment(env_override.lower())
        except ValueError as exc:
            raise ValueError(
                f"Invalid environment: {env_override}. "
                f"Valid options: dev, prod"
            ) from exc
    # Priority 3: Environment variable
    elif os.getenv("ONSENDO_ENV"):
        env_str = os.getenv("ONSENDO_ENV", "").lower()
        try:
            env = DatabaseEnvironment(env_str)
        except ValueError as exc:
            raise ValueError(
                f"Invalid ONSENDO_ENV: {env_str}. " f"Valid options: dev, prod"
            ) from exc
        logger.debug(f"Using environment from ONSENDO_ENV: {env.value}")
    # Priority 4: Default to dev
    else:
        env = DatabaseEnvironment.DEV
        logger.debug("Using default environment: dev")

    # Check production access permission
    if env == DatabaseEnvironment.PROD and not allow_prod:
        raise ValueError(
            "Production database access not allowed in this context. "
            "Use --env dev or unset ONSENDO_ENV."
        )

    # Build configuration
    url = get_database_url_for_env(env)
    path = get_database_path(env)
    is_prod = env == DatabaseEnvironment.PROD

    return DatabaseConfig(env=env, url=url, path=path, is_prod=is_prod)


def get_database_url(
    env_override: Optional[str] = None, path_override: Optional[str] = None
) -> str:
    """Get database URL for current environment (convenience function).

    Args:
        env_override: Explicit environment selection
        path_override: Explicit database path

    Returns:
        SQLAlchemy database URL
    """
    config = get_database_config(env_override=env_override, path_override=path_override)
    return config.url


def ensure_not_prod_in_tests() -> None:
    """Ensure production database cannot be accessed during test execution.

    This function should be called in test fixtures to prevent accidental
    modification of production data during testing.

    Raises:
        RuntimeError: If ONSENDO_ENV=prod is set
    """
    if os.getenv("ONSENDO_ENV") == "prod":
        raise RuntimeError(
            "CRITICAL: Cannot run tests with ONSENDO_ENV=prod set.\n"
            "Tests must use isolated databases to prevent data corruption.\n"
            "Please unset ONSENDO_ENV or set it to 'dev' or 'test'."
        )
