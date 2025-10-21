"""
Type definitions and enums for the rules management system.
"""

from enum import StrEnum
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


class RuleSectionEnum(StrEnum):
    """Enum for rule sections in the Onsendo Challenge ruleset."""

    CORE_PRINCIPLES = "1"
    VISIT_FREQUENCY_AND_TIMING = "2"
    SAUNA_POLICY = "3"
    EXERCISE_INTEGRATION = "4"
    HEALTH_AND_SAFETY = "5"
    DATA_AND_LOGGING = "6"
    ADAPTATION_AND_RULE_REVIEW = "7"
    COMPLETION_AND_INTEGRITY = "8"
    SUMMARY_TARGETS = "9"
    GUIDING_THOUGHT = "10"


class AdjustmentReasonEnum(StrEnum):
    """Enum for rule adjustment reasons."""

    FATIGUE = "fatigue"
    INJURY = "injury"
    SCHEDULE = "schedule"
    ILLNESS = "illness"
    WEATHER = "weather"
    TRAVEL = "travel"
    WORK_DEMAND = "work_demand"
    RECOVERY = "recovery"
    OTHER = "other"


class RevisionDurationEnum(StrEnum):
    """Enum for revision duration types."""

    TEMPORARY = "temporary"
    PERMANENT = "permanent"


@dataclass
class WeeklyReviewMetrics:
    """Weekly review summary metrics."""

    onsen_visits_count: Optional[int] = None
    total_soaking_hours: Optional[float] = None
    sauna_sessions_count: Optional[int] = None
    running_distance_km: Optional[float] = None
    gym_sessions_count: Optional[int] = None
    long_exercise_completed: Optional[bool] = None  # Hike or long run (>= 15km or >= 2.5hr)
    rest_days_count: Optional[int] = None


@dataclass
class HealthWellbeingData:
    """Health and wellbeing check data."""

    energy_level: Optional[int] = None  # 1-10
    sleep_hours: Optional[float] = None
    sleep_quality_rating: Optional[str] = None
    soreness_notes: Optional[str] = None
    hydration_nutrition_notes: Optional[str] = None
    mood_mental_state: Optional[str] = None


@dataclass
class ReflectionData:
    """Reflection questions data."""

    reflection_positive: Optional[str] = None
    reflection_patterns: Optional[str] = None
    reflection_warnings: Optional[str] = None
    reflection_standout_onsens: Optional[str] = None
    reflection_routine_notes: Optional[str] = None


@dataclass
class RuleAdjustmentContext:
    """Rule adjustment context data."""

    adjustment_reason: str
    adjustment_description: str
    expected_duration: str  # temporary/permanent
    health_safeguard_applied: Optional[str] = None


@dataclass
class NextWeekPlan:
    """Plans for next week."""

    next_week_focus: Optional[str] = None
    next_week_goals: Optional[str] = None
    next_week_sauna_limit: Optional[int] = None
    next_week_run_volume: Optional[float] = None
    next_week_hike_destination: Optional[str] = None


@dataclass
class RuleSection:
    """Represents a section of the rules document."""

    section_number: str
    section_title: str
    content: str
    rules: list[str] = field(default_factory=list)


@dataclass
class RuleModification:
    """Represents a modification to a specific rule."""

    section_number: str
    section_title: str
    old_text: str
    new_text: str
    rationale: str


@dataclass
class RuleRevisionData:
    """Complete data for a rule revision.

    This class has many attributes to capture all aspects of a weekly rule review.
    """
    # pylint: disable=too-many-instance-attributes

    version_number: int
    revision_date: datetime
    effective_date: datetime
    week_start_date: str
    week_end_date: str

    # Weekly review data
    metrics: WeeklyReviewMetrics
    health: HealthWellbeingData
    reflections: ReflectionData
    next_week: NextWeekPlan

    # Rule adjustment context
    adjustment: RuleAdjustmentContext

    # Rule modifications
    modifications: list[RuleModification]

    # Metadata
    revision_summary: str
    markdown_file_path: str


@dataclass
class RulesDiff:
    """Represents differences between two rule versions."""

    version_a: int
    version_b: int
    sections_modified: list[str]
    modifications: list[RuleModification]


@dataclass
class RuleRevisionSummary:
    """Summary of a rule revision for list display."""

    id: int
    version_number: int
    revision_date: datetime
    week_period: str
    sections_modified: list[str]
    revision_summary: str
    adjustment_reason: str
