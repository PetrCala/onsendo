"""
Exercise types and enums for the exercise tracking system.

This module defines all exercise-related types, enums, and data structures
used throughout the Onsendo exercise tracking system.
"""

from enum import StrEnum


class ExerciseType(StrEnum):
    """
    Types of exercise activities.

    These are the high-level exercise categories used throughout Onsendo,
    aligned with the challenge rules (running, gym, hiking).
    """

    RUNNING = "running"
    GYM = "gym"
    HIKING = "hiking"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    WALKING = "walking"
    YOGA = "yoga"
    OTHER = "other"


class WorkoutType(StrEnum):
    """
    Apple Health workout types.

    Comprehensive list of workout types from Apple Health/HealthKit.
    Maps to internal ExerciseType for normalization.
    """

    # Running & Walking
    RUNNING = "HKWorkoutActivityTypeRunning"
    WALKING = "HKWorkoutActivityTypeWalking"
    HIKING = "HKWorkoutActivityTypeHiking"
    TRAIL_RUNNING = "HKWorkoutActivityTypeTrailRunning"

    # Cycling
    CYCLING = "HKWorkoutActivityTypeCycling"
    INDOOR_CYCLING = "HKWorkoutActivityTypeCyclingIndoor"

    # Swimming
    SWIMMING = "HKWorkoutActivityTypeSwimming"
    SWIMMING_OPEN_WATER = "HKWorkoutActivityTypeSwimmingOpenWater"

    # Gym & Strength
    FUNCTIONAL_STRENGTH = "HKWorkoutActivityTypeFunctionalStrengthTraining"
    TRADITIONAL_STRENGTH = "HKWorkoutActivityTypeTraditionalStrengthTraining"
    CORE_TRAINING = "HKWorkoutActivityTypeCoreTraining"
    HIGH_INTENSITY_INTERVAL = "HKWorkoutActivityTypeHighIntensityIntervalTraining"
    CROSS_TRAINING = "HKWorkoutActivityTypeCrossTraining"

    # Flexibility & Mind-Body
    YOGA = "HKWorkoutActivityTypeYoga"
    PILATES = "HKWorkoutActivityTypePilates"
    STRETCHING = "HKWorkoutActivityTypeFlexibility"
    COOLDOWN = "HKWorkoutActivityTypeCooldown"

    # Other cardio
    ROWING = "HKWorkoutActivityTypeRowing"
    STAIR_CLIMBING = "HKWorkoutActivityTypeStairClimbing"
    ELLIPTICAL = "HKWorkoutActivityTypeElliptical"

    # Sports
    SOCCER = "HKWorkoutActivityTypeSoccer"
    BASKETBALL = "HKWorkoutActivityTypeBasketball"
    TENNIS = "HKWorkoutActivityTypeTennis"
    BADMINTON = "HKWorkoutActivityTypeBadminton"

    # Misc
    OTHER = "HKWorkoutActivityTypeOther"
    MIXED_CARDIO = "HKWorkoutActivityTypeMixedCardio"


class DataSource(StrEnum):
    """
    Data sources for exercise sessions.

    Indicates where the exercise data originated from.
    """

    APPLE_HEALTH = "apple_health"
    GARMIN = "garmin"
    STRAVA = "strava"
    MANUAL = "manual"
    GPX_FILE = "gpx_file"
    TCX_FILE = "tcx_file"
    OTHER = "other"


class IndoorOutdoor(StrEnum):
    """Indoor or outdoor workout classification."""

    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    UNKNOWN = "unknown"


# Mapping from Apple Health workout types to Onsendo exercise types
WORKOUT_TYPE_MAPPING: dict[str, ExerciseType] = {
    # Running
    WorkoutType.RUNNING: ExerciseType.RUNNING,
    WorkoutType.TRAIL_RUNNING: ExerciseType.RUNNING,
    # Hiking
    WorkoutType.HIKING: ExerciseType.HIKING,
    # Cycling
    WorkoutType.CYCLING: ExerciseType.CYCLING,
    WorkoutType.INDOOR_CYCLING: ExerciseType.CYCLING,
    # Swimming
    WorkoutType.SWIMMING: ExerciseType.SWIMMING,
    WorkoutType.SWIMMING_OPEN_WATER: ExerciseType.SWIMMING,
    # Gym
    WorkoutType.FUNCTIONAL_STRENGTH: ExerciseType.GYM,
    WorkoutType.TRADITIONAL_STRENGTH: ExerciseType.GYM,
    WorkoutType.CORE_TRAINING: ExerciseType.GYM,
    WorkoutType.HIGH_INTENSITY_INTERVAL: ExerciseType.GYM,
    WorkoutType.CROSS_TRAINING: ExerciseType.GYM,
    WorkoutType.ROWING: ExerciseType.GYM,
    WorkoutType.STAIR_CLIMBING: ExerciseType.GYM,
    WorkoutType.ELLIPTICAL: ExerciseType.GYM,
    # Walking
    WorkoutType.WALKING: ExerciseType.WALKING,
    # Yoga
    WorkoutType.YOGA: ExerciseType.YOGA,
    WorkoutType.PILATES: ExerciseType.YOGA,
    WorkoutType.STRETCHING: ExerciseType.YOGA,
    WorkoutType.COOLDOWN: ExerciseType.YOGA,
    # Sports and other
    WorkoutType.SOCCER: ExerciseType.OTHER,
    WorkoutType.BASKETBALL: ExerciseType.OTHER,
    WorkoutType.TENNIS: ExerciseType.OTHER,
    WorkoutType.BADMINTON: ExerciseType.OTHER,
    WorkoutType.OTHER: ExerciseType.OTHER,
    WorkoutType.MIXED_CARDIO: ExerciseType.OTHER,
}


def map_workout_type_to_exercise_type(workout_type: str) -> ExerciseType:
    """
    Map an Apple Health workout type to an Onsendo exercise type.

    Args:
        workout_type: Apple Health workout type string

    Returns:
        Corresponding Onsendo ExerciseType

    Examples:
        >>> map_workout_type_to_exercise_type("HKWorkoutActivityTypeRunning")
        ExerciseType.RUNNING
        >>> map_workout_type_to_exercise_type("HKWorkoutActivityTypeFunctionalStrengthTraining")
        ExerciseType.GYM
    """
    return WORKOUT_TYPE_MAPPING.get(workout_type, ExerciseType.OTHER)
