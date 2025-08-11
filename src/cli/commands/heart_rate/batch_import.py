"""
Batch import heart rate data from a directory.
"""

import argparse
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.lib.heart_rate_manager import (
    HeartRateDataImporter,
    HeartRateDataValidator,
    HeartRateDataManager,
)
from src.db.conn import get_db
from src.const import CONST


def get_heart_rate_files(directory: str, recursive: bool = False) -> List[Path]:
    """Get all heart rate data files from a directory."""
    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    # Supported file extensions
    extensions = {".csv", ".json", ".txt"}

    files = []

    if recursive:
        # Recursive search
        for file_path in directory_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                files.append(file_path)
    else:
        # Non-recursive search
        for file_path in directory_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                files.append(file_path)

    return sorted(files)


def import_single_file(
    file_path: Path,
    format_hint: Optional[str] = None,
    notes: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """Import a single heart rate data file."""
    result = {
        "file_path": str(file_path),
        "success": False,
        "error": None,
        "session_info": None,
        "validation_passed": False,
        "validation_errors": [],
    }

    try:
        # Import the data
        session = HeartRateDataImporter.import_from_file(str(file_path), format_hint)
        result["session_info"] = {
            "format": session.format,
            "duration_minutes": session.duration_minutes,
            "data_points_count": session.data_points_count,
            "average_heart_rate": session.average_heart_rate,
            "min_heart_rate": session.min_heart_rate,
            "max_heart_rate": session.max_heart_rate,
            "start_time": session.start_time,
            "end_time": session.end_time,
        }

        # Validate the data
        is_valid, errors = HeartRateDataValidator.validate_session(session)
        result["validation_passed"] = is_valid
        result["validation_errors"] = errors

        if not dry_run and is_valid:
            # Store in database
            with get_db(CONST.DATABASE_URL) as db:
                manager = HeartRateDataManager(db)
                if notes:
                    session.notes = notes

                record = manager.store_session(session)
                result["record_id"] = record.id
                result["success"] = True

        elif dry_run:
            result["success"] = True  # Consider it successful for dry run

    except Exception as e:
        result["error"] = str(e)

    return result


def batch_import_heart_rate_data(args: argparse.Namespace) -> int:
    """Batch import heart rate data from a directory."""
    try:
        directory = args.directory
        recursive = args.recursive
        format_hint = args.format
        notes = args.notes
        dry_run = args.dry_run
        max_workers = args.max_workers

        print(f"📁 Batch importing heart rate data from: {directory}")
        if recursive:
            print("   🔍 Recursive search enabled")
        if dry_run:
            print("   🧪 DRY RUN MODE - no data will be stored")

        # Get all heart rate files
        files = get_heart_rate_files(directory, recursive)

        if not files:
            print("❌ No heart rate data files found in directory")
            return 1

        print(f"📊 Found {len(files)} heart rate data files")

        # Import files
        successful_imports = 0
        failed_imports = 0
        validation_failures = 0

        if max_workers > 1 and len(files) > 1:
            # Use parallel processing for multiple files
            print(f"⚡ Using {max_workers} parallel workers")

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all import tasks
                future_to_file = {
                    executor.submit(
                        import_single_file, file_path, format_hint, notes, dry_run
                    ): file_path
                    for file_path in files
                }

                # Process results as they complete
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        _print_import_result(result, file_path)

                        if result["success"]:
                            successful_imports += 1
                        else:
                            failed_imports += 1

                        if not result["validation_passed"]:
                            validation_failures += 1

                    except Exception as e:
                        print(f"❌ Error processing {file_path.name}: {e}")
                        failed_imports += 1
        else:
            # Sequential processing
            for file_path in files:
                result = import_single_file(file_path, format_hint, notes, dry_run)
                _print_import_result(result, file_path)

                if result["success"]:
                    successful_imports += 1
                else:
                    failed_imports += 1

                if not result["validation_passed"]:
                    validation_failures += 1

        # Print summary
        print(f"\n📊 Batch import summary:")
        print(f"   ✅ Successful imports: {successful_imports}")
        print(f"   ❌ Failed imports: {failed_imports}")
        print(f"   ⚠️  Validation failures: {validation_failures}")
        print(f"   📁 Total files processed: {len(files)}")

        if dry_run:
            print("   🧪 DRY RUN MODE - no data was actually stored")

        return 0 if failed_imports == 0 else 1

    except Exception as e:
        print(f"❌ Error during batch import: {e}")
        return 1


def _print_import_result(result: dict, file_path: Path):
    """Print the result of importing a single file."""
    if result["success"]:
        if "record_id" in result:
            print(f"✅ {file_path.name} - ID: {result['record_id']}")
        else:
            print(f"✅ {file_path.name} - (dry run)")
    else:
        print(f"❌ {file_path.name} - {result['error']}")

    if result["session_info"]:
        info = result["session_info"]
        print(
            f"   📊 {info['format'].upper()}, {info['duration_minutes']} min, {info['data_points_count']} points"
        )
        print(
            f"   💓 HR: {info['average_heart_rate']:.1f} avg ({info['min_heart_rate']:.1f}-{info['max_heart_rate']:.1f})"
        )

    if result["validation_errors"]:
        print(f"   ⚠️  Validation issues:")
        for error in result["validation_errors"]:
            print(f"      - {error}")
