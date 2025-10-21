"""
Create a new rule revision with interactive workflow.
"""
# pylint: disable=bad-builtin  # input() is appropriate for CLI interaction

import argparse
import json
import os
from datetime import datetime
from typing import Optional

from src.db.conn import get_db
from src.db.models import RuleRevision
from src.const import CONST
from src.paths import PATHS
from src.lib.rule_manager import (
    RuleParser,
    RuleRevisionBuilder,
    RuleMarkdownGenerator,
    RuleFileUpdater,
)
from src.types.rules import (
    WeeklyReviewMetrics,
    HealthWellbeingData,
    ReflectionData,
    RuleAdjustmentContext,
    NextWeekPlan,
    RuleModification,
    RuleRevisionData,
    AdjustmentReasonEnum,
    RevisionDurationEnum,
)
from src.lib.exercise_manager import ExerciseDataManager
from src.db.models import OnsenVisit
from src.types.exercise import ExerciseType


def create_revision(args: argparse.Namespace) -> None:
    """
    Main entry point for creating a new rule revision.

    Args:
        args: Command-line arguments (currently no arguments supported)
    """
    print("=" * 80)
    print("RULE REVISION CREATION - Rule Review Sunday")
    print("=" * 80)
    print()
    print("This interactive workflow will guide you through creating a new rule revision.")
    print("You will complete the weekly review and optionally modify rules.")
    print()

    try:
        # Phase 1: Weekly Review Data Collection
        print("PHASE 1: Weekly Review Data Collection")
        print("-" * 80)
        print()

        week_dates = collect_week_dates()
        if not week_dates:
            print("Operation cancelled.")
            return

        week_start, week_end, _, _ = week_dates

        # Auto-fetch statistics if requested
        auto_fetched_metrics = None
        # Note: argparse converts --auto-fetch to auto_fetch attribute
        auto_fetch_enabled = getattr(args, 'auto_fetch', False)
        if auto_fetch_enabled:
            print()
            print("Auto-fetching statistics from database...")
            print()
            auto_fetched_metrics = auto_fetch_week_statistics(week_start, week_end)
            print()

        metrics = collect_summary_metrics(auto_fetched_metrics)
        health = collect_health_wellbeing()
        reflections = collect_reflections()
        next_week = collect_next_week_plans()

        # Phase 2: Rule Adjustment Context
        print()
        print("PHASE 2: Rule Adjustment Context")
        print("-" * 80)
        print()

        adjustment = collect_adjustment_context()
        if not adjustment:
            print("Operation cancelled.")
            return

        # Phase 3: Rule Modifications
        print()
        print("PHASE 3: Rule Modifications")
        print("-" * 80)
        print()

        modifications = collect_rule_modifications()

        # Phase 4: Preview & Confirmation
        print()
        print("PHASE 4: Preview & Confirmation")
        print("-" * 80)
        print()

        if not show_preview_and_confirm(
            week_dates, metrics, health, reflections, next_week, adjustment, modifications
        ):
            print("Operation cancelled.")
            return

        # Phase 5: Execution
        print()
        print("PHASE 5: Creating Revision...")
        print("-" * 80)
        print()

        create_and_save_revision(
            week_dates, metrics, health, reflections, next_week, adjustment, modifications
        )

        print()
        print("=" * 80)
        print("Rule revision created successfully!")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError creating revision: {e}")
        import traceback
        traceback.print_exc()


