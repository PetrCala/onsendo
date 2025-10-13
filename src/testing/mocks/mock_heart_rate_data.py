"""
Mock data for heart rate recordings using the faker library.

This module provides functions to generate realistic mock heart rate data
for testing and development purposes.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Any
from faker import Faker
import random
import csv
import json
import os
from pathlib import Path

fake = Faker(["en_US"])


@dataclass
class MockHeartRateSession:
    """Mock heart rate recording session with realistic data patterns."""

    # Session metadata
    start_time: datetime
    end_time: datetime
    data_format: str = "csv"
    source_file: str = ""
    notes: Optional[str] = None

    # Heart rate characteristics
    base_heart_rate: int = 70
    variability_factor: float = 0.15  # 15% variation
    trend_direction: str = "stable"  # stable, increasing, decreasing, variable

    # Data quality
    sample_rate_hz: float = 1.0  # samples per second
    confidence_range: tuple[float, float] = (0.85, 1.0)

    # Generated data (computed)
    data_points: list[tuple[datetime, float, float]] = field(default_factory=list)

    def __post_init__(self):
        """Generate realistic heart rate data points."""
        self._generate_data_points()

    def _generate_data_points(self):
        """Generate realistic heart rate data points based on session parameters."""
        duration_seconds = int((self.end_time - self.start_time).total_seconds())
        num_samples = int(duration_seconds * self.sample_rate_hz)

        if num_samples < 1:
            num_samples = 1

        # Generate base trend
        if self.trend_direction == "increasing":
            trend_multiplier = 1.0 + (
                0.3 * (self.end_time - self.start_time).total_seconds() / 3600
            )  # 30% increase per hour
        elif self.trend_direction == "decreasing":
            trend_multiplier = 1.0 - (
                0.2 * (self.end_time - self.start_time).total_seconds() / 3600
            )  # 20% decrease per hour
        elif self.trend_direction == "variable":
            trend_multiplier = 1.0
        else:  # stable
            trend_multiplier = 1.0

        for i in range(num_samples):
            # Calculate timestamp
            timestamp = self.start_time + timedelta(seconds=i / self.sample_rate_hz)

            # Calculate heart rate with trend and variation
            progress = i / max(num_samples - 1, 1)
            trend_factor = 1.0 + (trend_multiplier - 1.0) * progress

            # Add realistic variation (breathing, movement, etc.)
            variation = random.gauss(0, self.variability_factor)
            heart_rate = int(self.base_heart_rate * trend_factor * (1 + variation))

            # Ensure heart rate is within realistic bounds
            heart_rate = max(40, min(200, heart_rate))

            # Generate confidence score
            confidence = random.uniform(*self.confidence_range)

            self.data_points.append((timestamp, heart_rate, confidence))

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def average_heart_rate(self) -> float:
        """Calculate average heart rate."""
        if not self.data_points:
            return 0.0
        return sum(point[1] for point in self.data_points) / len(self.data_points)

    @property
    def min_heart_rate(self) -> float:
        """Get minimum heart rate."""
        if not self.data_points:
            return 0.0
        return min(point[1] for point in self.data_points)

    @property
    def max_heart_rate(self) -> float:
        """Get maximum heart rate."""
        if not self.data_points:
            return 0.0
        return max(point[1] for point in self.data_points)

    @property
    def data_points_count(self) -> int:
        """Get number of data points."""
        return len(self.data_points)

    def export_csv(self, file_path: str) -> str:
        """Export data to CSV format."""
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "heart_rate", "confidence"])

            for timestamp, heart_rate, confidence in self.data_points:
                writer.writerow(
                    [
                        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        heart_rate,
                        f"{confidence:.3f}",
                    ]
                )

        return file_path

    def export_json(self, file_path: str) -> str:
        """Export data to JSON format."""
        data = {
            "session_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_minutes": self.duration_minutes,
                "sample_rate_hz": self.sample_rate_hz,
                "base_heart_rate": self.base_heart_rate,
                "trend_direction": self.trend_direction,
            },
            "data_points": [
                {
                    "timestamp": timestamp.isoformat(),
                    "heart_rate": heart_rate,
                    "confidence": confidence,
                }
                for timestamp, heart_rate, confidence in self.data_points
            ],
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return file_path

    def export_text(self, file_path: str) -> str:
        """Export data to plain text format."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(
                f"# Heart Rate Session: {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}\n"
            )
            f.write(f"# Duration: {self.duration_minutes} minutes\n")
            f.write(f"# Sample Rate: {self.sample_rate_hz} Hz\n")
            f.write(f"# Base HR: {self.base_heart_rate} BPM\n")
            f.write(f"# Trend: {self.trend_direction}\n\n")

            for timestamp, heart_rate, confidence in self.data_points:
                f.write(
                    f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')},{heart_rate},{confidence:.3f}\n"
                )

        return file_path

    def export_apple_health_format(self, file_path: str) -> str:
        """Export data in Apple Health CSV format."""
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["SampleType", "SampleRate", "StartTime", "Data"])

            # Group consecutive heart rate values into batches
            batch_size = 10  # Number of samples per batch
            for i in range(0, len(self.data_points), batch_size):
                batch = self.data_points[i : i + batch_size]
                if not batch:
                    continue

                # Get start time for this batch
                batch_start_time = batch[0][0]

                # Extract heart rate values and join with semicolons
                hr_values = [str(point[1]) for point in batch]
                hr_data = ";".join(hr_values)

                writer.writerow(
                    [
                        "HEART_RATE",
                        self.sample_rate_hz,
                        batch_start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        hr_data,
                    ]
                )

        return file_path


