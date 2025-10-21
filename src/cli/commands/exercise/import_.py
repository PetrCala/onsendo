"""
Import exercise data from files.
"""

import argparse

from src.lib.exercise_manager import (
    ExerciseDataImporter,
    ExerciseDataValidator,
    ExerciseDataManager,
)
from src.db.conn import get_db
from src.config import get_database_config
from src.lib.cli_display import show_database_banner


def import_exercise_data(args: argparse.Namespace) -> int:
    """Import exercise data from a file."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Import exercise data")

    try:
        # Positional arguments keep hyphens, optional arguments use underscores
        file_path = getattr(args, 'file-path', None)
        format_hint = getattr(args, 'format', None)
        notes = getattr(args, 'notes', None)
        validate_only = getattr(args, 'validate_only', False)
        link_visit = getattr(args, 'link_visit', None)
        link_heart_rate = getattr(args, 'link_heart_rate', None)

        print(f"📁 Importing exercise data from: {file_path}")

        # Import the data
        session = ExerciseDataImporter.import_from_file(file_path, format_hint)

        print("✅ Successfully imported data:")
        print(f"   🏃 Type: {session.exercise_type.value}")
        if session.activity_name:
            print(f"   📝 Activity: {session.activity_name}")
        print(f"   🕐 Duration: {session.duration_minutes} minutes")
        if session.distance_km:
            print(f"   📏 Distance: {session.distance_km:.2f} km")
        if session.calories_burned:
            print(f"   🔥 Calories: {session.calories_burned}")
        if session.avg_heart_rate:
            print(
                f"   💓 HR: {session.avg_heart_rate:.0f} avg "
                f"({session.min_heart_rate:.0f}-{session.max_heart_rate:.0f})"
            )
        if session.elevation_gain_m:
            print(f"   ⛰️  Elevation gain: {session.elevation_gain_m:.0f} m")
        print(f"   🕐 Start: {session.start_time}")
        print(f"   🕐 End: {session.end_time}")
        if session.data_points:
            print(f"   📍 Route points: {len(session.data_points)}")

        # Validate the data
        print("\n🔍 Validating data quality...")
        is_valid, errors = ExerciseDataValidator.validate_session(session)

        if not is_valid:
            print("❌ Data validation failed:")
            for error in errors:
                print(f"   ⚠️  {error}")

            if not validate_only:
                response = input(
                    "\n❓ Data has quality issues. Continue with import anyway? (y/N): "
                )  # pylint: disable=bad-builtin
                if response.lower() not in ["y", "yes"]:
                    print("❌ Import cancelled.")
                    return 1

        if validate_only:
            print("✅ Validation complete (import not performed)")
            return 0

        # Store in database
        print("\n💾 Storing data in database...")

        if notes:
            session.notes = notes

        with get_db(url=config.url) as db:
            manager = ExerciseDataManager(db)
            record = manager.store_session(
                session, visit_id=link_visit, heart_rate_id=link_heart_rate
            )

        print(f"✅ Successfully stored exercise session with ID: {record.id}")
        if record.data_hash:
            print(f"🔗 File hash: {record.data_hash[:16]}...")

        if link_visit:
            print(f"🔗 Linked to visit ID: {link_visit}")
        if link_heart_rate:
            print(f"🔗 Linked to heart rate ID: {link_heart_rate}")

        return 0

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return 1
    except ValueError as e:
        print(f"❌ Invalid data format: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1
