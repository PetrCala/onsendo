"""
Manually add a weight measurement.
"""
# pylint: disable=bad-builtin

import argparse
from datetime import datetime

from src.lib.weight_manager import (
    WeightMeasurement,
    WeightDataValidator,
    WeightDataManager,
)
from src.db.conn import get_db
from src.config import get_database_config
from src.lib.cli_display import show_database_banner


def add_weight_measurement(args: argparse.Namespace) -> int:
    """Add a weight measurement manually (interactive or via flags)."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Add weight measurement")

    try:
        # Check if we have all required arguments (non-interactive mode)
        if hasattr(args, "weight") and args.weight:
            weight_kg = args.weight
            timestamp = args.time if hasattr(args, "time") and args.time else datetime.now()
            conditions = args.conditions if hasattr(args, "conditions") else None
            time_of_day = args.time_of_day if hasattr(args, "time_of_day") else None
            notes = args.notes if hasattr(args, "notes") else None
        else:
            # Interactive mode
            print("📝 Add new weight measurement (interactive mode)")
            print("=" * 60)

            # Get weight
            while True:
                weight_input = input("\n⚖️  Weight (kg): ")
                try:
                    weight_kg = float(weight_input)
                    if 40 <= weight_kg <= 200:
                        break
                    print(
                        "   ⚠️  Please enter a weight between 40 and 200 kg"
                    )
                except ValueError:
                    print("   ⚠️  Please enter a valid number")

            # Get timestamp (optional, defaults to now)
            timestamp_input = input(
                "\n🕐 Measurement time (YYYY-MM-DD HH:MM:SS, press Enter for now): "
            ).strip()

            if timestamp_input:
                try:
                    timestamp = datetime.strptime(timestamp_input, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        timestamp = datetime.strptime(timestamp_input, "%Y-%m-%d")
                    except ValueError:
                        print(
                            "   ⚠️  Invalid format, using current time"
                        )
                        timestamp = datetime.now()
            else:
                timestamp = datetime.now()

            # Get conditions (optional)
            print(
                "\n📝 Measurement conditions (optional):"
            )
            print(
                "   Options: fasted, after_meal, post_workout, before_workout, normal"
            )
            conditions = input("   Conditions (press Enter to skip): ").strip() or None

            # Get time of day (optional)
            print("\n🌅 Time of day (optional):")
            print("   Options: morning, afternoon, evening, night")
            time_of_day = input("   Time of day (press Enter to skip): ").strip() or None

            # Get notes (optional)
            notes = input("\n💬 Notes (press Enter to skip): ").strip() or None

        # Create measurement object
        measurement = WeightMeasurement(
            measurement_time=timestamp,
            weight_kg=weight_kg,
            data_source="manual",
            measurement_conditions=conditions,
            time_of_day=time_of_day,
            notes=notes,
        )

        # Validate
        print("\n🔍 Validating measurement...")
        is_valid, errors = WeightDataValidator.validate_measurement(measurement)

        if not is_valid:
            print("❌ Validation failed:")
            for error in errors:
                print(f"   ⚠️  {error}")
            return 1

        print("✅ Measurement is valid")

        # Confirm before saving
        print("\n📋 Summary:")
        print(f"   ⚖️  Weight: {measurement.weight_kg} kg")
        print(f"   🕐 Time: {measurement.measurement_time}")
        if measurement.measurement_conditions:
            print(f"   📝 Conditions: {measurement.measurement_conditions}")
        if measurement.time_of_day:
            print(f"   🌅 Time of day: {measurement.time_of_day}")
        if measurement.notes:
            print(f"   💬 Notes: {measurement.notes}")

        confirm = input("\n❓ Save this measurement? (Y/n): ")
        if confirm.lower() in ["n", "no"]:
            print("❌ Cancelled")
            return 1

        # Store in database
        print("\n💾 Storing measurement in database...")

        with get_db(url=config.url) as db:
            manager = WeightDataManager(db)
            record = manager.store_measurement(measurement)

        print(f"✅ Successfully stored measurement with ID: {record.id}")

        return 0

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
