#!/usr/bin/env python3
"""
Helper script for Google Drive backup operations.
Called by Makefile targets.
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.lib.cloud_backup import get_backup_manager


def sync_backups(
    credentials_file: str,
    token_file: str,
    backup_dir: str,
    remote_path: str = "db_backups",
):
    """Sync local backups to Google Drive."""
    try:
        manager = get_backup_manager(credentials_file, token_file)
        stats = manager.sync_directory(backup_dir, remote_path)

        print(f"\n\033[0;32m[SUCCESS]\033[0m Cloud sync complete:")
        print(f"  Uploaded: {stats['uploaded']}")
        print(f"  Skipped: {stats['skipped']}")
        print(f"  Failed: {stats['failed']}")

        return 0 if stats["failed"] == 0 else 1

    except Exception as e:
        print(f"\033[0;31m[ERROR]\033[0m Cloud sync failed: {e}")
        return 1


def list_backups(credentials_file: str, token_file: str):
    """List backups in Google Drive."""
    try:
        manager = get_backup_manager(credentials_file, token_file)
        backups = manager.list_backups()

        print(f"\nFound {len(backups)} backups in Google Drive:\n")

        for backup in backups[:20]:
            size_mb = int(backup.get("size", 0)) / (1024 * 1024)
            print(
                f"  {backup['name']} ({size_mb:.2f} MB) - {backup.get('modifiedTime', 'N/A')}"
            )

        return 0

    except Exception as e:
        print(f"\033[0;31m[ERROR]\033[0m Failed to list backups: {e}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: backup_to_drive.py <command> [args...]")
        print("Commands: sync, list")
        sys.exit(1)

    command = sys.argv[1]

    if command == "sync":
        if len(sys.argv) < 5:
            print(
                "Usage: backup_to_drive.py sync <credentials> <token> <backup_dir> [remote_path]"
            )
            sys.exit(1)

        credentials = sys.argv[2]
        token = sys.argv[3]
        backup_dir = sys.argv[4]
        remote_path = sys.argv[5] if len(sys.argv) > 5 else "db_backups"

        sys.exit(sync_backups(credentials, token, backup_dir, remote_path))

    elif command == "list":
        if len(sys.argv) < 4:
            print("Usage: backup_to_drive.py list <credentials> <token>")
            sys.exit(1)

        credentials = sys.argv[2]
        token = sys.argv[3]

        sys.exit(list_backups(credentials, token))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
