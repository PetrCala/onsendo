"""
Link/unlink exercise sessions to visits and heart rate data.
"""

import argparse

from src.lib.exercise_manager import ExerciseDataManager
from src.db.conn import get_db
from src.const import CONST


def link_exercise(args: argparse.Namespace) -> int:
    """Link exercise session to a visit or heart rate record."""
    try:
        exercise_id = args.exercise_id
        visit_id = args.visit
        heart_rate_id = args.heart_rate
        auto_match = args.auto_match
        unlink = args.unlink

        with get_db(CONST.DATABASE_URL) as db:
            manager = ExerciseDataManager(db)

            # Verify exercise exists
            exercise = manager.get_by_id(exercise_id)
            if not exercise:
                print(f"❌ Exercise session {exercise_id} not found")
                return 1

            if unlink:
                # Unlink from visit and/or heart rate
                if visit_id or exercise.visit_id:
                    if manager.unlink_from_visit(exercise_id):
                        print(f"✅ Unlinked exercise {exercise_id} from visit")
                    else:
                        print(f"❌ Failed to unlink from visit")
                        return 1

                if heart_rate_id or exercise.heart_rate_id:
                    if manager.unlink_from_heart_rate(exercise_id):
                        print(f"✅ Unlinked exercise {exercise_id} from heart rate")
                    else:
                        print(f"❌ Failed to unlink from heart rate")
                        return 1

                return 0

            if auto_match:
                # Suggest potential visits based on timestamps
                suggestions = manager.suggest_visit_links(exercise_id)

                if not suggestions:
                    print(f"❌ No potential visit matches found for exercise {exercise_id}")
                    return 1

                print(f"🔍 Found {len(suggestions)} potential visit matches:")
                for i, (vid, description) in enumerate(suggestions, 1):
                    print(f"   {i}. Visit ID {vid}: {description}")

                # Prompt user to select
                response = input(
                    "\n❓ Select a visit to link (number), or 'n' to cancel: "
                )  # pylint: disable=bad-builtin

                if response.lower() == "n":
                    print("❌ Cancelled")
                    return 0

                try:
                    selection = int(response) - 1
                    if 0 <= selection < len(suggestions):
                        visit_id = suggestions[selection][0]
                    else:
                        print("❌ Invalid selection")
                        return 1
                except ValueError:
                    print("❌ Invalid input")
                    return 1

            # Link to visit
            if visit_id:
                if manager.link_to_visit(exercise_id, visit_id):
                    print(f"✅ Linked exercise {exercise_id} to visit {visit_id}")
                else:
                    print(f"❌ Failed to link to visit {visit_id}")
                    return 1

            # Link to heart rate
            if heart_rate_id:
                if manager.link_to_heart_rate(exercise_id, heart_rate_id):
                    print(f"✅ Linked exercise {exercise_id} to heart rate {heart_rate_id}")
                else:
                    print(f"❌ Failed to link to heart rate {heart_rate_id}")
                    return 1

        return 0

    except Exception as e:
        print(f"❌ Error linking exercise: {e}")
        import traceback

        traceback.print_exc()
        return 1
