"""
Comprehensive scenario builder for generating realistic, analysis-ready mock data.

This module creates sophisticated mock datasets with:
- Realistic correlations between variables
- Econometric relationships suitable for regression analysis
- User profile-based behavioral patterns
- Seasonal effects and temporal trends
- Heart rate data integration
- Geographic patterns
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import random
import numpy as np
from faker import Faker

from src.testing.mocks.user_profiles import (
    UserProfile,
    get_random_profile,
    ALL_PROFILES,
)
from src.testing.mocks.mock_visit_data import MockOnsenVisit

fake = Faker(['ja_JP', 'en_US'])


@dataclass
class ScenarioConfig:
    """Configuration for mock data scenario generation."""

    # Temporal scope
    start_date: datetime
    end_date: datetime

    # User profiles
    profiles: list[UserProfile]
    profile_weights: Optional[list[float]] = None

    # Onsen selection
    onsen_ids: list[int] = None
    onsen_visit_probabilities: Optional[dict[int, float]] = None  # Popularity weights

    # Data volume
    total_visits: Optional[int] = None
    visits_per_user: Optional[int] = None

    # Correlations and effects
    enable_seasonal_effects: bool = True
    enable_price_quality_correlation: bool = True
    enable_weather_effects: bool = True
    enable_learning_effects: bool = True  # Ratings improve over time as user learns
    enable_fatigue_effects: bool = True  # Multi-onsen days have diminishing returns

    # Noise and realism
    add_missing_data: bool = True
    missing_data_rate: float = 0.05
    add_outliers: bool = True
    outlier_rate: float = 0.02

    def __post_init__(self):
        """Validate and set defaults."""
        if self.profile_weights is None:
            self.profile_weights = [1.0] * len(self.profiles)

        if len(self.profile_weights) != len(self.profiles):
            raise ValueError("profile_weights must match length of profiles")

        if self.total_visits is None and self.visits_per_user is None:
            self.visits_per_user = 20  # Default

        days = (self.end_date - self.start_date).days
        if days < 1:
            raise ValueError("end_date must be after start_date")


class RealisticDataGenerator:
    """
    Advanced mock data generator with realistic correlations and econometric relationships.
    """

    def __init__(self, config: ScenarioConfig):
        """Initialize generator with scenario configuration."""
        self.config = config
        self.fake = Faker(['ja_JP', 'en_US'])
        self._setup_constants()
        self._generated_visits = []

    def _setup_constants(self):
        """Setup constants for realistic data generation."""
        self.PAYMENT_METHODS = ['cash', 'card', 'IC card', 'other']
        self.WEATHER_CONDITIONS = ['sunny', 'cloudy', 'rainy', 'snowy', 'partly cloudy']
        self.TIME_OF_DAY = ['morning', 'afternoon', 'evening', 'night']
        self.CROWD_LEVELS = ['empty', 'quiet', 'moderate', 'busy', 'crowded']
        self.MAIN_BATH_TYPES = ['indoor', 'open air', 'mixed', 'other']
        self.WATER_COLORS = ['clear', 'brown', 'green', 'blue', 'milky']
        self.MOODS = ['relaxed', 'stressed', 'anxious', 'tired', 'energetic', 'excited']
        self.EXERCISE_TYPES = ['running', 'walking', 'cycling', 'swimming', 'hiking']

        # Price-quality correlation (higher price → better facilities)
        self.PRICE_TIERS = {
            100: {'cleanliness_boost': -1, 'atmosphere_boost': -1, 'facility_probability': 0.3},
            200: {'cleanliness_boost': 0, 'atmosphere_boost': 0, 'facility_probability': 0.5},
            300: {'cleanliness_boost': 0, 'atmosphere_boost': 0, 'facility_probability': 0.6},
            400: {'cleanliness_boost': 1, 'atmosphere_boost': 0, 'facility_probability': 0.7},
            500: {'cleanliness_boost': 1, 'atmosphere_boost': 1, 'facility_probability': 0.75},
            800: {'cleanliness_boost': 2, 'atmosphere_boost': 1, 'facility_probability': 0.85},
            1000: {'cleanliness_boost': 2, 'atmosphere_boost': 2, 'facility_probability': 0.9},
            1500: {'cleanliness_boost': 3, 'atmosphere_boost': 2, 'facility_probability': 0.95},
        }

    def _get_season(self, date: datetime) -> str:
        """Determine season from date."""
        month = date.month
        if month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'autumn'
        else:
            return 'winter'

    def _get_seasonal_temperature(self, season: str, time_of_day: str) -> float:
        """Generate realistic temperature with seasonal variation."""
        base_temps = {
            'spring': (15, 22),
            'summer': (26, 34),
            'autumn': (14, 21),
            'winter': (4, 12),
        }

        base_min, base_max = base_temps[season]

        # Time of day adjustment
        if time_of_day == 'morning':
            temp = np.random.normal((base_min + base_max) / 2 - 3, 2)
        elif time_of_day == 'afternoon':
            temp = np.random.normal(base_max, 2)
        elif time_of_day == 'evening':
            temp = np.random.normal((base_min + base_max) / 2, 2)
        else:  # night
            temp = np.random.normal(base_min, 2)

        return round(max(base_min - 5, min(base_max + 5, temp)), 1)

    def _get_seasonal_weather(self, season: str) -> str:
        """Get weather appropriate for season."""
        weather_probabilities = {
            'spring': {
                'sunny': 0.4,
                'partly cloudy': 0.3,
                'cloudy': 0.2,
                'rainy': 0.1,
            },
            'summer': {
                'sunny': 0.6,
                'partly cloudy': 0.2,
                'cloudy': 0.1,
                'rainy': 0.1,
            },
            'autumn': {
                'sunny': 0.5,
                'partly cloudy': 0.25,
                'cloudy': 0.15,
                'rainy': 0.1,
            },
            'winter': {
                'cloudy': 0.3,
                'sunny': 0.3,
                'partly cloudy': 0.2,
                'snowy': 0.15,
                'rainy': 0.05,
            },
        }

        weather_options = list(weather_probabilities[season].keys())
        weights = list(weather_probabilities[season].values())
        return random.choices(weather_options, weights=weights)[0]

    def _get_crowd_level(self, time_of_day: str, day_of_week: int) -> str:
        """Get realistic crowd level based on time and day."""
        # Weekend (5, 6) is more crowded
        is_weekend = day_of_week >= 5

        if is_weekend:
            if time_of_day == 'morning':
                levels = ['quiet', 'moderate', 'busy']
                weights = [0.3, 0.5, 0.2]
            elif time_of_day == 'afternoon':
                levels = ['moderate', 'busy', 'crowded']
                weights = [0.2, 0.5, 0.3]
            elif time_of_day == 'evening':
                levels = ['busy', 'moderate', 'crowded']
                weights = [0.4, 0.4, 0.2]
            else:  # night
                levels = ['quiet', 'moderate', 'empty']
                weights = [0.5, 0.3, 0.2]
        else:  # weekday
            if time_of_day == 'morning':
                levels = ['empty', 'quiet']
                weights = [0.4, 0.6]
            elif time_of_day == 'afternoon':
                levels = ['quiet', 'moderate']
                weights = [0.6, 0.4]
            elif time_of_day == 'evening':
                levels = ['moderate', 'busy', 'quiet']
                weights = [0.4, 0.3, 0.3]
            else:  # night
                levels = ['empty', 'quiet']
                weights = [0.5, 0.5]

        return random.choices(levels, weights=weights)[0]

    def _select_onsen(self, profile: UserProfile, previous_onsens: list[int]) -> int:
        """
        Select onsen based on user profile and experience seeking behavior.
        """
        available_onsens = self.config.onsen_ids.copy()

        # Explorer profiles prefer new onsens
        if profile.experience_seeking > 0.7:
            # 80% chance to try new onsen
            if random.random() < 0.8 and previous_onsens:
                available_onsens = [o for o in available_onsens if o not in previous_onsens[-5:]]

        # Local regular profiles stick to favorites
        elif profile.experience_seeking < 0.3:
            if previous_onsens and random.random() < 0.7:
                # 70% chance to revisit favorite
                favorite = random.choice(previous_onsens)
                return favorite

        # Use popularity weights if provided
        if self.config.onsen_visit_probabilities:
            weights = [self.config.onsen_visit_probabilities.get(oid, 1.0) for oid in available_onsens]
            return random.choices(available_onsens, weights=weights)[0]

        return random.choice(available_onsens)

    def _generate_correlated_ratings(
        self,
        entry_fee: int,
        profile: UserProfile,
        weather: str,
        crowd_level: str,
        season: str,
    ) -> dict[str, int]:
        """
        Generate facility ratings with realistic correlations.

        Econometric relationships:
        - Price → quality (positive correlation)
        - Cleanliness highly correlated with atmosphere
        - View affected by weather
        - All influence personal rating based on profile
        """
        # Base ratings from price tier
        price_tier_data = min(
            (p for p in self.PRICE_TIERS.keys() if entry_fee <= p),
            key=lambda x: abs(x - entry_fee),
            default=1500,
        )
        price_effects = self.PRICE_TIERS[price_tier_data]

        # Cleanliness (Japanese onsens generally very clean)
        cleanliness_base = random.choices([7, 8, 9, 10], weights=[0.1, 0.3, 0.4, 0.2])[0]
        cleanliness = min(10, max(1, cleanliness_base + price_effects['cleanliness_boost']))

        # Atmosphere (correlated with cleanliness + price)
        atmosphere_base = cleanliness + np.random.normal(0, 1)
        atmosphere = min(10, max(1, int(round(atmosphere_base + price_effects['atmosphere_boost']))))

        # View (affected by weather)
        view_base = random.randint(6, 10)
        weather_view_effect = {
            'sunny': 1,
            'partly cloudy': 0,
            'cloudy': -1,
            'rainy': -2,
            'snowy': 1,  # Can be beautiful
        }
        view = min(10, max(1, view_base + weather_view_effect.get(weather, 0)))

        # Navigability (mostly independent)
        navigability = random.randint(6, 10)

        # Accessibility (related to price - cheaper often less accessible)
        accessibility_base = random.randint(5, 10)
        if entry_fee < 300:
            accessibility = min(10, max(1, accessibility_base - 1))
        else:
            accessibility = accessibility_base

        # Locker availability
        locker = random.randint(7, 10)

        # Changing room cleanliness (highly correlated with general cleanliness)
        changing_room_clean = min(10, max(1, cleanliness + np.random.randint(-1, 2)))

        # Generate personal rating using profile-specific logic
        personal_rating = profile.generate_personal_rating(
            cleanliness=cleanliness,
            atmosphere=atmosphere,
            view=view,
            entry_fee=entry_fee,
            crowd_level=crowd_level,
            weather=weather,
        )

        return {
            'cleanliness_rating': cleanliness,
            'atmosphere_rating': atmosphere,
            'view_rating': view,
            'navigability_rating': navigability,
            'accessibility_rating': accessibility,
            'locker_availability_rating': locker,
            'changing_room_cleanliness_rating': changing_room_clean,
            'personal_rating': personal_rating,
            'smell_intensity_rating': random.randint(3, 8),
        }

    def _select_entry_fee(self, profile: UserProfile) -> int:
        """Select entry fee based on user profile price sensitivity."""
        fees = [100, 200, 300, 400, 500, 800, 1000, 1500]

        # Filter by max acceptable price
        affordable_fees = [f for f in fees if f <= profile.max_acceptable_price]

        if not affordable_fees:
            affordable_fees = [fees[0]]

        # Weight towards lower prices for price-sensitive users
        if profile.price_sensitivity > 0.7:
            # Strong preference for cheaper
            weights = [1/(i+1) for i in range(len(affordable_fees))]
        elif profile.price_sensitivity < 0.3:
            # Willing to pay more
            weights = [(i+1) for i in range(len(affordable_fees))]
        else:
            # Neutral
            weights = [1.0] * len(affordable_fees)

        return random.choices(affordable_fees, weights=weights)[0]

    def generate_visit(
        self,
        profile: UserProfile,
        visit_date: datetime,
        previous_onsens: list[int],
        visit_count: int,
    ) -> MockOnsenVisit:
        """Generate a single realistic visit based on user profile."""

        # Select onsen
        onsen_id = self._select_onsen(profile, previous_onsens)

        # Temporal features
        season = self._get_season(visit_date)
        time_of_day = random.choices(
            profile.preferred_times,
            weights=[1.0] * len(profile.preferred_times)
        )[0]

        day_of_week = visit_date.weekday()

        # Weather (seasonal)
        if self.config.enable_seasonal_effects:
            weather = self._get_seasonal_weather(season)
            temperature = self._get_seasonal_temperature(season, time_of_day)
        else:
            weather = random.choice(self.WEATHER_CONDITIONS)
            temperature = round(random.uniform(5, 35), 1)

        # Crowd level
        crowd_level = self._get_crowd_level(time_of_day, day_of_week)

        # Entry fee
        entry_fee = self._select_entry_fee(profile)

        # Facilities (correlated with price)
        price_tier_data = min(
            (p for p in self.PRICE_TIERS.keys() if entry_fee <= p),
            key=lambda x: abs(x - entry_fee),
            default=1500,
        )
        facility_prob = self.PRICE_TIERS[price_tier_data]['facility_probability']

        had_sauna = random.random() < facility_prob
        had_outdoor_bath = random.random() < facility_prob
        had_rest_area = random.random() < max(0.7, facility_prob)
        had_food_service = random.random() < (facility_prob - 0.1)
        had_soap = random.random() < 0.9
        massage_chair = random.random() < 0.3

        # Generate correlated ratings
        ratings = self._generate_correlated_ratings(
            entry_fee, profile, weather, crowd_level, season
        )

        # Learning effect: ratings slightly improve over time
        if self.config.enable_learning_effects and visit_count > 5:
            learning_boost = min(1, (visit_count - 5) * 0.05)
            ratings['personal_rating'] = min(10, ratings['personal_rating'] + int(learning_boost))

        # Travel mode and time
        travel_mode = random.choices(
            list(profile.preferred_travel_modes.keys()),
            weights=list(profile.preferred_travel_modes.values())
        )[0]
        travel_time = random.randint(*profile.typical_travel_time_range)

        # Social
        visited_with = random.choices(
            list(profile.social_preference.keys()),
            weights=list(profile.social_preference.values())
        )[0]

        # Stay length (influenced by social setting and facilities)
        base_stay = random.randint(45, 90)
        if visited_with in ['family', 'group']:
            base_stay += random.randint(15, 30)
        if had_rest_area and random.random() < 0.6:
            base_stay += random.randint(10, 20)

        # Bath details
        main_bath_type = random.choice(self.MAIN_BATH_TYPES)
        main_bath_temp = round(random.uniform(38, 43), 1)

        # Mood changes
        pre_moods = ['stressed', 'tired', 'anxious', 'neutral']
        post_moods = ['relaxed', 'very relaxed', 'energetic', 'refreshed']
        pre_mood = random.choice(pre_moods)
        post_mood = random.choice(post_moods)

        energy_change = random.randint(1, 3)  # Onsen generally increases energy

        # Create visit
        visit = MockOnsenVisit(
            onsen_id=onsen_id,
            entry_fee_yen=entry_fee,
            payment_method=random.choice(self.PAYMENT_METHODS),
            weather=weather,
            time_of_day=time_of_day,
            temperature_outside_celsius=temperature,
            visit_time=visit_date,
            stay_length_minutes=base_stay,
            visited_with=visited_with,
            travel_mode=travel_mode,
            travel_time_minutes=travel_time,
            crowd_level=crowd_level,
            view_rating=ratings['view_rating'],
            navigability_rating=ratings['navigability_rating'],
            cleanliness_rating=ratings['cleanliness_rating'],
            accessibility_rating=ratings['accessibility_rating'],
            main_bath_type=main_bath_type,
            main_bath_temperature=main_bath_temp,
            water_color=random.choice(self.WATER_COLORS),
            smell_intensity_rating=ratings['smell_intensity_rating'],
            changing_room_cleanliness_rating=ratings['changing_room_cleanliness_rating'],
            locker_availability_rating=ratings['locker_availability_rating'],
            had_soap=had_soap,
            had_sauna=had_sauna,
            had_outdoor_bath=had_outdoor_bath,
            had_rest_area=had_rest_area,
            had_food_service=had_food_service,
            massage_chair_available=massage_chair,
            pre_visit_mood=pre_mood,
            post_visit_mood=post_mood,
            energy_level_change=energy_change,
            hydration_level=random.randint(5, 9),
            atmosphere_rating=ratings['atmosphere_rating'],
            personal_rating=ratings['personal_rating'],
        )

        return visit

    def generate_scenario(self) -> list[MockOnsenVisit]:
        """
        Generate complete scenario based on configuration.

        Returns:
            List of MockOnsenVisit objects with realistic correlations
        """
        all_visits = []

        # Determine how many visits to generate
        if self.config.total_visits:
            num_profiles = self.config.total_visits // 20  # Average per profile
        elif self.config.visits_per_user:
            num_profiles = len(self.config.profiles)
        else:
            num_profiles = len(self.config.profiles)

        # Generate visits for each user profile
        for _ in range(num_profiles):
            profile = random.choices(self.config.profiles, weights=self.config.profile_weights)[0]

            # Determine number of visits for this user
            if self.config.visits_per_user:
                num_visits = self.config.visits_per_user
            else:
                # Sample from profile's monthly rate
                days = (self.config.end_date - self.config.start_date).days
                expected_visits = int(profile.visits_per_month * (days / 30))
                num_visits = max(1, np.random.poisson(expected_visits))

            previous_onsens = []

            # Generate visits for this user
            for visit_idx in range(num_visits):
                # Generate visit date
                days_range = (self.config.end_date - self.config.start_date).days
                random_day = random.randint(0, days_range)
                visit_date = self.config.start_date + timedelta(days=random_day)

                # Generate visit
                visit = self.generate_visit(profile, visit_date, previous_onsens, visit_idx + 1)
                all_visits.append(visit)
                previous_onsens.append(visit.onsen_id)

        # Sort by date
        all_visits.sort(key=lambda v: v.visit_time)

        # Add missing data
        if self.config.add_missing_data:
            all_visits = self._add_missing_data(all_visits)

        return all_visits

    def _add_missing_data(self, visits: list[MockOnsenVisit]) -> list[MockOnsenVisit]:
        """Randomly set some optional fields to None to simulate realistic missing data."""
        for visit in visits:
            if random.random() < self.config.missing_data_rate:
                # Randomly nullify some optional fields
                optional_fields = [
                    'sauna_temperature',
                    'sauna_duration_minutes',
                    'sauna_rating',
                    'outdoor_bath_temperature',
                    'outdoor_bath_rating',
                    'rest_area_rating',
                    'food_quality_rating',
                ]
                field = random.choice(optional_fields)
                setattr(visit, field, None)

        return visits


# Pre-configured scenarios for common use cases
def create_analysis_ready_dataset(
    onsen_ids: list[int],
    num_visits: int = 100,
    start_date: Optional[datetime] = None,
    days: int = 90,
) -> list[MockOnsenVisit]:
    """
    Create a comprehensive dataset ready for all analysis types.

    Features:
    - Mix of all user profiles
    - Seasonal coverage
    - Price-quality correlations
    - Realistic missing data
    - Suitable for econometric analysis
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)

    end_date = start_date + timedelta(days=days)

    config = ScenarioConfig(
        start_date=start_date,
        end_date=end_date,
        profiles=ALL_PROFILES,
        profile_weights=[1.0] * len(ALL_PROFILES),  # Equal mix
        onsen_ids=onsen_ids,
        total_visits=num_visits,
        enable_seasonal_effects=True,
        enable_price_quality_correlation=True,
        enable_weather_effects=True,
        enable_learning_effects=True,
        add_missing_data=True,
        missing_data_rate=0.05,
    )

    generator = RealisticDataGenerator(config)
    return generator.generate_scenario()


