"""
Batch import exercise data from a directory.
"""

import argparse
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.lib.exercise_manager import (
    ExerciseDataImporter,
    ExerciseDataValidator,
    ExerciseDataManager,
)
from src.db.conn import get_db
from src.const import CONST


def get_exercise_files(directory: str, recursive: bool = False) -> list[Path]:
    """Get all exercise data files from a directory."""
    directory_path = Path(directory)

    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory_path.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    # Supported file extensions
    extensions = {".csv", ".json", ".gpx", ".tcx", ".xml"}

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
    """Import a single exercise data file."""
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
        session = ExerciseDataImporter.import_from_file(str(file_path), format_hint)
        result["session_info"] = {
            "exercise_type": session.exercise_type.value,
            "activity_name": session.activity_name,
            "duration_minutes": session.duration_minutes,
            "distance_km": session.distance_km,
            "calories_burned": session.calories_burned,
            "avg_heart_rate": session.avg_heart_rate,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "data_points_count": len(session.data_points) if session.data_points else 0,
        }

        # Validate the data
        is_valid, errors = ExerciseDataValidator.validate_session(session)
        result["validation_passed"] = is_valid
        result["validation_errors"] = errors

        if not dry_run and is_valid:
            # Store in database
            with get_db(CONST.DATABASE_URL) as db:
                manager = ExerciseDataManager(db)
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


def batch_import_exercise_data(args: argparse.Namespace) -> int:
    """Batch import exercise data from a directory."""
    try:
        directory = args.directory
        recursive = args.recursive
        format_hint = args.format
        notes = args.notes
        dry_run = args.dry_run
        max_workers = args.max_workers

        print(f"📁 Batch importing exercise data from: {directory}")
        if recursive:
            print("   🔍 Recursive search enabled")
        if dry_run:
            print("   🧪 DRY RUN MODE - no data will be stored")

        # Get all exercise files
        files = get_exercise_files(directory, recursive)

        if not files:
            print("❌ No exercise data files found in directory")
            return 1

        print(f"📊 Found {len(files)} exercise data files")

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
        import traceback

        traceback.print_exc()
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
        distance_str = f"{info['distance_km']:.2f} km" if info["distance_km"] else "N/A"
        activity = info["activity_name"] or info["exercise_type"]
        print(
            f"   📊 {activity.upper()}, {info['duration_minutes']} min, {distance_str}"
        )

        if info["avg_heart_rate"]:
            print(f"   💓 HR: {info['avg_heart_rate']:.0f} avg")

    if result["validation_errors"]:
        print("   ⚠️  Validation issues:")
        for error in result["validation_errors"]:
            print(f"      - {error}")
