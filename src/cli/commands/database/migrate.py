"""
Database migration commands using Alembic.
"""

import argparse
import os
import subprocess
import sys

from src.config import get_database_config


def migrate_upgrade(args: argparse.Namespace) -> None:
    """
    Run database migrations to upgrade to the latest version.

    Args:
        args: Command-line arguments containing:
            - revision: Optional specific revision to upgrade to (default: "head")
            - env: Optional environment override
            - database: Optional database path override
    """
    # Get database config to show which database will be migrated
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    revision = "head"
    if hasattr(args, "revision") and args.revision:
        revision = args.revision

    print(f"Upgrading {config.env.value} database to revision: {revision}")
    print(f"Database: {config.path or config.url}")
    print()

    # Set environment variable for Alembic to use
    env = os.environ.copy()
    if config.env:
        env['ONSENDO_ENV'] = config.env.value
    if config.path:
        env['ONSENDO_DATABASE'] = config.path

    try:
        result = subprocess.run(
            ["poetry", "run", "alembic", "upgrade", revision],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print()
        print(f"✓ Successfully upgraded database to {revision}")
    except subprocess.CalledProcessError as e:
        print(f"Error running migration: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)


def migrate_downgrade(args: argparse.Namespace) -> None:
    """
    Downgrade database to a previous migration.

    Args:
        args: Command-line arguments containing:
            - revision: Revision to downgrade to (required, use "-1" for previous)
    """
    if not hasattr(args, "revision") or not args.revision:
        print("Error: --revision is required for downgrade", file=sys.stderr)
        sys.exit(1)

    revision = args.revision
    print(f"Downgrading database to revision: {revision}")
    print()

    # Confirm if not forcing
    if not (hasattr(args, "force") and args.force):
        # Using input() is acceptable here for user confirmation
        confirm = input(  # pylint: disable=bad-builtin
            f"Are you sure you want to downgrade to {revision}? (yes/no): "
        ).strip().lower()
        if confirm not in ["yes", "y"]:
            print("Downgrade cancelled.")
            return

    try:
        result = subprocess.run(
            ["poetry", "run", "alembic", "downgrade", revision],
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print()
        print(f"✓ Successfully downgraded database to {revision}")
    except subprocess.CalledProcessError as e:
        print(f"Error running downgrade: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)


def migrate_current(args: argparse.Namespace) -> None:  # pylint: disable=unused-argument
    """
    Show current database migration revision.

    Args:
        args: Command-line arguments (none required)
    """
    print("Current database revision:")
    print()

    try:
        result = subprocess.run(
            ["poetry", "run", "alembic", "current"],
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error checking current revision: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)


def migrate_history(args: argparse.Namespace) -> None:
    """
    Show migration history.

    Args:
        args: Command-line arguments containing:
            - verbose: Show detailed information (default: False)
    """
    print("Migration history:")
    print()

    cmd = ["poetry", "run", "alembic", "history"]
    if hasattr(args, "verbose") and args.verbose:
        cmd.append("--verbose")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error showing history: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)


def migrate_generate(args: argparse.Namespace) -> None:
    """
    Generate a new migration based on model changes.

    Args:
        args: Command-line arguments containing:
            - message: Migration message (required)
    """
    if not hasattr(args, "message") or not args.message:
        print("Error: --message is required for generating migrations", file=sys.stderr)
        sys.exit(1)

    message = args.message
    print(f"Generating new migration: {message}")
    print()

    try:
        result = subprocess.run(
            ["poetry", "run", "alembic", "revision", "--autogenerate", "-m", message],
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print()
        print("✓ Migration generated successfully")
        print("Please review the generated migration file before running 'database migrate-upgrade'")
    except subprocess.CalledProcessError as e:
        print(f"Error generating migration: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)


def migrate_stamp(args: argparse.Namespace) -> None:
    """
    Stamp the database with a specific revision without running migrations.

    This is useful for marking an existing database as being at a specific migration level.

    Args:
        args: Command-line arguments containing:
            - revision: Revision to stamp (required, use "head" for latest)
    """
    if not hasattr(args, "revision") or not args.revision:
        print("Error: --revision is required for stamp", file=sys.stderr)
        sys.exit(1)

    revision = args.revision
    print(f"Stamping database with revision: {revision}")
    print()

    try:
        result = subprocess.run(
            ["poetry", "run", "alembic", "stamp", revision],
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print()
        print(f"✓ Successfully stamped database with {revision}")
    except subprocess.CalledProcessError as e:
        print(f"Error stamping database: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)
