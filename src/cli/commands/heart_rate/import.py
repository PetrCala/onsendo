"""
Import heart rate data from files.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.lib.heart_rate_manager import (
    HeartRateDataImporter,
    HeartRateDataValidator,
    HeartRateDataManager,
)


def import_heart_rate_data(
    file_path: str,
    format_hint: Optional[str] = None,
    notes: Optional[str] = None,
    validate_only: bool = False,
) -> int:
    """Import heart rate data from a file."""
    try:
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
        manager = HeartRateDataManager()

        if notes:
            session.notes = notes

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


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Import heart rate data from various file formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported formats:
  CSV: timestamp,heart_rate[,confidence] columns
  JSON: Array of objects with timestamp and heart_rate fields
  Text: timestamp,heart_rate[,confidence] lines

Example CSV format:
  timestamp,heart_rate,confidence
  2024-01-01 10:00:00,72,0.95
  2024-01-01 10:01:00,75,0.92

Example JSON format:
  [
    {"timestamp": "2024-01-01T10:00:00", "heart_rate": 72, "confidence": 0.95},
    {"timestamp": "2024-01-01T10:01:00", "heart_rate": 75, "confidence": 0.92}
  ]
        """,
    )

    parser.add_argument("file_path", help="Path to the heart rate data file")

    parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json", "text"],
        help="Force specific file format (auto-detected if not specified)",
    )

    parser.add_argument(
        "--notes", "-n", help="Optional notes about this recording session"
    )

    parser.add_argument(
        "--validate-only",
        "-v",
        action="store_true",
        help="Only validate the data without importing to database",
    )

    args = parser.parse_args()

    # Check if file exists
    if not Path(args.file_path).exists():
        print(f"❌ File not found: {args.file_path}")
        return 1

    return import_heart_rate_data(
        args.file_path,
        format_hint=args.format,
        notes=args.notes,
        validate_only=args.validate_only,
    )


if __name__ == "__main__":
    sys.exit(main())
