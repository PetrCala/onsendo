"""
List weight measurements.
"""

import argparse
import json
from datetime import datetime
from tabulate import tabulate

from src.lib.weight_manager import WeightDataManager
from src.db.conn import get_db
from src.config import get_database_config


def list_weight_measurements(args: argparse.Namespace) -> int:
    """List weight measurements with optional filtering."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    try:
        with get_db(url=config.url) as db:
            manager = WeightDataManager(db)

            # Get measurements
            if hasattr(args, "date_range") and args.date_range:
                # Parse date range
                date_parts = args.date_range.split(",")
                if len(date_parts) != 2:
                    print(
                        "❌ Invalid date range format. Use: YYYY-MM-DD,YYYY-MM-DD"
                    )
                    return 1

                start_str, end_str = date_parts
                start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d")
                end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d")

                measurements = manager.get_by_date_range(start_date, end_date)
                print(
                    f"📊 Weight measurements from {start_str} to {end_str}:"
                )
            else:
                measurements = manager.get_all()
                print("📊 All weight measurements:")

            if not measurements:
                print("   No measurements found")
                return 0

            # Apply limit if specified
            if hasattr(args, "limit") and args.limit:
                measurements = measurements[: args.limit]

            # Determine output format
            output_format = "table"
            if hasattr(args, "format") and args.format:
                output_format = args.format

            # Display based on format
            if output_format == "json":
                # JSON output
                data = []
                for m in measurements:
                    data.append(
                        {
                            "id": m.id,
                            "measurement_time": m.measurement_time.isoformat(),
                            "weight_kg": m.weight_kg,
                            "measurement_conditions": m.measurement_conditions,
                            "hydrated_before": m.hydrated_before,
                            "data_source": m.data_source,
                            "notes": m.notes,
                        }
                    )
                print(json.dumps(data, indent=2))

            else:
                # Table output (default)
                table_data = []
                for m in measurements:
                    # Format hydration status
                    if m.hydrated_before is None:
                        hydration = "-"
                    elif m.hydrated_before:
                        hydration = "Yes"
                    else:
                        hydration = "No"

                    table_data.append(
                        [
                            m.id,
                            m.measurement_time.strftime("%Y-%m-%d %H:%M"),
                            f"{m.weight_kg} kg",
                            m.measurement_conditions or "-",
                            hydration,
                            m.data_source,
                            (m.notes[:30] + "...") if m.notes and len(m.notes) > 30 else (m.notes or "-"),
                        ]
                    )

                headers = [
                    "ID",
                    "Time",
                    "Weight",
                    "Conditions",
                    "Hydrated",
                    "Source",
                    "Notes",
                ]

                print("\n" + tabulate(table_data, headers=headers, tablefmt="simple"))

            print(f"\n✅ Total: {len(measurements)} measurement(s)")

        return 0

    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
