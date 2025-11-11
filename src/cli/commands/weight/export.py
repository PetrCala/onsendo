"""
Export weight measurements to file.
"""

import argparse
import csv
import json
import os
from datetime import datetime

from src.lib.weight_manager import WeightDataManager
from src.db.conn import get_db
from src.config import get_database_config
from src.paths import PATHS


def export_weight_data(args: argparse.Namespace) -> int:
    """Export weight measurements to CSV or JSON file."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    try:
        # Determine format
        export_format = "csv"
        if hasattr(args, "format") and args.format:
            export_format = args.format.lower()

        if export_format not in ["csv", "json"]:
            print(f"❌ Unsupported format: {export_format}. Use 'csv' or 'json'")
            return 1

        # Determine output path
        if hasattr(args, "output") and args.output:
            output_path = args.output
        else:
            # Generate default output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"weight_export_{timestamp}.{export_format}"
            output_path = os.path.join(PATHS.OUTPUT_DIR, filename)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Get measurements from database
        with get_db(url=config.url) as db:
            manager = WeightDataManager(db)

            if hasattr(args, "date_range") and args.date_range:
                # Parse date range
                date_parts = args.date_range.split(",")
                if len(date_parts) != 2:
                    print("❌ Invalid date range format. Use: YYYY-MM-DD,YYYY-MM-DD")
                    return 1

                start_str, end_str = date_parts
                start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d")
                end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d")

                measurements = manager.get_by_date_range(start_date, end_date)
                print(f"📊 Exporting measurements from {start_str} to {end_str}")
            else:
                measurements = manager.get_all()
                print("📊 Exporting all measurements")

        if not measurements:
            print("❌ No measurements to export")
            return 0

        # Export based on format
        print(
            f"💾 Exporting {len(measurements)} measurement(s) to {export_format.upper()}..."
        )

        if export_format == "json":
            export_json(measurements, output_path)
        elif export_format == "csv":
            export_csv(measurements, output_path)

        print(f"✅ Exported {len(measurements)} measurement(s) to: {output_path}")

        # Show file size
        file_size = os.path.getsize(output_path)
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"

        print(f"📦 File size: {size_str}")

        return 0

    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


def export_csv(measurements, output_path: str) -> None:
    """
    Export measurements to CSV format.

    Args:
        measurements: List of WeightMeasurementModel objects
        output_path: Path to output CSV file
    """
    fieldnames = [
        "id",
        "measurement_time",
        "weight_kg",
        "measurement_conditions",
        "time_of_day",
        "hydrated_before",
        "data_source",
        "notes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for m in measurements:
            writer.writerow(
                {
                    "id": m.id,
                    "measurement_time": m.measurement_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "weight_kg": m.weight_kg,
                    "measurement_conditions": m.measurement_conditions or "",
                    "time_of_day": m.time_of_day or "",
                    "hydrated_before": (
                        m.hydrated_before if m.hydrated_before is not None else ""
                    ),
                    "data_source": m.data_source,
                    "notes": m.notes or "",
                }
            )


def export_json(measurements, output_path: str) -> None:
    """
    Export measurements to JSON format.

    Args:
        measurements: List of WeightMeasurementModel objects
        output_path: Path to output JSON file
    """
    data = []
    for m in measurements:
        data.append(
            {
                "id": m.id,
                "measurement_time": m.measurement_time.isoformat(),
                "weight_kg": m.weight_kg,
                "measurement_conditions": m.measurement_conditions,
                "time_of_day": m.time_of_day,
                "hydrated_before": m.hydrated_before,
                "data_source": m.data_source,
                "data_file_path": m.data_file_path,
                "data_hash": m.data_hash,
                "notes": m.notes,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
        )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
