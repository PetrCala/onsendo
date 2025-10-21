"""
Mock data for onsen visits using the faker library.

This module provides functions to generate basic mock data for onsen visits,
ensuring data consistency and following the logic chains defined in interactive.py.

NOTE: This module generates simple mock data with random ratings.
For analysis-ready data with realistic econometric relationships, user profiles,
and correlations, use the advanced generators in:
- scenario_builder.py (profile-based data generation)
- user_profiles.py (behavioral personas)
- integrated_scenario.py (heart rate data integration)

This module is best suited for:
- Quick unit tests requiring simple visit data
- Basic testing scenarios without econometric requirements
- Foundation dataclass (MockOnsenVisit) used by all mock systems
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from faker import Faker
import random

fake = Faker(["ja_JP", "en_US"])


@dataclass
class MockOnsenVisit:
    """Mock onsen visit data with validation logic."""

    # Basic visit information
    onsen_id: int
    entry_fee_yen: int
    payment_method: str
    weather: str
    time_of_day: str
    temperature_outside_celsius: float
    visit_time: datetime
    stay_length_minutes: int
    visited_with: str
    travel_mode: str
    travel_time_minutes: int

    # Exercise information
    exercise_before_onsen: bool
    accessibility_rating: int
    crowd_level: str
    view_rating: int
    navigability_rating: int
    cleanliness_rating: int

    # Main bath information
    main_bath_type: str
    main_bath_temperature: float
    main_bath_water_type: str
    water_color: str
    smell_intensity_rating: int

    # Changing room and facilities
    changing_room_cleanliness_rating: int
    locker_availability_rating: int
    had_soap: bool

    # Sauna information
    had_sauna: bool
    had_outdoor_bath: bool
    had_rest_area: bool
    had_food_service: bool
    massage_chair_available: bool

    # Mood and energy
    pre_visit_mood: str
    post_visit_mood: str
    energy_level_change: int
    hydration_level: int

    # Overall ratings
    atmosphere_rating: int
    personal_rating: int

    # Optional notes
    notes: Optional[str] = None

    # Optional fields with defaults
    exercise_type: Optional[str] = None
    exercise_length_minutes: Optional[int] = None
    sauna_visited: Optional[bool] = None
    sauna_temperature: Optional[float] = None
    sauna_steam: Optional[bool] = None
    sauna_duration_minutes: Optional[int] = None
    sauna_rating: Optional[int] = None
    outdoor_bath_visited: Optional[bool] = None
    outdoor_bath_temperature: Optional[float] = None
    outdoor_bath_rating: Optional[int] = None
    rest_area_used: Optional[bool] = None
    rest_area_rating: Optional[int] = None
    food_service_used: Optional[bool] = None
    food_quality_rating: Optional[int] = None
    multi_onsen_day: bool = False
    visit_order: Optional[int] = None
    previous_location: Optional[int] = None
    next_location: Optional[int] = None

    def __post_init__(self):
        """Validate and adjust data based on logic chains."""
        self._validate_sauna_logic()
        self._validate_outdoor_bath_logic()
        self._validate_rest_area_logic()
        self._validate_food_service_logic()
        self._validate_exercise_logic()
        self._validate_multi_onsen_logic()

    def _validate_sauna_logic(self):
        """Ensure sauna-related data is consistent."""
        if not self.had_sauna:
            self.sauna_visited = False
            self.sauna_temperature = None
            self.sauna_steam = None
            self.sauna_duration_minutes = None
            self.sauna_rating = None
        elif self.had_sauna and self.sauna_visited is None:
            # If sauna exists, randomly decide if visited
            self.sauna_visited = random.choice([True, False])
            if not self.sauna_visited:
                self.sauna_temperature = None
                self.sauna_steam = None
                self.sauna_duration_minutes = None
                self.sauna_rating = None

    def _validate_outdoor_bath_logic(self):
        """Ensure outdoor bath-related data is consistent."""
        if not self.had_outdoor_bath:
            self.outdoor_bath_visited = False
            self.outdoor_bath_temperature = None
            self.outdoor_bath_rating = None
        elif self.had_outdoor_bath and self.outdoor_bath_visited is None:
            # If outdoor bath exists, randomly decide if visited
            self.outdoor_bath_visited = random.choice([True, False])
            if not self.outdoor_bath_visited:
                self.outdoor_bath_temperature = None
                self.outdoor_bath_rating = None

    def _validate_rest_area_logic(self):
        """Ensure rest area-related data is consistent."""
        if not self.had_rest_area:
            self.rest_area_used = False
            self.rest_area_rating = None
        elif self.had_rest_area and self.rest_area_used is None:
            # If rest area exists, randomly decide if used
            self.rest_area_used = random.choice([True, False])
            if not self.rest_area_used:
                self.rest_area_rating = None

    def _validate_food_service_logic(self):
        """Ensure food service-related data is consistent."""
        if not self.had_food_service:
            self.food_service_used = False
            self.food_quality_rating = None
        elif self.had_food_service and self.food_service_used is None:
            # If food service exists, randomly decide if used
            self.food_service_used = random.choice([True, False])
            if not self.food_service_used:
                self.food_quality_rating = None

    def _validate_exercise_logic(self):
        """Ensure exercise-related data is consistent."""
        if not self.exercise_before_onsen:
            self.exercise_type = None
            self.exercise_length_minutes = None

    def _validate_multi_onsen_logic(self):
        """Ensure multi-onsen day data is consistent."""
        if not self.multi_onsen_day:
            self.visit_order = None
            self.previous_location = None
            self.next_location = None


class MockVisitDataGenerator:
    """Generator for realistic mock onsen visit data."""

    def __init__(self, locale: str = "ja_JP"):
        """Initialize the generator with specified locale."""
        self.fake = Faker([locale, "en_US"])
        self._setup_constants()

    def _setup_constants(self):
        """Setup constants for realistic data generation."""
        self.PAYMENT_METHODS = ["cash", "card", "IC card", "other"]
        self.WEATHER_CONDITIONS = ["sunny", "cloudy", "rainy", "snowy", "partly cloudy"]
        self.TIME_OF_DAY = ["morning", "afternoon", "evening", "night"]
        self.VISITED_WITH = ["alone", "friend", "group", "family", "partner"]
        self.TRAVEL_MODES = ["car", "train", "bus", "walk", "run", "bike", "taxi"]
        self.EXERCISE_TYPES = ["running", "walking", "cycling", "swimming", "hiking"]
        self.CROWD_LEVELS = ["empty", "quiet", "moderate", "busy", "crowded"]
        self.MAIN_BATH_TYPES = ["indoor", "open air", "mixed", "other"]
        self.WATER_TYPES = ["sulfur", "salt", "alkaline", "acidic", "neutral"]
        self.WATER_COLORS = ["clear", "brown", "green", "blue", "milky"]
        self.MOODS = ["relaxed", "stressed", "anxious", "tired", "energetic", "excited"]

        # Note templates for realistic visit notes
        self.NOTE_TEMPLATES = [
            "Great experience, will definitely return",
            "Water was perfect temperature today",
            "Very crowded, came at a bad time",
            "Beautiful views from the outdoor bath",
            "Staff was very friendly and helpful",
            "Sauna was excellent, best in the area",
            "First time visit, exceeded expectations",
            "Regular visit, as good as always",
            "Water color was different today, interesting",
            "Met some friendly locals here",
            "Perfect after a long run",
            "Exactly what I needed after work",
            "Lovely quiet atmosphere",
            "A bit too hot for my taste today",
            "Great value for the price",
        ]

        # Temperature ranges for different seasons
        self.TEMP_RANGES = {
            "spring": (15.0, 25.0),
            "summer": (25.0, 35.0),
            "autumn": (15.0, 25.0),
            "winter": (5.0, 15.0),
        }

        # Onsen temperature ranges
        self.ONSEN_TEMP_RANGES = {
            "indoor": (38.0, 42.0),
            "open air": (40.0, 45.0),
            "mixed": (39.0, 43.0),
        }

    def _get_season(self, date: datetime) -> str:
        """Determine season from date."""
        month = date.month
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "autumn"
        else:
            return "winter"

    def _get_realistic_temperature(self, season: str, time_of_day: str) -> float:
        """Generate realistic outside temperature based on season and time."""
        base_min, base_max = self.TEMP_RANGES[season]

        # Adjust for time of day
        if time_of_day == "morning":
            temp = random.uniform(base_min, (base_min + base_max) / 2)
        elif time_of_day == "afternoon":
            temp = random.uniform((base_min + base_max) / 2, base_max)
        elif time_of_day == "evening":
            temp = random.uniform(base_min, (base_min + base_max) / 2)
        else:  # night
            temp = random.uniform(base_min - 2, base_min + 2)

        return round(temp, 1)

    def _get_realistic_onsen_temperature(self, bath_type: str) -> float:
        """Generate realistic onsen temperature based on bath type."""
        min_temp, max_temp = self.ONSEN_TEMP_RANGES.get(bath_type, (40.0, 42.0))
        return round(random.uniform(min_temp, max_temp), 1)

    def _get_realistic_ratings(self, feature_type: str) -> int:
        """Generate realistic ratings based on feature type."""
        if feature_type == "cleanliness":
            # Cleanliness tends to be higher in Japan
            return random.choices([7, 8, 9, 10], weights=[0.1, 0.2, 0.4, 0.3])[0]
        elif feature_type == "accessibility":
            # Accessibility varies more
            return random.randint(5, 10)
        elif feature_type == "view":
            # Views can be very good at onsens
            return random.choices([6, 7, 8, 9, 10], weights=[0.1, 0.2, 0.3, 0.3, 0.1])[
                0
            ]
        else:
            return random.randint(6, 10)

    def _generate_optional_notes(self) -> Optional[str]:
        """Generate optional notes for a visit (50% chance)."""
        if random.choice([True, False]):
            return random.choice(self.NOTE_TEMPLATES)
        return None

    def generate_single_visit(
        self,
        onsen_id: int,
        visit_date: Optional[datetime] = None,
        time_of_day: Optional[str] = None,
        weather: Optional[str] = None,
        visited_with: Optional[str] = None,
        travel_mode: Optional[str] = None,
        exercise_before: Optional[bool] = None,
        **kwargs,
    ) -> MockOnsenVisit:
        """Generate a single realistic onsen visit."""

        # Set defaults if not provided
        if visit_date is None:
            visit_date = self.fake.date_time_between(start_date="-1y", end_date="now")

        if time_of_day is None:
            time_of_day = random.choice(self.TIME_OF_DAY)

        if weather is None:
            weather = random.choice(self.WEATHER_CONDITIONS)

        if visited_with is None:
            visited_with = random.choice(self.VISITED_WITH)

        if travel_mode is None:
            travel_mode = random.choice(self.TRAVEL_MODES)

        if exercise_before is None:
            exercise_before = random.choice([True, False])

        # Determine season and generate realistic temperatures
        season = self._get_season(visit_date)
        outside_temp = self._get_realistic_temperature(season, time_of_day)

        # Generate bath type and temperature
        main_bath_type = random.choice(self.MAIN_BATH_TYPES)
        main_bath_temp = self._get_realistic_onsen_temperature(main_bath_type)

        # Generate facility availability (with realistic probabilities)
        had_sauna = random.choices([True, False], weights=[0.7, 0.3])[0]
        had_outdoor_bath = random.choices([True, False], weights=[0.6, 0.4])[0]
        had_rest_area = random.choices([True, False], weights=[0.8, 0.2])[0]
        had_food_service = random.choices([True, False], weights=[0.5, 0.5])[0]
        had_soap = random.choices([True, False], weights=[0.9, 0.1])[0]
        massage_chair_available = random.choices([True, False], weights=[0.3, 0.7])[0]

        # Generate visit data
        visit_data = {
            "onsen_id": onsen_id,
            "entry_fee_yen": random.choice([100, 200, 300, 400, 500, 800, 1000]),
            "payment_method": random.choice(self.PAYMENT_METHODS),
            "weather": weather,
            "time_of_day": time_of_day,
            "temperature_outside_celsius": outside_temp,
            "visit_time": visit_date,
            "stay_length_minutes": random.randint(30, 120),
            "visited_with": visited_with,
            "travel_mode": travel_mode,
            "travel_time_minutes": random.randint(5, 60),
            "exercise_before_onsen": exercise_before,
            "exercise_type": (
                random.choice(self.EXERCISE_TYPES) if exercise_before else None
            ),
            "exercise_length_minutes": (
                random.randint(15, 60) if exercise_before else None
            ),
            "crowd_level": random.choice(self.CROWD_LEVELS),
            "view_rating": self._get_realistic_ratings("view"),
            "navigability_rating": random.randint(6, 10),
            "cleanliness_rating": self._get_realistic_ratings("cleanliness"),
            "main_bath_type": main_bath_type,
            "main_bath_temperature": main_bath_temp,
            "main_bath_water_type": random.choice(self.WATER_TYPES),
            "water_color": random.choice(self.WATER_COLORS),
            "smell_intensity_rating": random.randint(3, 8),
            "changing_room_cleanliness_rating": self._get_realistic_ratings(
                "cleanliness"
            ),
            "locker_availability_rating": random.randint(6, 10),
            "had_soap": had_soap,
            "had_sauna": had_sauna,
            "had_outdoor_bath": had_outdoor_bath,
            "had_rest_area": had_rest_area,
            "had_food_service": had_food_service,
            "massage_chair_available": massage_chair_available,
            "pre_visit_mood": random.choice(self.MOODS),
            "post_visit_mood": random.choice(["relaxed", "very relaxed", "energetic"]),
            "energy_level_change": random.randint(-2, 3),
            "hydration_level": random.randint(4, 9),
            "multi_onsen_day": False,
            "atmosphere_rating": random.randint(7, 10),
            "personal_rating": random.randint(6, 10),
            "accessibility_rating": self._get_realistic_ratings("accessibility"),
            "notes": self._generate_optional_notes(),
        }

        # Override with any provided kwargs
        visit_data.update(kwargs)

        return MockOnsenVisit(**visit_data)

    def generate_multi_onsen_day(
        self,
        onsen_ids: list[int],
        visit_date: Optional[datetime] = None,
        start_time: Optional[str] = None,
        **kwargs,
    ) -> list[MockOnsenVisit]:
        """Generate multiple onsen visits for the same day."""

        if not onsen_ids:
            raise ValueError("At least one onsen ID must be provided")

        if visit_date is None:
            visit_date = self.fake.date_time_between(start_date="-1y", end_date="now")

        # Normalize to start of day
        visit_date = visit_date.replace(hour=0, minute=0, second=0, microsecond=0)

        visits = []
        base_time = visit_date

        for i, onsen_id in enumerate(onsen_ids):
            # Calculate visit time (spread throughout the day)
            if start_time == "morning":
                hour = 8 + (i * 3)  # Start at 8 AM, every 3 hours
            elif start_time == "afternoon":
                hour = 12 + (i * 2)  # Start at 12 PM, every 2 hours
            else:
                hour = 10 + (i * 2)  # Start at 10 AM, every 2 hours

            visit_time = base_time + timedelta(
                hours=hour, minutes=random.randint(0, 59)
            )

            # Generate visit data
            visit = self.generate_single_visit(
                onsen_id=onsen_id,
                visit_date=visit_time,
                multi_onsen_day=True,
                visit_order=i + 1,
                **kwargs,
            )

            # Set previous/next location references
            if i > 0:
                visit.previous_location = visits[i - 1].onsen_id
            if i < len(onsen_ids) - 1:
                visit.next_location = onsen_ids[i + 1]

            visits.append(visit)

        return visits

    def generate_visit_series(
        self,
        onsen_ids: list[int],
        num_days: int = 7,
        visits_per_day: int = 1,
        start_date: Optional[datetime] = None,
        **kwargs,
    ) -> list[MockOnsenVisit]:
        """Generate a series of visits over multiple days."""

        if start_date is None:
            start_date = datetime.now() - timedelta(days=num_days)

        all_visits = []

        for day in range(num_days):
            current_date = start_date + timedelta(days=day)

            # Randomly select onsens for this day
            day_onsen_ids = random.sample(
                onsen_ids, min(visits_per_day, len(onsen_ids))
            )

            if len(day_onsen_ids) == 1:
                # Single visit day
                visit = self.generate_single_visit(
                    onsen_id=day_onsen_ids[0],
                    visit_date=current_date + timedelta(hours=random.randint(10, 18)),
                    **kwargs,
                )
                all_visits.append(visit)
            else:
                # Multi-onsen day
                day_visits = self.generate_multi_onsen_day(
                    onsen_ids=day_onsen_ids, visit_date=current_date, **kwargs
                )
                all_visits.extend(day_visits)

        return all_visits

    def generate_seasonal_visits(
        self, onsen_ids: list[int], season: str, num_visits: int = 10, **kwargs
    ) -> list[MockOnsenVisit]:
        """Generate visits for a specific season with appropriate characteristics."""

        # Determine date range for season
        current_year = datetime.now().year
        season_dates = {
            "spring": (datetime(current_year, 3, 1), datetime(current_year, 5, 31)),
            "summer": (datetime(current_year, 6, 1), datetime(current_year, 8, 31)),
            "autumn": (datetime(current_year, 9, 1), datetime(current_year, 11, 30)),
            "winter": (datetime(current_year, 12, 1), datetime(current_year, 2, 28)),
        }

        if season not in season_dates:
            raise ValueError(
                f"Invalid season: {season}. Use: {list(season_dates.keys())}"
            )

        start_date, end_date = season_dates[season]

        visits = []
        for _ in range(num_visits):
            visit_date = self.fake.date_time_between(
                start_date=start_date, end_date=end_date
            )

            # Adjust characteristics based on season
            season_kwargs = kwargs.copy()

            if season == "summer":
                season_kwargs.update(
                    {
                        "time_of_day": random.choice(
                            ["morning", "evening"]
                        ),  # Avoid hot afternoon
                        "temperature_outside_celsius": random.uniform(25.0, 35.0),
                    }
                )
            elif season == "winter":
                season_kwargs.update(
                    {
                        "time_of_day": random.choice(
                            ["afternoon", "evening"]
                        ),  # Avoid cold morning
                        "temperature_outside_celsius": random.uniform(5.0, 15.0),
                    }
                )

            visit = self.generate_single_visit(
                onsen_id=random.choice(onsen_ids),
                visit_date=visit_date,
                **season_kwargs,
            )
            visits.append(visit)

        return visits


# Convenience functions for common use cases
def create_single_visit(
    onsen_id: int, visit_date: Optional[datetime] = None, **kwargs
) -> MockOnsenVisit:
    """Create a single mock onsen visit."""
    generator = MockVisitDataGenerator()
    return generator.generate_single_visit(onsen_id, visit_date, **kwargs)


def create_multi_onsen_day(
    onsen_ids: list[int], visit_date: Optional[datetime] = None, **kwargs
) -> list[MockOnsenVisit]:
    """Create multiple onsen visits for the same day."""
    generator = MockVisitDataGenerator()
    return generator.generate_multi_onsen_day(onsen_ids, visit_date, **kwargs)


def create_visit_series(
    onsen_ids: list[int], num_days: int = 7, visits_per_day: int = 1, **kwargs
) -> list[MockOnsenVisit]:
    """Create a series of visits over multiple days."""
    generator = MockVisitDataGenerator()
    return generator.generate_visit_series(
        onsen_ids, num_days, visits_per_day, **kwargs
    )


def create_seasonal_visits(
    onsen_ids: list[int], season: str, num_visits: int = 10, **kwargs
) -> list[MockOnsenVisit]:
    """Create visits for a specific season."""
    generator = MockVisitDataGenerator()
    return generator.generate_seasonal_visits(onsen_ids, season, num_visits, **kwargs)


def create_realistic_visit_scenario(
    onsen_ids: list[int], scenario_type: str = "random", **kwargs
) -> list[MockOnsenVisit]:
    """Create a realistic visit scenario based on type."""

    generator = MockVisitDataGenerator()

    if scenario_type == "weekend_warrior":
        # Someone who visits multiple onsens on weekends
        return generator.generate_visit_series(
            onsen_ids=onsen_ids,
            num_days=4,  # 4 weekends
            visits_per_day=2,  # 2 visits per weekend
            **kwargs,
        )

    elif scenario_type == "daily_visitor":
        # Someone who visits almost daily
        return generator.generate_visit_series(
            onsen_ids=onsen_ids, num_days=14, visits_per_day=1, **kwargs  # 2 weeks
        )

    elif scenario_type == "seasonal_explorer":
        # Someone who visits different onsens based on season
        visits = []
        for season in ["spring", "summer", "autumn", "winter"]:
            season_visits = generator.generate_seasonal_visits(
                onsen_ids=onsen_ids, season=season, num_visits=3, **kwargs
            )
            visits.extend(season_visits)
        return visits

    elif scenario_type == "multi_onsen_enthusiast":
        # Someone who does multi-onsen days
        visits = []
        for _ in range(5):  # 5 multi-onsen days
            day_onsen_ids = random.sample(onsen_ids, min(3, len(onsen_ids)))
            day_visits = generator.generate_multi_onsen_day(
                onsen_ids=day_onsen_ids, **kwargs
            )
            visits.extend(day_visits)
        return visits

    else:  # random
        # Random mix of scenarios
        num_days = kwargs.get("num_days", random.randint(5, 15))
        visits_per_day = kwargs.get("visits_per_day", random.randint(1, 3))
        return generator.generate_visit_series(
            onsen_ids=onsen_ids,
            num_days=num_days,
            visits_per_day=visits_per_day,
        )


# Example usage and testing
if __name__ == "__main__":
    # Example: Generate some mock data
    generator = MockVisitDataGenerator()

    # Single visit
    single_visit = generator.generate_single_visit(onsen_id=1)
    print(f"Single visit to onsen {single_visit.onsen_id}")
    print(f"  Date: {single_visit.visit_time}")
    print(f"  Temperature: {single_visit.temperature_outside_celsius}°C")
    print(f"  Stay length: {single_visit.stay_length_minutes} minutes")
    print(f"  Personal rating: {single_visit.personal_rating}/10")

    # Multi-onsen day
    multi_visits = generator.generate_multi_onsen_day([1, 2, 3])
    print(f"\nMulti-onsen day with {len(multi_visits)} visits")
    for visit in multi_visits:
        print(
            f"  Onsen {visit.onsen_id}: Order {visit.visit_order}, Time {visit.visit_time.strftime('%H:%M')}"
        )

    # Seasonal visits
    summer_visits = generator.generate_seasonal_visits([1, 2, 3], "summer", 5)
    print(f"\nSummer visits: {len(summer_visits)} visits")
    for visit in summer_visits:
        print(
            f"  {visit.visit_time.strftime('%Y-%m-%d %H:%M')}: {visit.temperature_outside_celsius}°C"
        )