def auto_fetch_week_statistics(week_start: str, week_end: str) -> Optional[WeeklyReviewMetrics]:
    """
    Automatically fetch weekly statistics from the database.

    Args:
        week_start: Week start date in YYYY-MM-DD format
        week_end: Week end date in YYYY-MM-DD format

    Returns:
        WeeklyReviewMetrics populated with database data, or None if fetch fails
    """
    try:
        # Parse dates
        start_date = datetime.strptime(week_start, "%Y-%m-%d")
        end_date = datetime.strptime(week_end, "%Y-%m-%d")

        metrics = WeeklyReviewMetrics()

        with get_db(url=CONST.DATABASE_URL) as db:
            # Query onsen visits
            onsen_visits = (
                db.query(OnsenVisit)
                .filter(OnsenVisit.visit_time >= start_date)
                .filter(OnsenVisit.visit_time <= end_date)
                .all()
            )

            metrics.onsen_visits_count = len(onsen_visits)

            # Count sauna sessions (visits where sauna was used)
            sauna_sessions = [v for v in onsen_visits if v.sauna_visited]
            metrics.sauna_sessions_count = len(sauna_sessions)

            # Calculate total soaking time (only if data exists)
            soaking_times = [v.stay_length_minutes for v in onsen_visits if v.stay_length_minutes]
            if soaking_times:
                metrics.total_soaking_hours = sum(soaking_times) / 60.0

            # Query exercise data
            exercise_manager = ExerciseDataManager(db)
            exercise_summary = exercise_manager.get_weekly_summary(start_date, end_date)

            # Extract exercise metrics
            sessions_by_type = exercise_summary.sessions_by_type or {}

            # Running distance (sum all running sessions)
            running_sessions = exercise_manager.get_by_date_range(start_date, end_date)
            running_distance = sum(
                s.distance_km
                for s in running_sessions
                if s.exercise_type == ExerciseType.RUNNING.value and s.distance_km
            )
            metrics.running_distance_km = round(running_distance, 2) if running_distance > 0 else None

            # Gym sessions
            gym_count = sessions_by_type.get(ExerciseType.GYM.value, 0)
            metrics.gym_sessions_count = gym_count if gym_count > 0 else None

            # Hike completed
            hike_count = sessions_by_type.get(ExerciseType.HIKING.value, 0)
            metrics.hike_completed = hike_count > 0

            # Rest days - cannot be auto-calculated, leave as None

        print("✅ Successfully auto-fetched weekly statistics from database")
        return metrics

    except Exception as e:
        print(f"⚠️  Warning: Could not auto-fetch statistics: {e}")
        print("Falling back to manual entry...")
        return None


