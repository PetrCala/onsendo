"""CLI display utilities for database environment awareness.

This module provides visual feedback and safety confirmations for
database operations, with special handling for production environments.
"""

from typing import Optional
from loguru import logger

from src.config import DatabaseConfig


def show_database_banner(
    config: DatabaseConfig, operation: Optional[str] = None
) -> None:
    """Display database environment banner for destructive operations.

    Shows a prominent warning banner for production database operations,
    and a simple indicator for dev/test environments.

    Args:
        config: Database configuration
        operation: Optional operation name to display (e.g., "Delete visit", "Modify onsen")
    """
    if config.is_prod:
        # Production warning banner
        print("━" * 60)
        print("⚠️  PRODUCTION DATABASE")
        if config.path:
            print(f"   Path: {config.path}")
        if operation:
            print(f"   Operation: {operation}")
        print("━" * 60)
    else:
        # Simple dev/test indicator
        env_display = config.get_display_name()
        if config.path:
            print(f"→ Using {env_display} database: {config.path}")
        else:
            print(f"→ Using {env_display} database")


def confirm_destructive_operation(
    config: DatabaseConfig, operation: str, force: bool = False
) -> bool:
    """Request confirmation for destructive operations on production database.

    For production databases, requires the user to type 'yes' to confirm.
    For dev/test databases, returns True immediately.

    Args:
        config: Database configuration
        operation: Operation description (e.g., "delete visit", "drop all visits")
        force: If True, skip confirmation even for production

    Returns:
        True if operation should proceed, False if cancelled

    Raises:
        ValueError: If operation is cancelled by user
    """
    # Dev/test - no confirmation needed
    if not config.is_prod:
        return True

    # Production with --force flag - skip confirmation but log
    if force:
        logger.warning(f"Force flag used - skipping confirmation for: {operation}")
        return True

    # Production - require typed confirmation
    print()  # Blank line for readability
    response = input(
        f"⚠️  Confirm {operation} on PRODUCTION database. Type 'yes' to proceed: "
    )  # pylint: disable=bad-builtin

    if response.strip().lower() == "yes":
        logger.info(f"User confirmed: {operation}")
        return True

    logger.info(f"User cancelled: {operation}")
    raise ValueError("Operation cancelled by user")


def get_database_display_path(config: DatabaseConfig) -> str:
    """Get display-friendly database path.

    Args:
        config: Database configuration

    Returns:
        Database path or "(in-memory)" for test databases
    """
    if config.path:
        return config.path
    return "(in-memory)"
