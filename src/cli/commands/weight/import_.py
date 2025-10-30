"""
Import weight data from files.
"""
# pylint: disable=bad-builtin

import argparse

from src.lib.weight_manager import (
    WeightDataImporter,
    WeightDataValidator,
    WeightDataManager,
)
from src.db.conn import get_db
from src.config import get_database_config
from src.lib.cli_display import show_database_banner


def import_weight_data(args: argparse.Namespace) -> int:
    """Import weight data from a file."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Import weight data")

    try:
        file_path = args.file_path
        format_hint = args.format
        notes = args.notes
        validate_only = args.validate_only

        print(f"📁 Importing weight data from: {file_path}")

        # Import the data
        measurements = WeightDataImporter.import_from_file(file_path, format_hint)

        print(f"✅ Successfully imported {len(measurements)} measurement(s)")

        # Show first few measurements
        for idx, measurement in enumerate(measurements[:5], 1):
            print(f"\n   Measurement {idx}:")
            print(f"   ⚖️  Weight: {measurement.weight_kg} kg")
            print(f"   🕐 Time: {measurement.measurement_time}")
            if measurement.measurement_conditions:
                print(f"   📝 Conditions: {measurement.measurement_conditions}")
            if measurement.time_of_day:
                print(f"   🌅 Time of day: {measurement.time_of_day}")

        if len(measurements) > 5:
            print(f"\n   ... and {len(measurements) - 5} more measurement(s)")

        # Validate all measurements
        print("\n🔍 Validating data quality...")
        validation_errors = []

        for idx, measurement in enumerate(measurements, 1):
            is_valid, errors = WeightDataValidator.validate_measurement(measurement)
            if not is_valid:
                validation_errors.append((idx, errors))

        if validation_errors:
            print(f"❌ Validation failed for {len(validation_errors)} measurement(s):")
            for idx, errors in validation_errors[:5]:
                print(f"\n   Measurement {idx}:")
                for error in errors:
                    print(f"   ⚠️  {error}")

            if len(validation_errors) > 5:
                print(f"\n   ... and {len(validation_errors) - 5} more validation errors")

            if not validate_only:
                response = input(
                    "\n❓ Data has quality issues. Continue with import anyway? (y/N): "
                )
                if response.lower() not in ["y", "yes"]:
                    print("❌ Import cancelled.")
                    return 1
        else:
            print("✅ All measurements passed validation")

        if validate_only:
            print("✅ Validation complete (import not performed)")
            return 0

        # Store in database
        print(f"\n💾 Storing {len(measurements)} measurement(s) in database...")

        # Add notes if provided
        if notes:
            for measurement in measurements:
                if not measurement.notes:
                    measurement.notes = notes

        with get_db(url=config.url) as db:
            manager = WeightDataManager(db)
            records = manager.store_measurements_bulk(measurements)

        print(
            f"✅ Successfully stored {len(records)} measurement(s) "
            f"(IDs: {records[0].id}-{records[-1].id})"
        )

        if records[0].data_hash:
            print(f"🔗 File hash: {records[0].data_hash[:16]}...")

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
