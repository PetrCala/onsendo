"""
List and query exercise sessions.
"""

import argparse
from datetime import datetime
from typing import Optional

from src.lib.exercise_manager import ExerciseDataManager
from src.types.exercise import ExerciseType
from src.db.conn import get_db
from src.config import get_database_config


def list_exercise_sessions(args: argparse.Namespace) -> int:
    """List exercise sessions with optional filtering."""
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    try:
        exercise_type = args.type
        unlinked_only = args.unlinked_only
        visit_id = args.visit_id
        date_range = args.date_range
        limit = args.limit

        with get_db(url=config.url) as db:
            manager = ExerciseDataManager(db)

            # Get sessions based on filters
            if visit_id:
                sessions = manager.get_by_visit(visit_id)
                print(f"📊 Exercise sessions linked to visit {visit_id}:")
            elif unlinked_only:
                sessions = manager.get_unlinked()
                print("📊 Unlinked exercise sessions:")
            elif exercise_type:
                ex_type = ExerciseType(exercise_type)
                sessions = manager.get_by_exercise_type(ex_type)
                print(f"📊 {exercise_type.upper()} exercise sessions:")
            elif date_range:
                start_str, end_str = date_range.split(",")
                start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d")
                end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d")
                sessions = manager.get_by_date_range(start_date, end_date)
                print(f"📊 Exercise sessions from {start_str} to {end_str}:")
            else:
                # Get all sessions (with limit)
                sessions = (
                    db.query(manager.db_session.query(type(sessions[0])).limit(limit).all())
                    if limit
                    else []
                )
                print("📊 All exercise sessions:")

            if not sessions:
                print("   No sessions found.")
                return 0

            # Apply limit if specified
            if limit and len(sessions) > limit:
                sessions = sessions[:limit]
                print(f"   (Showing first {limit} results)")

            # Display sessions
            print(f"\n   Total: {len(sessions)} sessions\n")

            for session in sessions:
                _print_session_summary(session)
                print()

        return 0

    except Exception as e:
        print(f"❌ Error listing exercise sessions: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _print_session_summary(session):
    """Print a summary of an exercise session."""
    print(f"   🆔 ID: {session.id}")
    print(f"   🏃 Type: {session.exercise_type}")
    if session.activity_name:
        print(f"   📝 Activity: {session.activity_name}")
    print(
        f"   🕐 {session.recording_start.strftime('%Y-%m-%d %H:%M')} "
        f"- {session.recording_end.strftime('%H:%M')} ({session.duration_minutes} min)"
    )
    if session.distance_km:
        pace = session.duration_minutes / session.distance_km
        print(f"   📏 Distance: {session.distance_km:.2f} km (pace: {pace:.1f} min/km)")
    if session.calories_burned:
        print(f"   🔥 Calories: {session.calories_burned}")
    if session.avg_heart_rate:
        print(
            f"   💓 HR: {session.avg_heart_rate:.0f} avg "
            f"({session.min_heart_rate:.0f}-{session.max_heart_rate:.0f})"
        )
    if session.elevation_gain_m:
        print(f"   ⛰️  Elevation: +{session.elevation_gain_m:.0f} m")
    if session.visit_id:
        print(f"   🔗 Linked to visit: {session.visit_id}")
    if session.heart_rate_id:
        print(f"   🔗 Linked to HR data: {session.heart_rate_id}")
    if session.notes:
        print(f"   📝 Notes: {session.notes}")