class MockHeartRateDataGenerator:
    """Generator for realistic mock heart rate data."""

    def __init__(self, locale: str = "en_US"):
        """Initialize the generator with locale settings."""
        self.fake = Faker([locale])
        self._setup_constants()

    def _setup_constants(self):
        """Setup constants for realistic data generation."""
        self.heart_rate_scenarios = {
            "resting": {
                "base_rate": (60, 80),
                "variability": (0.05, 0.15),
                "trend": ["stable", "slight_decrease"],
                "duration_range": (30, 120),  # minutes
            },
            "light_exercise": {
                "base_rate": (80, 100),
                "variability": (0.10, 0.20),
                "trend": ["stable", "slight_increase"],
                "duration_range": (15, 60),
            },
            "moderate_exercise": {
                "base_rate": (100, 140),
                "variability": (0.15, 0.25),
                "trend": ["increasing", "variable"],
                "duration_range": (20, 90),
            },
            "intense_exercise": {
                "base_rate": (140, 180),
                "variability": (0.20, 0.30),
                "trend": ["increasing", "peak", "decreasing"],
                "duration_range": (10, 45),
            },
            "recovery": {
                "base_rate": (80, 120),
                "variability": (0.10, 0.20),
                "trend": ["decreasing", "stable"],
                "duration_range": (15, 60),
            },
            "sleep": {
                "base_rate": (50, 70),
                "variability": (0.03, 0.10),
                "trend": ["stable", "slight_decrease"],
                "duration_range": (240, 480),  # 4-8 hours
            },
        }

    def generate_session(
        self,
        scenario: str = "resting",
        start_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        **kwargs,
    ) -> MockHeartRateSession:
        """Generate a single heart rate session."""
        if scenario not in self.heart_rate_scenarios:
            scenario = "resting"

        config = self.heart_rate_scenarios[scenario]

        # Set start time
        if start_time is None:
            start_time = self.fake.date_time_between(start_date="-30d", end_date="now")

        # Set duration
        if duration_minutes is None:
            duration_minutes = random.randint(*config["duration_range"])

        end_time = start_time + timedelta(minutes=duration_minutes)

        # Set heart rate parameters
        base_hr = random.randint(*config["base_rate"])
        variability = random.uniform(*config["variability"])
        trend = random.choice(config["trend"])

        # Adjust trend for specific scenarios
        if trend == "peak" and scenario == "intense_exercise":
            # Create a peak pattern
            peak_time = start_time + timedelta(minutes=duration_minutes * 0.6)
            return self._generate_peak_session(
                start_time, end_time, peak_time, base_hr, variability
            )
        elif trend == "decreasing" and scenario == "recovery":
            # Create a recovery pattern
            return self._generate_recovery_session(
                start_time, end_time, base_hr, variability
            )

        # Generate standard session
        session = MockHeartRateSession(
            start_time=start_time,
            end_time=end_time,
            base_heart_rate=base_hr,
            variability_factor=variability,
            trend_direction=trend,
            **kwargs,
        )

        # Add notes if not provided
        if not session.notes:
            session.notes = f"Mock {scenario} session - {self.fake.sentence()}"

        return session

    def _generate_peak_session(
        self,
        start_time: datetime,
        end_time: datetime,
        peak_time: datetime,
        base_hr: int,
        variability: float,
    ) -> MockHeartRateSession:
        """Generate a session with a peak heart rate pattern."""
        session = MockHeartRateSession(
            start_time=start_time,
            end_time=end_time,
            base_heart_rate=base_hr,
            variability_factor=variability,
            trend_direction="peak",
        )

        # Override data points with peak pattern
        session.data_points = []
        duration_seconds = int((end_time - start_time).total_seconds())
        sample_rate = session.sample_rate_hz

        for i in range(int(duration_seconds * sample_rate)):
            timestamp = start_time + timedelta(seconds=i / sample_rate)
            progress = i / max(int(duration_seconds * sample_rate) - 1, 1)

            # Create peak pattern
            time_to_peak = abs((timestamp - peak_time).total_seconds())
            peak_factor = max(0, 1 - (time_to_peak / (duration_seconds * 0.3)))

            # Calculate heart rate with peak
            hr = base_hr + int(peak_factor * 60)  # Up to 60 BPM increase at peak
            hr += random.gauss(0, hr * variability)
            hr = max(40, min(200, int(hr)))

            confidence = random.uniform(*session.confidence_range)
            session.data_points.append((timestamp, hr, confidence))

        return session

    def _generate_recovery_session(
        self, start_time: datetime, end_time: datetime, base_hr: int, variability: float
    ) -> MockHeartRateSession:
        """Generate a session with a recovery heart rate pattern."""
        session = MockHeartRateSession(
            start_time=start_time,
            end_time=end_time,
            base_heart_rate=base_hr,
            variability_factor=variability,
            trend_direction="decreasing",
        )

        # Override data points with recovery pattern
        session.data_points = []
        duration_seconds = int((end_time - start_time).total_seconds())
        sample_rate = session.sample_rate_hz

        for i in range(int(duration_seconds * sample_rate)):
            timestamp = start_time + timedelta(seconds=i / sample_rate)
            progress = i / max(int(duration_seconds * sample_rate) - 1, 1)

            # Create recovery pattern (exponential decay)
            recovery_factor = 1 - (1 - progress) ** 2  # Exponential decay

            # Start from elevated heart rate and recover to base
            hr = base_hr + int(recovery_factor * 40)  # Start 40 BPM above base
            hr += random.gauss(0, hr * variability)
            hr = max(40, min(200, int(hr)))

            confidence = random.uniform(*session.confidence_range)
            session.data_points.append((timestamp, hr, confidence))

        return session

    def generate_workout_session(
        self, start_time: Optional[datetime] = None, **kwargs
    ) -> MockHeartRateSession:
        """Generate a complete workout session with warmup, exercise, and cooldown."""
        if start_time is None:
            start_time = self.fake.date_time_between(start_date="-7d", end_date="now")

        # Generate warmup
        warmup = self.generate_session(
            "light_exercise",
            start_time=start_time,
            duration_minutes=random.randint(10, 20),
        )

        # Generate main exercise
        exercise_start = warmup.end_time
        exercise = self.generate_session(
            "moderate_exercise",
            start_time=exercise_start,
            duration_minutes=random.randint(30, 60),
        )

        # Generate cooldown
        cooldown_start = exercise.end_time
        cooldown = self.generate_session(
            "recovery",
            start_time=cooldown_start,
            duration_minutes=random.randint(15, 25),
        )

        # Combine into single session
        combined_session = MockHeartRateSession(
            start_time=warmup.start_time,
            end_time=cooldown.end_time,
            base_heart_rate=warmup.base_heart_rate,
            variability_factor=0.2,
            trend_direction="variable",
            notes="Mock workout session with warmup, exercise, and cooldown",
        )

        # Combine all data points
        combined_session.data_points = (
            warmup.data_points + exercise.data_points + cooldown.data_points
        )

        return combined_session

    def generate_sleep_session(
        self, start_time: Optional[datetime] = None, **kwargs
    ) -> MockHeartRateSession:
        """Generate a sleep session with realistic patterns."""
        if start_time is None:
            # Start in evening
            start_time = self.fake.date_time_between(
                start_date="-7d", end_date="now"
            ).replace(hour=random.randint(22, 23), minute=random.randint(0, 59))

        duration_hours = random.randint(6, 9)
        end_time = start_time + timedelta(hours=duration_hours)

        session = self.generate_session(
            "sleep", start_time=start_time, duration_minutes=duration_hours * 60
        )

        session.notes = f"Mock sleep session - {duration_hours} hours"
        return session

    def generate_daily_sessions(
        self, date: Optional[datetime] = None, num_sessions: int = 3, **kwargs
    ) -> list[MockHeartRateSession]:
        """Generate multiple sessions for a single day."""
        if date is None:
            date = self.fake.date_time_between(
                start_date="-7d", end_date="now"
            ).replace(hour=6, minute=0, second=0, microsecond=0)

        sessions = []
        current_time = date.replace(hour=6, minute=0)  # Start at 6 AM

        for i in range(num_sessions):
            # Choose scenario based on time of day
            if current_time.hour < 8:
                scenario = "light_exercise"  # Morning workout
            elif current_time.hour < 12:
                scenario = "resting"  # Morning
            elif current_time.hour < 17:
                scenario = random.choice(["resting", "light_exercise"])
            elif current_time.hour < 20:
                scenario = "moderate_exercise"  # Evening workout
            else:
                scenario = "resting"  # Evening

            # Generate session
            session = self.generate_session(
                scenario=scenario,
                start_time=current_time,
                duration_minutes=random.randint(20, 90),
            )

            sessions.append(session)

            # Move to next session time
            current_time = session.end_time + timedelta(minutes=random.randint(30, 120))

            # Don't go past midnight
            if current_time.day != date.day:
                break

        return sessions


