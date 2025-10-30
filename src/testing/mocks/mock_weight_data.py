"""
Mock data for weight measurements using the faker library.

This module provides functions to generate realistic mock weight data
for testing and development purposes.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from faker import Faker
import random
import csv
import json

fake = Faker(["en_US"])


@dataclass
class MockWeightProfile:
    """
    Mock weight measurement profile for realistic data generation.

    This class represents a person's weight tracking profile with realistic
    characteristics like base weight, variability, and trends over time.
    """

    # Profile characteristics
    base_weight_kg: float = 70.0
    variability_kg: float = 0.5  # Daily variation (standard deviation)
    trend: str = "stable"  # stable, gaining, losing, fluctuating

    # Trend characteristics
    trend_rate_kg_per_month: float = 0.5  # Rate of weight change per month

    # Measurement habits
    measurement_frequency: str = "daily"  # daily, every_other_day, weekly, random
    preferred_time: str = "morning"  # morning, afternoon, evening, varied
    preferred_conditions: str = "fasted"  # fasted, after_meal, varied

    # Data sources
    primary_data_source: str = "manual"  # manual, scale, apple_health

    def generate_measurement(
        self,
        measurement_date: datetime,
        days_since_start: int = 0,
    ) -> dict[str, any]:
        """
        Generate a realistic weight measurement for a specific date.

        Args:
            measurement_date: The date and time of the measurement
            days_since_start: Number of days since the start of tracking (for trends)

        Returns:
            Dictionary with measurement data
        """
        # Calculate base weight with trend
        if self.trend == "gaining":
            trend_adjustment = (days_since_start / 30) * self.trend_rate_kg_per_month
        elif self.trend == "losing":
            trend_adjustment = -(days_since_start / 30) * self.trend_rate_kg_per_month
        elif self.trend == "fluctuating":
            # Sinusoidal fluctuation
            cycle_days = 14  # Two-week cycle
            trend_adjustment = (
                self.trend_rate_kg_per_month
                * random.uniform(0.5, 1.5)
                * (days_since_start % cycle_days - cycle_days / 2)
                / cycle_days
            )
        else:  # stable
            trend_adjustment = 0.0

        # Add daily variation
        daily_variation = random.gauss(0, self.variability_kg)

        # Calculate final weight
        weight_kg = self.base_weight_kg + trend_adjustment + daily_variation

        # Ensure reasonable bounds
        weight_kg = max(40.0, min(200.0, weight_kg))
        weight_kg = round(weight_kg, 1)

        # Determine measurement conditions
        if self.preferred_conditions == "varied":
            conditions = random.choice(
                ["fasted", "after_meal", "post_workout", "before_workout", "normal"]
            )
        else:
            conditions = self.preferred_conditions

        # Determine time of day
        if self.preferred_time == "varied":
            time_of_day = random.choice(["morning", "afternoon", "evening", "night"])
        else:
            time_of_day = self.preferred_time

        # Add some notes occasionally (20% chance)
        notes = None
        if random.random() < 0.2:
            note_options = [
                "Feeling good",
                "After workout",
                "Before breakfast",
                "Post-meal",
                "End of day",
                None,
            ]
            notes = random.choice(note_options)

        return {
            "measurement_time": measurement_date,
            "weight_kg": weight_kg,
            "measurement_conditions": conditions,
            "time_of_day": time_of_day,
            "data_source": self.primary_data_source,
            "notes": notes,
        }

    def generate_series(
        self,
        start_date: datetime,
        duration_days: int,
    ) -> list[dict]:
        """
        Generate a series of weight measurements over a period.

        Args:
            start_date: Starting date for measurements
            duration_days: Number of days to generate measurements for

        Returns:
            List of measurement dictionaries
        """
        measurements = []

        for day_offset in range(duration_days):
            # Determine if we should record a measurement on this day
            should_measure = self._should_measure_on_day(day_offset)

            if should_measure:
                # Determine measurement time based on preferred time
                measurement_time = self._get_measurement_time(start_date, day_offset)

                # Generate measurement
                measurement = self.generate_measurement(measurement_time, day_offset)
                measurements.append(measurement)

        return measurements

    def _should_measure_on_day(self, day_offset: int) -> bool:
        """Determine if a measurement should be taken on this day based on frequency."""
        if self.measurement_frequency == "daily":
            return True
        if self.measurement_frequency == "every_other_day":
            return day_offset % 2 == 0
        if self.measurement_frequency == "weekly":
            return day_offset % 7 == 0
        if self.measurement_frequency == "random":
            # 60% chance on any given day
            return random.random() < 0.6

        return True

    def _get_measurement_time(self, start_date: datetime, day_offset: int) -> datetime:
        """Get measurement time based on preferred time of day."""
        base_date = start_date + timedelta(days=day_offset)

        if self.preferred_time == "morning":
            hour = random.randint(6, 9)
            minute = random.randint(0, 59)
        elif self.preferred_time == "afternoon":
            hour = random.randint(12, 16)
            minute = random.randint(0, 59)
        elif self.preferred_time == "evening":
            hour = random.randint(18, 21)
            minute = random.randint(0, 59)
        elif self.preferred_time == "night":
            hour = random.randint(22, 23)
            minute = random.randint(0, 59)
        else:  # varied
            hour = random.randint(6, 22)
            minute = random.randint(0, 59)

        return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


def export_measurements_csv(measurements: list[dict], file_path: str) -> str:
    """
    Export measurements to CSV format.

    Args:
        measurements: List of measurement dictionaries
        file_path: Path to save CSV file

    Returns:
        Path to the created file
    """
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "timestamp",
            "weight_kg",
            "conditions",
            "time_of_day",
            "notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for m in measurements:
            writer.writerow(
                {
                    "timestamp": m["measurement_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    "weight_kg": m["weight_kg"],
                    "conditions": m.get("measurement_conditions", ""),
                    "time_of_day": m.get("time_of_day", ""),
                    "notes": m.get("notes", ""),
                }
            )

    return file_path


def export_measurements_json(measurements: list[dict], file_path: str) -> str:
    """
    Export measurements to JSON format.

    Args:
        measurements: List of measurement dictionaries
        file_path: Path to save JSON file

    Returns:
        Path to the created file
    """
    data = []
    for m in measurements:
        data.append(
            {
                "timestamp": m["measurement_time"].isoformat(),
                "weight_kg": m["weight_kg"],
                "conditions": m.get("measurement_conditions"),
                "time_of_day": m.get("time_of_day"),
                "notes": m.get("notes"),
            }
        )

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return file_path


# Predefined profiles for common scenarios
PROFILE_STABLE_TRACKER = MockWeightProfile(
    base_weight_kg=72.0,
    variability_kg=0.3,
    trend="stable",
    measurement_frequency="daily",
    preferred_time="morning",
    preferred_conditions="fasted",
)

PROFILE_WEIGHT_LOSS = MockWeightProfile(
    base_weight_kg=85.0,
    variability_kg=0.5,
    trend="losing",
    trend_rate_kg_per_month=2.0,  # 2kg per month
    measurement_frequency="daily",
    preferred_time="morning",
    preferred_conditions="fasted",
)

PROFILE_MUSCLE_GAIN = MockWeightProfile(
    base_weight_kg=70.0,
    variability_kg=0.4,
    trend="gaining",
    trend_rate_kg_per_month=1.5,  # 1.5kg per month
    measurement_frequency="every_other_day",
    preferred_time="morning",
    preferred_conditions="post_workout",
)

PROFILE_FLUCTUATING = MockWeightProfile(
    base_weight_kg=75.0,
    variability_kg=1.0,
    trend="fluctuating",
    trend_rate_kg_per_month=1.0,
    measurement_frequency="random",
    preferred_time="varied",
    preferred_conditions="varied",
)

PROFILE_CASUAL_TRACKER = MockWeightProfile(
    base_weight_kg=68.0,
    variability_kg=0.8,
    trend="stable",
    measurement_frequency="weekly",
    preferred_time="varied",
    preferred_conditions="varied",
)


def generate_realistic_scenario(
    profile_name: str = "stable",
    start_date: Optional[datetime] = None,
    duration_days: int = 30,
) -> list[dict]:
    """
    Generate a realistic weight tracking scenario.

    Args:
        profile_name: Name of predefined profile (stable, weight_loss, muscle_gain, fluctuating, casual)
        start_date: Starting date (defaults to 30 days ago)
        duration_days: Number of days to generate data for

    Returns:
        List of measurement dictionaries
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=duration_days)

    # Select profile
    profiles = {
        "stable": PROFILE_STABLE_TRACKER,
        "weight_loss": PROFILE_WEIGHT_LOSS,
        "muscle_gain": PROFILE_MUSCLE_GAIN,
        "fluctuating": PROFILE_FLUCTUATING,
        "casual": PROFILE_CASUAL_TRACKER,
    }

    profile = profiles.get(profile_name, PROFILE_STABLE_TRACKER)

    return profile.generate_series(start_date, duration_days)
