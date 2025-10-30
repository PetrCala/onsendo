#!/usr/bin/env python3
"""
One-off migration script to update onsen monitoring activities.

This script migrates the is_onsen_monitoring boolean flag to the activity_type
enum value. It finds all activities where is_onsen_monitoring=True and sets
their activity_type to 'onsen_monitoring'.

Usage:
    python scripts/migrate_onsen_monitoring_type.py [--dry-run] [--env dev|prod]

Arguments:
    --dry-run: Show what would be changed without making changes
    --env: Database environment (dev or prod, default: dev)
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.config import get_database_config
from src.db.conn import get_db
from src.db.models import Activity
from src.types.exercise import ExerciseType


def migrate_onsen_monitoring_activities(dry_run: bool = False, env: str = "dev"):
    """
    Migrate activities from is_onsen_monitoring flag to activity_type enum.

    Args:
        dry_run: If True, show changes without applying them
        env: Database environment (dev or prod)
    """
    print("=" * 70)
    print("Onsen Monitoring Activity Type Migration")
    print("=" * 70)
    print(f"Environment: {env}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    # Get database config
    config = get_database_config(env_override=env)
    print(f"Database: {config.path}")
    print()

    # Connect to database
    with get_db(url=config.url) as db:
        # Check if is_onsen_monitoring column exists
        # (it should exist until the migration is run)
        try:
            result = db.execute(
                text("SELECT is_onsen_monitoring FROM activities LIMIT 1")
            ).fetchone()
        except Exception:
            print("❌ Error: is_onsen_monitoring column not found!")
            print("This migration may have already been run, or the database")
            print("schema is not in the expected state.")
            return

        # Find activities with is_onsen_monitoring = True
        activities_to_migrate = (
            db.query(Activity)
            .filter(Activity.is_onsen_monitoring.is_(True))
            .all()
        )

        if not activities_to_migrate:
            print("✓ No activities to migrate (no activities with is_onsen_monitoring=True)")
            return

        print(f"Found {len(activities_to_migrate)} activities to migrate:")
        print()

        # Show details for each activity
        for activity in activities_to_migrate:
            print(f"  Activity ID: {activity.id}")
            print(f"    Name: {activity.activity_name}")
            print(f"    Date: {activity.start_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"    Current Type: {activity.activity_type}")
            print(f"    Workout Type: {activity.workout_type}")
            print(f"    Linked to Visit: {'Yes' if activity.visit_id else 'No'}")
            if not dry_run:
                print(f"    → Will change to: {ExerciseType.ONSEN_MONITORING.value}")
            print()

        if dry_run:
            print("=" * 70)
            print("DRY RUN - No changes made")
            print(f"Run without --dry-run to apply these {len(activities_to_migrate)} changes")
            print("=" * 70)
            return

        # Apply migration
        print("=" * 70)
        print("Applying migration...")
        print()

        migrated_count = 0
        for activity in activities_to_migrate:
            try:
                activity.activity_type = ExerciseType.ONSEN_MONITORING.value
                migrated_count += 1
            except Exception as e:
                print(f"❌ Error migrating activity {activity.id}: {e}")

        # Commit changes
        try:
            db.commit()
            print(f"✓ Successfully migrated {migrated_count} activities")
            print()
            print("Summary:")
            print(f"  - {migrated_count} activities updated")
            print(f"  - All updated to activity_type = '{ExerciseType.ONSEN_MONITORING.value}'")
            print(f"  - workout_type preserved (unchanged)")
            print()
            print("=" * 70)
            print("Migration Complete!")
            print("=" * 70)
            print()
            print("Next steps:")
            print("  1. Run the database migration to remove is_onsen_monitoring column")
            print("     poetry run onsendo database migrate-upgrade")
            print("  2. Verify activities with: poetry run onsendo activity list")
        except Exception as e:
            db.rollback()
            print(f"❌ Error committing changes: {e}")
            print("Migration rolled back - no changes applied")


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate onsen monitoring activities to use activity_type enum"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--env",
        type=str,
        choices=["dev", "prod"],
        default="dev",
        help="Database environment (default: dev)",
    )

    args = parser.parse_args()

    # Safety check for production
    if args.env == "prod" and not args.dry_run:
        print("⚠️  WARNING: You are about to modify the PRODUCTION database!")
        print()
        response = input("Type 'yes' to continue: ")
        if response.lower() != "yes":
            print("Migration cancelled")
            return

    migrate_onsen_monitoring_activities(dry_run=args.dry_run, env=args.env)


if __name__ == "__main__":
    main()
