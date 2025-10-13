"""
Mock data generators for rule revisions.
"""

import random
from datetime import datetime, timedelta
from src.types.rules import (
    WeeklyReviewMetrics,
    HealthWellbeingData,
    ReflectionData,
    RuleAdjustmentContext,
    NextWeekPlan,
    RuleModification,
    AdjustmentReasonEnum,
    RevisionDurationEnum,
)


def generate_mock_metrics() -> WeeklyReviewMetrics:
    """Generate mock weekly review metrics."""
    return WeeklyReviewMetrics(
        onsen_visits_count=random.randint(8, 16),
        total_soaking_hours=round(random.uniform(4.0, 10.0), 1),
        sauna_sessions_count=random.randint(2, 5),
        running_distance_km=round(random.uniform(15.0, 40.0), 1),
        gym_sessions_count=random.randint(2, 4),
        hike_completed=random.choice([True, False]),
        rest_days_count=random.randint(1, 2),
    )


def generate_mock_health() -> HealthWellbeingData:
    """Generate mock health and wellbeing data."""
    return HealthWellbeingData(
        energy_level=random.randint(6, 10),
        sleep_hours=round(random.uniform(6.5, 8.5), 1),
        sleep_quality_rating=random.choice(["good", "excellent", "fair", "restful"]),
        soreness_notes=random.choice(
            [
                "Minor muscle fatigue",
                "Feeling good",
                "Some knee discomfort",
                "No issues",
            ]
        ),
        hydration_nutrition_notes="Adequate hydration, balanced diet",
        mood_mental_state=random.choice(
            ["positive", "energized", "slightly stressed", "calm"]
        ),
    )


def generate_mock_reflections() -> ReflectionData:
    """Generate mock reflection data."""
    reflections = [
        "Made good progress on the challenge this week",
        "Felt more comfortable with the routine",
        "Discovered some great new onsens",
    ]

    return ReflectionData(
        reflection_positive=random.choice(reflections),
        reflection_patterns="Noticed improved recovery with proper rest days",
        reflection_warnings=random.choice([None, "Slight fatigue mid-week"]),
        reflection_standout_onsens="Takegawara Onsen - excellent traditional atmosphere",
        reflection_routine_notes="Morning visits feel very natural now",
    )


def generate_mock_adjustment() -> RuleAdjustmentContext:
    """Generate mock rule adjustment context."""
    reasons = list(AdjustmentReasonEnum)
    durations = list(RevisionDurationEnum)

    return RuleAdjustmentContext(
        adjustment_reason=random.choice(reasons),
        adjustment_description="Adjusting visit frequency due to schedule constraints",
        expected_duration=random.choice(durations),
        health_safeguard_applied=random.choice(
            [None, "Extra rest day added", "Reduced sauna sessions"]
        ),
    )


def generate_mock_next_week() -> NextWeekPlan:
    """Generate mock next week plan."""
    return NextWeekPlan(
        next_week_focus=random.choice(["recovery", "consistency", "exploration"]),
        next_week_goals="Visit 3 new onsens in the Kannawa area",
        next_week_sauna_limit=random.randint(3, 5),
        next_week_run_volume=round(random.uniform(20.0, 35.0), 1),
        next_week_hike_destination=random.choice(
            ["Mount Tsurumi", "Beppu Park Trail", "Coastal route"]
        ),
    )


def generate_mock_modifications(num_mods: int = 1) -> list[RuleModification]:
    """Generate mock rule modifications."""
    modifications = []

    sections = [
        ("2", "Visit Frequency and Timing"),
        ("3", "Sauna Policy"),
        ("4", "Exercise Integration"),
    ]

    for _ in range(num_mods):
        section_num, section_title = random.choice(sections)

        modifications.append(
            RuleModification(
                section_number=section_num,
                section_title=section_title,
                old_text="Target: Two onsen visits per day on active days.",
                new_text="Target: One to two onsen visits per day on active days.",
                rationale="Allowing flexibility for busy days while maintaining consistency",
            )
        )

    return modifications


def generate_mock_week_dates(weeks_ago: int = 0) -> tuple:
    """
    Generate mock week dates.

    Args:
        weeks_ago: Number of weeks in the past (0 = current week)

    Returns:
        Tuple of (week_start, week_end, revision_date, effective_date)
    """
    today = datetime.now() - timedelta(weeks=weeks_ago)
    # Get start of week (Monday)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    revision_date = week_end  # Sunday
    effective_date = week_end + timedelta(days=1)  # Monday

    return (
        week_start.strftime("%Y-%m-%d"),
        week_end.strftime("%Y-%m-%d"),
        revision_date,
        effective_date,
    )
