"""
Link command for Strava integration.

Provides linking of already-imported exercise sessions or heart rate data
to onsen visits.
"""

from datetime import datetime, timedelta

from loguru import logger

from src.config import get_database_config
from src.db.conn import get_db
from src.db.models import ExerciseSession, HeartRateData, OnsenVisit
from src.lib.exercise_manager import ExerciseDataManager
from src.lib.heart_rate_manager import HeartRateDataManager


def cmd_strava_link(args):
    """
    Link already-imported Strava activity to visit.

    Links existing exercise sessions or heart rate records to onsen visits,
    either manually or with auto-suggestions based on timestamps.

    Usage:
        poetry run onsendo strava link --exercise 42 --visit 123
        poetry run onsendo strava link --heart-rate 10 --visit 123
        poetry run onsendo strava link --exercise 42 --auto-match

    Arguments:
        --exercise ID: Exercise session ID to link
        --heart-rate ID: Heart rate record ID to link
        --visit ID: Visit ID to link to
        --auto-match: Auto-suggest nearby visits based on timestamp

    Examples:
        # Link exercise to specific visit
        poetry run onsendo strava link --exercise 42 --visit 123

        # Link heart rate to specific visit
        poetry run onsendo strava link --heart-rate 10 --visit 123

        # Auto-suggest visits for exercise
        poetry run onsendo strava link --exercise 42 --auto-match

        # Auto-suggest visits for heart rate
        poetry run onsendo strava link --heart-rate 10 --auto-match
    """
    exercise_id = args.exercise if hasattr(args, "exercise") and args.exercise else None
    hr_id = args.heart_rate if hasattr(args, "heart_rate") and args.heart_rate else None
    visit_id = args.visit if hasattr(args, "visit") and args.visit else None
    auto_match = args.auto_match if hasattr(args, "auto_match") else False

    # Validate arguments
    if not exercise_id and not hr_id:
        print("Error: You must specify either --exercise or --heart-rate")
        return

    if exercise_id and hr_id:
        print("Error: Specify only one of --exercise or --heart-rate")
        return

    if not visit_id and not auto_match:
        print("Error: You must specify either --visit or --auto-match")
        return

    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Use database session for all operations
    with get_db(url=config.url) as db:
        # Handle exercise linking
        if exercise_id:
            # Fetch exercise session
            try:
                exercise = db.query(ExerciseSession).filter_by(id=exercise_id).first()

                if not exercise:
                    print(f"Error: Exercise session {exercise_id} not found")
                    return

                print(f"Exercise Session: {exercise_id}")
                print(f"  Type: {exercise.exercise_type}")
                print(f"  Start: {exercise.start_time}")
                print(f"  End: {exercise.end_time}")

            except Exception as e:
                logger.exception(f"Failed to fetch exercise {exercise_id}")
                print(f"Error: {e}")
                return

            # Auto-match visits
            if auto_match:
                print("\nSearching for nearby visits...")
                visit_id = _find_nearby_visit(db, exercise.start_time)

                if not visit_id:
                    print("No nearby visits found (±2 hours)")
                    return

            # Link to visit
            try:
                manager = ExerciseDataManager(db)
                manager.link_to_visit(exercise_id, visit_id)
                print(f"\n✓ Linked exercise {exercise_id} to visit {visit_id}")

            except Exception as e:
                logger.exception(
                    f"Failed to link exercise {exercise_id} to visit {visit_id}"
                )
                print(f"Error: {e}")

        # Handle heart rate linking
        if hr_id:
            # Fetch heart rate record
            try:
                hr_record = db.query(HeartRateData).filter_by(id=hr_id).first()

                if not hr_record:
                    print(f"Error: Heart rate record {hr_id} not found")
                    return

                print(f"Heart Rate Record: {hr_id}")
                print(f"  Start: {hr_record.start_time}")
                print(f"  End: {hr_record.end_time}")
                print(f"  Source: {hr_record.data_source}")

            except Exception as e:
                logger.exception(f"Failed to fetch heart rate record {hr_id}")
                print(f"Error: {e}")
                return

            # Auto-match visits
            if auto_match:
                print("\nSearching for nearby visits...")
                visit_id = _find_nearby_visit(db, hr_record.start_time)

                if not visit_id:
                    print("No nearby visits found (±2 hours)")
                    return

            # Link to visit
            try:
                hr_manager = HeartRateDataManager(db)
                hr_manager.link_to_visit(hr_id, visit_id)
                print(f"\n✓ Linked heart rate {hr_id} to visit {visit_id}")

            except Exception as e:
                logger.exception(
                    f"Failed to link heart rate {hr_id} to visit {visit_id}"
                )
                print(f"Error: {e}")


def _find_nearby_visit(db, activity_time: datetime) -> int:
    """
    Find nearby visit within ±2 hours of activity time.

    Args:
        db: Database session
        activity_time: Activity timestamp

    Returns:
        Visit ID if found, None otherwise
    """
    search_start = activity_time - timedelta(hours=2)
    search_end = activity_time + timedelta(hours=2)

    visits = (
        db.query(OnsenVisit)
        .filter(OnsenVisit.visit_date >= search_start.date())
        .filter(OnsenVisit.visit_date <= search_end.date())
        .order_by(OnsenVisit.visit_date.desc(), OnsenVisit.visit_time.desc())
        .limit(5)
        .all()
    )

    if not visits:
        return None

    print("  Suggested visits:")
    for i, visit in enumerate(visits, 1):
        visit_datetime = datetime.combine(
            visit.visit_date, visit.visit_time or datetime.min.time()
        )
        time_diff = abs((visit_datetime - activity_time).total_seconds() / 60)
        print(
            f"    {i}. [ID: {visit.id}] {visit.visit_date} "
            f"at {visit.visit_time or 'N/A'} ({time_diff:.0f} min from activity)"
        )

    # Return first (closest) suggestion
    best_match = visits[0]
    print(f"\n  Using closest match: Visit {best_match.id}")
    return best_match.id


def configure_args(parser):
    """Configure argument parser for link command."""
    parser.add_argument(
        "--exercise",
        type=int,
        help="Exercise session ID to link",
    )
    parser.add_argument(
        "--heart-rate",
        type=int,
        help="Heart rate record ID to link",
    )
    parser.add_argument(
        "--visit",
        type=int,
        help="Visit ID to link to",
    )
    parser.add_argument(
        "--auto-match",
        action="store_true",
        help="Auto-suggest nearby visits based on timestamp",
    )