# Convenience functions
def create_single_session(
    scenario: str = "resting", start_time: Optional[datetime] = None, **kwargs
) -> MockHeartRateSession:
    """Create a single heart rate session."""
    generator = MockHeartRateDataGenerator()
    return generator.generate_session(scenario, start_time, **kwargs)


def create_workout_session(
    start_time: Optional[datetime] = None, **kwargs
) -> MockHeartRateSession:
    """Create a workout session with warmup, exercise, and cooldown."""
    generator = MockHeartRateDataGenerator()
    return generator.generate_workout_session(start_time, **kwargs)


def create_sleep_session(
    start_time: Optional[datetime] = None, **kwargs
) -> MockHeartRateSession:
    """Create a sleep session."""
    generator = MockHeartRateDataGenerator()
    return generator.generate_sleep_session(start_time, **kwargs)


def create_daily_sessions(
    date: Optional[datetime] = None, num_sessions: int = 3, **kwargs
) -> list[MockHeartRateSession]:
    """Create multiple sessions for a single day."""
    generator = MockHeartRateDataGenerator()
    return generator.generate_daily_sessions(date, num_sessions, **kwargs)


def create_realistic_scenario(
    scenario_type: str = "daily", **kwargs
) -> list[MockHeartRateSession]:
    """Create realistic heart rate scenarios."""
    generator = MockHeartRateDataGenerator()

    if scenario_type == "daily":
        return generator.generate_daily_sessions(**kwargs)
    elif scenario_type == "workout":
        return [generator.generate_workout_session(**kwargs)]
    elif scenario_type == "sleep":
        return [generator.generate_sleep_session(**kwargs)]
    elif scenario_type == "mixed":
        sessions = []
        sessions.extend(generator.generate_daily_sessions(**kwargs))
        sessions.append(generator.generate_workout_session(**kwargs))
        return sessions
    else:
        return [generator.generate_session(**kwargs)]