def collect_week_dates() -> Optional[tuple[str, str, datetime, datetime]]:
    """
    Collect week start/end dates and revision/effective dates.

    Returns:
        Tuple of (week_start, week_end, revision_date, effective_date) or None if cancelled
    """
    print("Week Period:")
    print("Enter the week period you are reviewing (Rule Review Sunday).")
    print()

    while True:
        week_start = input("Week start date (YYYY-MM-DD): ").strip()
        if not week_start:
            return None
        try:
            datetime.strptime(week_start, "%Y-%m-%d")
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

    while True:
        week_end = input("Week end date (YYYY-MM-DD): ").strip()
        if not week_end:
            return None
        try:
            datetime.strptime(week_end, "%Y-%m-%d")
            break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")

    print()
    print("Revision Date (typically today, the Rule Review Sunday):")
    revision_date_str = input("Revision date (YYYY-MM-DD, or press Enter for today): ").strip()
    if not revision_date_str:
        revision_date = datetime.now()
    else:
        try:
            revision_date = datetime.strptime(revision_date_str, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Using today.")
            revision_date = datetime.now()

    print()
    print("Effective Date (when rule changes take effect):")
    effective_date_str = input("Effective date (YYYY-MM-DD, or press Enter for today): ").strip()
    if not effective_date_str:
        effective_date = datetime.now()
    else:
        try:
            effective_date = datetime.strptime(effective_date_str, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Using today.")
            effective_date = datetime.now()

    print()
    return (week_start, week_end, revision_date, effective_date)


def collect_summary_metrics(
    auto_fetched_metrics: Optional[WeeklyReviewMetrics] = None,
) -> WeeklyReviewMetrics:
    """
    Collect weekly summary metrics.

    Args:
        auto_fetched_metrics: Optional pre-populated metrics from database.
                             If provided, shows auto-fetched values as defaults.

    Returns:
        WeeklyReviewMetrics with user input (and/or auto-fetched values)
    """
    print("1. Summary Metrics")
    print()

    if auto_fetched_metrics:
        print("(Auto-fetched values shown in [brackets]. Press Enter to accept, or type new value)")
        print()

    metrics = WeeklyReviewMetrics()

    def get_int(prompt: str, auto_value: Optional[int] = None) -> Optional[int]:
        if auto_value is not None:
            full_prompt = f"{prompt}[auto: {auto_value}]: "
        else:
            full_prompt = prompt
        value = input(full_prompt).strip()
        if not value:
            return auto_value  # Accept auto-fetched value or None
        try:
            return int(value)
        except ValueError:
            print("Invalid number, using auto-fetched value." if auto_value else "Invalid number, skipping.")
            return auto_value

    def get_float(prompt: str, auto_value: Optional[float] = None) -> Optional[float]:
        if auto_value is not None:
            full_prompt = f"{prompt}[auto: {auto_value:.2f}]: "
        else:
            full_prompt = prompt
        value = input(full_prompt).strip()
        if not value:
            return auto_value  # Accept auto-fetched value or None
        try:
            return float(value)
        except ValueError:
            print("Invalid number, using auto-fetched value." if auto_value else "Invalid number, skipping.")
            return auto_value

    def get_bool(prompt: str, auto_value: Optional[bool] = None) -> Optional[bool]:
        if auto_value is not None:
            auto_display = "yes" if auto_value else "no"
            full_prompt = f"{prompt}[auto: {auto_display}] (y/n): "
        else:
            full_prompt = prompt
        value = input(full_prompt).strip().lower()
        if not value:
            return auto_value  # Accept auto-fetched value or None
        return value in ["y", "yes", "true", "1"]

    # Get auto-fetched values if available
    auto_onsen = auto_fetched_metrics.onsen_visits_count if auto_fetched_metrics else None
    auto_soaking = auto_fetched_metrics.total_soaking_hours if auto_fetched_metrics else None
    auto_sauna = auto_fetched_metrics.sauna_sessions_count if auto_fetched_metrics else None
    auto_running = auto_fetched_metrics.running_distance_km if auto_fetched_metrics else None
    auto_gym = auto_fetched_metrics.gym_sessions_count if auto_fetched_metrics else None
    auto_hike = auto_fetched_metrics.hike_completed if auto_fetched_metrics else None
    auto_rest = auto_fetched_metrics.rest_days_count if auto_fetched_metrics else None

    metrics.onsen_visits_count = get_int("Onsen visits this week: ", auto_onsen)
    metrics.total_soaking_hours = get_float("Total soaking time (hours): ", auto_soaking)
    metrics.sauna_sessions_count = get_int("Sauna sessions: ", auto_sauna)
    metrics.running_distance_km = get_float("Running distance (km): ", auto_running)
    metrics.gym_sessions_count = get_int("Gym sessions: ", auto_gym)
    metrics.hike_completed = get_bool("Hike completed (y/n): ", auto_hike)
    metrics.rest_days_count = get_int("Rest days: ", auto_rest)

    print()
    return metrics


def collect_health_wellbeing() -> HealthWellbeingData:
    """Collect health and wellbeing check data."""
    print("2. Health and Wellbeing Check")
    print()

    health = HealthWellbeingData()

    energy_input = input("Energy levels (1-10): ").strip()
    if energy_input:
        try:
            health.energy_level = int(energy_input)
        except ValueError:
            pass

    sleep_hours_input = input("Sleep hours per night (average): ").strip()
    if sleep_hours_input:
        try:
            health.sleep_hours = float(sleep_hours_input)
        except ValueError:
            pass

    health.sleep_quality_rating = input("Sleep quality rating (subjective): ").strip() or None
    health.soreness_notes = input("Soreness, pain, warning signs: ").strip() or None
    health.hydration_nutrition_notes = input("Hydration & nutrition adherence: ").strip() or None
    health.mood_mental_state = input("Mood / mental state: ").strip() or None

    print()
    return health


def collect_reflections() -> ReflectionData:
    """Collect reflection questions data."""
    print("3. Reflections")
    print()

    reflections = ReflectionData()

    reflections.reflection_positive = (
        input("What went particularly well this week?\n> ").strip() or None
    )
    reflections.reflection_patterns = (
        input("What patterns or improvements did you notice?\n> ").strip() or None
    )
    reflections.reflection_warnings = (
        input("Any warning signs (fatigue, skin, dehydration)?\n> ").strip() or None
    )
    reflections.reflection_standout_onsens = (
        input("Which onsens stood out, and why?\n> ").strip() or None
    )
    reflections.reflection_routine_notes = (
        input("Which elements of the routine felt natural or forced?\n> ").strip() or None
    )

    print()
    return reflections


def collect_next_week_plans() -> NextWeekPlan:
    """Collect plans for next week."""
    print("4. Plans for Next Week")
    print()

    next_week = NextWeekPlan()

    next_week.next_week_focus = input("Focus (e.g., recovery, pace stabilization): ").strip() or None
    next_week.next_week_goals = input("Intentional goals: ").strip() or None

    sauna_limit_input = input("Sauna limit for the week: ").strip()
    if sauna_limit_input:
        try:
            next_week.next_week_sauna_limit = int(sauna_limit_input)
        except ValueError:
            pass

    run_volume_input = input("Estimated total run volume (km): ").strip()
    if run_volume_input:
        try:
            next_week.next_week_run_volume = float(run_volume_input)
        except ValueError:
            pass

    next_week.next_week_hike_destination = input("Hike destination idea: ").strip() or None

    print()
    return next_week


def collect_adjustment_context() -> Optional[RuleAdjustmentContext]:
    """Collect rule adjustment context."""
    print("Rule Adjustment Context (§7 of the challenge ruleset)")
    print()
    print("Are you making any rule adjustments this week?")
    make_adjustments = input("Make adjustments? (y/n): ").strip().lower()

    if make_adjustments not in ["y", "yes"]:
        # No adjustments, create minimal context
        return RuleAdjustmentContext(
            adjustment_reason="none",
            adjustment_description="No rule adjustments this week",
            expected_duration="n/a",
            health_safeguard_applied=None,
        )

    print()
    print("Adjustment Reason:")
    print("  1. Fatigue")
    print("  2. Injury")
    print("  3. Schedule")
    print("  4. Illness")
    print("  5. Weather")
    print("  6. Travel")
    print("  7. Work demand")
    print("  8. Recovery")
    print("  9. Other")

    reason_choice = input("Select reason (1-9): ").strip()
    reason_map = {
        "1": AdjustmentReasonEnum.FATIGUE,
        "2": AdjustmentReasonEnum.INJURY,
        "3": AdjustmentReasonEnum.SCHEDULE,
        "4": AdjustmentReasonEnum.ILLNESS,
        "5": AdjustmentReasonEnum.WEATHER,
        "6": AdjustmentReasonEnum.TRAVEL,
        "7": AdjustmentReasonEnum.WORK_DEMAND,
        "8": AdjustmentReasonEnum.RECOVERY,
        "9": AdjustmentReasonEnum.OTHER,
    }

    adjustment_reason = reason_map.get(reason_choice, AdjustmentReasonEnum.OTHER)

    print()
    adjustment_description = input("Describe the modification:\n> ").strip()
    if not adjustment_description:
        print("Description is required for rule adjustments.")
        return None

    print()
    print("Expected Duration:")
    print("  1. Temporary")
    print("  2. Permanent")
    duration_choice = input("Select duration (1-2): ").strip()
    expected_duration = (
        RevisionDurationEnum.TEMPORARY if duration_choice == "1" else RevisionDurationEnum.PERMANENT
    )

    print()
    health_safeguard = input("Health safeguard applied (optional): ").strip() or None

    return RuleAdjustmentContext(
        adjustment_reason=adjustment_reason,
        adjustment_description=adjustment_description,
        expected_duration=expected_duration,
        health_safeguard_applied=health_safeguard,
    )


def collect_rule_modifications() -> list[RuleModification]:
    """Collect rule modifications for specific sections."""
    print("Rule Modifications")
    print()
    print("Now you can modify specific sections of the ruleset.")
    print()

    parser = RuleParser()
    sections = parser.parse()

    print("Available sections:")
    for section in sections:
        print(f"  {section.section_number}. {section.section_title}")

    print()
    print("Enter section numbers to modify (comma-separated), or press Enter to skip:")
    sections_input = input("> ").strip()

    if not sections_input:
        return []

    section_numbers = [s.strip() for s in sections_input.split(",")]

    modifications = []
    for section_num in section_numbers:
        section = parser.get_section(section_num)
        if not section:
            print(f"Warning: Section {section_num} not found. Skipping.")
            continue

        print()
        print("=" * 80)
        print(f"Modifying Section {section.section_number}: {section.section_title}")
        print("=" * 80)
        print()
        print("Current content:")
        print(section.content)
        print()

        print("Enter new content for this section:")
        print("(Type 'END' on a new line when finished)")
        print()

        new_lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            new_lines.append(line)

        new_content = "\n".join(new_lines).strip()

        if not new_content:
            print("No content entered. Skipping this section.")
            continue

        print()
        rationale = input("Rationale for this change:\n> ").strip()

        modification = RuleModification(
            section_number=section.section_number,
            section_title=section.section_title,
            old_text=section.content,
            new_text=new_content,
            rationale=rationale or "No rationale provided",
        )

        modifications.append(modification)

    return modifications


def show_preview_and_confirm(
    week_dates: tuple[str, str, datetime, datetime],
    metrics: WeeklyReviewMetrics,
    health: HealthWellbeingData,
    reflections: ReflectionData,
    next_week: NextWeekPlan,
    adjustment: RuleAdjustmentContext,
    modifications: list[RuleModification],
) -> bool:
    """
    Show preview of the revision and ask for confirmation.

    Returns:
        True if user confirms, False otherwise
    """
    week_start, week_end, revision_date, effective_date = week_dates

    print("REVISION PREVIEW")
    print()
    print(f"Week Period: {week_start} → {week_end}")
    print(f"Revision Date: {revision_date.strftime('%Y-%m-%d')}")
    print(f"Effective Date: {effective_date.strftime('%Y-%m-%d')}")
    print()

    print("Summary Metrics:")
    if metrics.onsen_visits_count:
        print(f"  - Onsen visits: {metrics.onsen_visits_count}")
    if metrics.sauna_sessions_count:
        print(f"  - Sauna sessions: {metrics.sauna_sessions_count}")
    if metrics.running_distance_km:
        print(f"  - Running: {metrics.running_distance_km}km")
    print()

    print("Adjustment Context:")
    print(f"  - Reason: {adjustment.adjustment_reason}")
    print(f"  - Description: {adjustment.adjustment_description[:100]}...")
    print(f"  - Duration: {adjustment.expected_duration}")
    print()

    if modifications:
        print("Sections to Modify:")
        for mod in modifications:
            print(f"  - Section {mod.section_number}: {mod.section_title}")
    else:
        print("No rule modifications.")
    print()

    while True:
        confirm = input("Proceed with creating this revision? (y/n): ").strip().lower()
        if confirm in ["y", "yes"]:
            return True
        elif confirm in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'.")


def create_and_save_revision(
    week_dates: tuple[str, str, datetime, datetime],
    metrics: WeeklyReviewMetrics,
    health: HealthWellbeingData,
    reflections: ReflectionData,
    next_week: NextWeekPlan,
    adjustment: RuleAdjustmentContext,
    modifications: list[RuleModification],
) -> None:
    """
    Create and save the revision to database and files.

    Args:
        week_dates: Tuple of (week_start, week_end, revision_date, effective_date)
        metrics: Weekly review metrics
        health: Health and wellbeing data
        reflections: Reflection data
        next_week: Next week plans
        adjustment: Rule adjustment context
        modifications: List of rule modifications
    """
    week_start, week_end, revision_date, effective_date = week_dates

    # Get next version number
    builder = RuleRevisionBuilder()
    version_number = builder.get_next_version_number()

    print(f"Creating revision v{version_number}...")

    # Generate revision summary
    sections_modified = [mod.section_number for mod in modifications]
    if modifications:
        revision_summary = f"Modified sections: {', '.join(sections_modified)}"
    else:
        revision_summary = "Weekly review without rule changes"

    # Create markdown file path
    markdown_filename = f"v{version_number}_{revision_date.strftime('%Y-%m-%d')}.md"
    markdown_file_path = os.path.join(PATHS.RULES_REVISIONS_DIR, markdown_filename)

    # Build RuleRevisionData object
    revision_data = RuleRevisionData(
        version_number=version_number,
        revision_date=revision_date,
        effective_date=effective_date,
        week_start_date=week_start,
        week_end_date=week_end,
        metrics=metrics,
        health=health,
        reflections=reflections,
        next_week=next_week,
        adjustment=adjustment,
        modifications=modifications,
        revision_summary=revision_summary,
        markdown_file_path=markdown_file_path,
    )

    # Generate and save markdown file
    generator = RuleMarkdownGenerator()
    generator.save_revision_markdown(revision_data, markdown_file_path)
    print(f"Saved revision markdown: {markdown_file_path}")

    # Save to database
    with get_db(url=CONST.DATABASE_URL) as db:
        db_revision = RuleRevision(
            version_number=version_number,
            revision_date=revision_date,
            effective_date=effective_date,
            week_start_date=week_start,
            week_end_date=week_end,
            onsen_visits_count=metrics.onsen_visits_count,
            total_soaking_hours=metrics.total_soaking_hours,
            sauna_sessions_count=metrics.sauna_sessions_count,
            running_distance_km=metrics.running_distance_km,
            gym_sessions_count=metrics.gym_sessions_count,
            hike_completed=metrics.hike_completed,
            rest_days_count=metrics.rest_days_count,
            energy_level=health.energy_level,
            sleep_hours=health.sleep_hours,
            sleep_quality_rating=health.sleep_quality_rating,
            soreness_notes=health.soreness_notes,
            hydration_nutrition_notes=health.hydration_nutrition_notes,
            mood_mental_state=health.mood_mental_state,
            reflection_positive=reflections.reflection_positive,
            reflection_patterns=reflections.reflection_patterns,
            reflection_warnings=reflections.reflection_warnings,
            reflection_standout_onsens=reflections.reflection_standout_onsens,
            reflection_routine_notes=reflections.reflection_routine_notes,
            adjustment_reason=adjustment.adjustment_reason,
            adjustment_description=adjustment.adjustment_description,
            expected_duration=adjustment.expected_duration,
            health_safeguard_applied=adjustment.health_safeguard_applied,
            next_week_focus=next_week.next_week_focus,
            next_week_goals=next_week.next_week_goals,
            next_week_sauna_limit=next_week.next_week_sauna_limit,
            next_week_run_volume=next_week.next_week_run_volume,
            next_week_hike_destination=next_week.next_week_hike_destination,
            sections_modified=json.dumps(sections_modified),
            revision_summary=revision_summary,
            markdown_file_path=markdown_file_path,
        )

        db.add(db_revision)
        db.commit()
        print(f"Saved to database: Revision ID {db_revision.id}")

    # Update main rules file if there are modifications
    if modifications:
        updater = RuleFileUpdater()
        updater.apply_modifications(modifications, version_number, revision_date, revision_summary)
        print(f"Updated main rules file: {PATHS.RULES_FILE}")