def create_econometric_test_dataset(
    onsen_ids: list[int],
    num_visits: int = 200,
) -> list[MockOnsenVisit]:
    """
    Create dataset specifically optimized for econometric analysis.

    Features:
    - Strong price-quality correlations
    - Clear seasonal effects
    - User profile-based heterogeneity
    - Sufficient variation for regression
    """
    config = ScenarioConfig(
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        profiles=[QUALITY_SEEKER, BUDGET_TRAVELER, EXPLORER, TOURIST],
        profile_weights=[0.3, 0.3, 0.2, 0.2],
        onsen_ids=onsen_ids,
        total_visits=num_visits,
        enable_seasonal_effects=True,
        enable_price_quality_correlation=True,
        enable_weather_effects=True,
        enable_learning_effects=True,
        add_missing_data=True,
        missing_data_rate=0.03,
    )

    generator = RealisticDataGenerator(config)
    return generator.generate_scenario()


def create_tourist_scenario(
    onsen_ids: list[int],
    trip_days: int = 7,
    visits_per_day: int = 3,
) -> list[MockOnsenVisit]:
    """
    Create scenario for intensive tourist visiting pattern.

    Perfect for testing:
    - Multi-onsen day analysis
    - Geographic clustering
    - Intensive short-term patterns
    """
    start_date = datetime.now() - timedelta(days=trip_days)

    config = ScenarioConfig(
        start_date=start_date,
        end_date=datetime.now(),
        profiles=[TOURIST],
        onsen_ids=onsen_ids,
        visits_per_user=trip_days * visits_per_day,
        enable_seasonal_effects=True,
        enable_price_quality_correlation=True,
        enable_weather_effects=True,
        enable_fatigue_effects=True,
        add_missing_data=False,  # Tourists tend to record everything
    )

    generator = RealisticDataGenerator(config)
    return generator.generate_scenario()


def create_local_regular_scenario(
    onsen_ids: list[int],
    months: int = 12,
) -> list[MockOnsenVisit]:
    """
    Create scenario for local regular visitor.

    Perfect for testing:
    - Temporal trends
    - Loyalty patterns
    - Long-term health tracking
    """
    config = ScenarioConfig(
        start_date=datetime.now() - timedelta(days=months * 30),
        end_date=datetime.now(),
        profiles=[LOCAL_REGULAR],
        onsen_ids=onsen_ids,
        visits_per_user=months * 12,  # ~12 visits per month
        enable_seasonal_effects=True,
        enable_price_quality_correlation=True,
        enable_weather_effects=True,
        enable_learning_effects=True,
        add_missing_data=True,
        missing_data_rate=0.08,
    )

    generator = RealisticDataGenerator(config)
    return generator.generate_scenario()
