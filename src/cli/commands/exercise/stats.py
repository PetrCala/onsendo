"""
Show exercise statistics and summaries.
"""

import argparse
from datetime import datetime, timedelta

from src.lib.exercise_manager import ExerciseDataManager
from src.types.exercise import ExerciseType
from src.db.conn import get_db
from src.const import CONST


def show_exercise_stats(args: argparse.Namespace) -> int:
    """Show exercise statistics for a time period."""
    try:
        week = args.week
        month = args.month
        year = args.year or datetime.now().year
        exercise_type = args.type

        with get_db(CONST.DATABASE_URL) as db:
            manager = ExerciseDataManager(db)

            # Determine date range
            if week:
                # Parse week start date
                week_start = datetime.strptime(week, "%Y-%m-%d")
                week_end = week_start + timedelta(days=7)
                period_name = f"Week of {week}"
            elif month:
                # Month stats
                month_start = datetime(year, month, 1)
                if month == 12:
                    month_end = datetime(year + 1, 1, 1)
                else:
                    month_end = datetime(year, month + 1, 1)
                week_start = month_start
                week_end = month_end
                period_name = f"{month_start.strftime('%B %Y')}"
            else:
                print("❌ Please specify either --week or --month")
                return 1

            # Get summary
            summary = manager.get_weekly_summary(week_start, week_end)

            # Display statistics
            print(f"📊 Exercise Statistics - {period_name}")
            print("=" * 60)
            print(f"\n🏃 Total Sessions: {summary.total_sessions}")

            if summary.sessions_by_type:
                print("\n📋 Sessions by Type:")
                for ex_type, count in summary.sessions_by_type.items():
                    print(f"   • {ex_type}: {count}")

            print(f"\n📏 Total Distance: {summary.total_distance_km:.2f} km")
            print(f"⏱️  Total Duration: {summary.total_duration_minutes} minutes "
                  f"({summary.total_duration_minutes / 60:.1f} hours)")

            if summary.total_calories:
                print(f"🔥 Total Calories: {summary.total_calories:,}")

            if summary.avg_heart_rate:
                print(f"💓 Average Heart Rate: {summary.avg_heart_rate:.0f} BPM")

            # Get specific type stats if requested
            if exercise_type:
                ex_type = ExerciseType(exercise_type)
                type_sessions = manager.get_by_exercise_type(ex_type)
                type_sessions_in_period = [
                    s
                    for s in type_sessions
                    if week_start <= s.recording_start <= week_end
                ]

                if type_sessions_in_period:
                    print(f"\n🎯 {exercise_type.upper()} Statistics:")
                    total_dist = sum(
                        s.distance_km for s in type_sessions_in_period if s.distance_km
                    )
                    total_dur = sum(s.duration_minutes for s in type_sessions_in_period)

                    print(f"   Sessions: {len(type_sessions_in_period)}")
                    if total_dist > 0:
                        print(f"   Distance: {total_dist:.2f} km")
                        avg_pace = total_dur / total_dist if total_dist > 0 else 0
                        print(f"   Avg Pace: {avg_pace:.1f} min/km")
                    print(f"   Duration: {total_dur} min ({total_dur / 60:.1f} hours)")

            # Rules compliance (for Onsendo Challenge)
            print("\n📖 Challenge Rules Compliance:")
            print("=" * 60)

            running_sessions = summary.sessions_by_type.get(ExerciseType.RUNNING.value, 0)
            gym_sessions = summary.sessions_by_type.get(ExerciseType.GYM.value, 0)
            hike_sessions = summary.sessions_by_type.get(ExerciseType.HIKING.value, 0)

            running_distance = sum(
                s.distance_km
                for s in manager.get_by_date_range(week_start, week_end)
                if s.exercise_type == ExerciseType.RUNNING.value and s.distance_km
            )

            # Check for long running sessions (>= 15km or >= 2.5hr)
            all_sessions = manager.get_by_date_range(week_start, week_end)
            long_run_sessions = sum(
                1
                for s in all_sessions
                if s.exercise_type == ExerciseType.RUNNING.value
                and ((s.distance_km is not None and s.distance_km >= 15.0) or s.duration_minutes >= 150)
            )

            long_exercise_completed = (hike_sessions > 0) or (long_run_sessions > 0)

            print(f"🏃 Running: {running_distance:.1f} km "
                  f"(target: 20-35 km, max: 40 km)")
            print(f"🏋️  Gym Sessions: {gym_sessions} (target: 2-4, max: 4)")
            print(
                f"⛰️  Long Exercise Session: {'✅ Yes' if long_exercise_completed else '❌ No'} "
                f"(mandatory: hike or long run >= 15km/2.5hr)"
            )

            # Check limits
            warnings = []
            if running_distance > 40:
                warnings.append(f"⚠️  Running distance ({running_distance:.1f} km) exceeds limit (40 km)")
            if gym_sessions > 4:
                warnings.append(f"⚠️  Gym sessions ({gym_sessions}) exceed limit (4)")
            if not long_exercise_completed and week:
                warnings.append(
                    "⚠️  No long exercise session this week "
                    "(mandatory: hike or long run >= 15km/2.5hr)"
                )

            if warnings:
                print("\n⚠️  Warnings:")
                for warning in warnings:
                    print(f"   {warning}")
            else:
                print("\n✅ All exercise targets within recommended ranges")

        return 0

    except Exception as e:
        print(f"❌ Error generating exercise statistics: {e}")
        import traceback

        traceback.print_exc()
        return 1
