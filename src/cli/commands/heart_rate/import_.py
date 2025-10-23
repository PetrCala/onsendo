"""
Import heart rate data from files.
"""

import argparse

from src.lib.heart_rate_manager import (
    HeartRateDataImporter,
    HeartRateDataValidator,
    HeartRateDataManager,
)
from src.db.conn import get_db_from_args
from src.lib.cli_display import show_database_banner


def import_heart_rate_data(args: argparse.Namespace) -> int:
    """Import heart rate data from a file."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Import heart rate data")

    try:
        file_path = args.file_path
        format_hint = args.format
        notes = args.notes
        validate_only = args.validate_only

        print(f"📁 Importing heart rate data from: {file_path}")

        # Import the data
        session = HeartRateDataImporter.import_from_file(file_path, format_hint)

        print(f"✅ Successfully imported data:")
        print(f"   📊 Format: {session.format}")
        print(f"   🕐 Duration: {session.duration_minutes} minutes")
        print(f"   📈 Data points: {session.data_points_count}")
        print(f"   💓 Average HR: {session.average_heart_rate:.1f} BPM")
        print(f"   📉 Min HR: {session.min_heart_rate:.1f} BPM")
        print(f"   📈 Max HR: {session.max_heart_rate:.1f} BPM")
        print(f"   🕐 Start: {session.start_time}")
        print(f"   🕐 End: {session.end_time}")

        # Validate the data
        print("\n🔍 Validating data quality...")
        is_valid, errors = HeartRateDataValidator.validate_session(session)

        if not is_valid:
            print("❌ Data validation failed:")
            for error in errors:
                print(f"   ⚠️  {error}")

            if not validate_only:
                response = input(
                    "\n❓ Data has quality issues. Continue with import anyway? (y/N): "
                )
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
            manager = HeartRateDataManager(db)
            record = manager.store_session(session)

        print(f"✅ Successfully stored heart rate data with ID: {record.id}")
        print(f"🔗 File hash: {record.data_hash[:16]}...")

        return 0

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return 1
    except ValueError as e:
        print(f"❌ Invalid data format: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
