"""
Delete weight measurements.
"""
# pylint: disable=bad-builtin

import argparse
from tabulate import tabulate

from src.lib.weight_manager import WeightDataManager
from src.db.conn import get_db
from src.config import get_database_config
from src.lib.cli_display import show_database_banner


def delete_weight_measurement(args: argparse.Namespace) -> int:
    """Delete a weight measurement by ID."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Delete weight measurement")

    try:
        with get_db(url=config.url) as db:
            manager = WeightDataManager(db)

            # Get measurement ID
            measurement_id = getattr(args, "id", None)

            if measurement_id is None:
                # Interactive selection
                measurements = manager.get_all()

                if not measurements:
                    print("❌ No measurements found")
                    return 1

                # Show recent measurements
                print("📊 Recent weight measurements:")
                table_data = []
                for m in measurements[:20]:
                    table_data.append(
                        [
                            m.id,
                            m.measurement_time.strftime("%Y-%m-%d %H:%M"),
                            f"{m.weight_kg} kg",
                            m.measurement_conditions or "-",
                            m.data_source,
                        ]
                    )

                headers = ["ID", "Time", "Weight", "Conditions", "Source"]
                print("\n" + tabulate(table_data, headers=headers, tablefmt="simple"))

                if len(measurements) > 20:
                    print(f"\n   ... and {len(measurements) - 20} more")

                # Get ID from user
                try:
                    measurement_id = int(input("\n🔢 Enter measurement ID to delete: "))
                except ValueError:
                    print("❌ Invalid ID")
                    return 1

            # Get the measurement
            measurement = manager.get_by_id(measurement_id)

            if not measurement:
                print(f"❌ Measurement with ID {measurement_id} not found")
                return 1

            # Show details and confirm
            print("\n⚠️  You are about to delete this measurement:")
            print(f"   ID: {measurement.id}")
            print(f"   Weight: {measurement.weight_kg} kg")
            print(f"   Time: {measurement.measurement_time}")
            if measurement.measurement_conditions:
                print(f"   Conditions: {measurement.measurement_conditions}")
            if measurement.notes:
                print(f"   Notes: {measurement.notes}")

            confirm = input("\n❓ Are you sure you want to delete this? (y/N): ")
            if confirm.lower() not in ["y", "yes"]:
                print("❌ Deletion cancelled")
                return 1

            # Delete
            success = manager.delete_measurement(measurement_id)

            if success:
                print(f"✅ Successfully deleted measurement ID: {measurement_id}")
                return 0

            print(f"❌ Failed to delete measurement ID: {measurement_id}")
            return 1

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
