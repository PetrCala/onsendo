"""
User profiles and personas for realistic mock data generation.

This module defines distinct user archetypes with characteristic behaviors,
preferences, and visiting patterns. Each profile generates data with realistic
correlations and econometric relationships suitable for analysis.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random
from typing import Optional, Any

import numpy as np


@dataclass
class UserProfile:
    """
    User profile defining characteristic behaviors and preferences.

    Profiles encode realistic correlations between variables:
    - Quality seekers rate cleanliness high
    - Budget travelers prefer cheaper onsens
    - Health enthusiasts exercise before visits
    - Relaxation seekers visit during quiet times
    """

    name: str
    description: str

    # Visit frequency and timing
    visits_per_month: float  # Average visits per month
    preferred_times: list[str]  # Preferred times of day
    preferred_days: list[str]  # Preferred days (weekday, weekend, any)
    multi_onsen_probability: float  # Probability of multi-onsen days

    # Travel and logistics
    preferred_travel_modes: dict[str, float]  # Mode -> probability
    typical_travel_time_range: tuple[int, int]  # Minutes
    price_sensitivity: float  # 0-1, higher = more price sensitive
    max_acceptable_price: int  # Yen

    # Experience preferences
    facility_preferences: dict[str, float]  # Feature -> importance weight
    quality_standards: dict[str, float]  # Aspect -> minimum acceptable rating
    experience_seeking: float  # 0-1, higher = seeks new experiences

    # Rating behavior
    rating_bias: float  # -2 to +2, overall rating tendency
    rating_variance: float  # 0-2, consistency of ratings
    rating_correlations: dict[str, float]  # Which factors most influence personal rating

    # Health and wellness
    exercise_probability: float  # Probability of exercising before visit
    health_focused: float  # 0-1, importance of health benefits
    relaxation_seeking: float  # 0-1, importance of relaxation

    # Social patterns
    social_preference: dict[str, float]  # Visiting companion -> probability
    crowd_tolerance: float  # 0-1, tolerance for crowds

    # Seasonal patterns
    seasonal_preferences: dict[str, float]  # Season -> relative preference
    weather_sensitivity: float  # 0-1, how much weather affects decisions

    def __post_init__(self):
        """Validate profile parameters."""
        assert 0 <= self.price_sensitivity <= 1, "price_sensitivity must be 0-1"
        assert 0 <= self.experience_seeking <= 1, "experience_seeking must be 0-1"
        assert -2 <= self.rating_bias <= 2, "rating_bias must be -2 to 2"
        assert 0 <= self.rating_variance <= 2, "rating_variance must be 0-2"

    def generate_personal_rating(
        self,
        cleanliness: int,
        atmosphere: int,
        view: int,
        entry_fee: int,
        crowd_level: str,
        weather: str,
        **kwargs
    ) -> int:
        """
        Generate personal rating based on profile preferences and correlations.

        This creates realistic econometric relationships for analysis.
        """
        # Base rating from facility ratings
        component_ratings = {
            'cleanliness': cleanliness,
            'atmosphere': atmosphere,
            'view': view,
        }

        # Weighted average of components based on profile
        base_score = sum(
            rating * self.rating_correlations.get(component, 0.33)
            for component, rating in component_ratings.items()
        )

        # Price effect (diminishing returns for quality seekers, strong for budget)
        price_effect = 0
        if entry_fee > self.max_acceptable_price:
            price_effect = -self.price_sensitivity * 2
        else:
            # Cheaper can be better for budget travelers
            price_factor = 1 - (entry_fee / self.max_acceptable_price)
            price_effect = price_factor * self.price_sensitivity * 0.5

        # Crowd effect
        crowd_effects = {
            'empty': 0.5 if self.crowd_tolerance < 0.3 else 0.8,
            'quiet': 0.8 if self.crowd_tolerance < 0.5 else 0.9,
            'moderate': 0.7,
            'busy': 0.5 if self.crowd_tolerance > 0.7 else 0.3,
            'crowded': 0.3 if self.crowd_tolerance > 0.7 else -0.5,
        }
        crowd_effect = crowd_effects.get(crowd_level, 0.5)

        # Weather effect
        weather_effects = {
            'sunny': 0.5,
            'cloudy': 0.2,
            'partly cloudy': 0.3,
            'rainy': -0.3 if self.weather_sensitivity > 0.5 else 0.2,
            'snowy': 0.5 if self.weather_sensitivity > 0.5 else 0.1,
        }
        weather_effect = weather_effects.get(weather, 0) * self.weather_sensitivity

        # Combine all effects
        final_score = (
            base_score
            + price_effect
            + crowd_effect
            + weather_effect
            + self.rating_bias
        )

        # Add variance
        final_score += np.random.normal(0, self.rating_variance)

        # Bound to 1-10
        return max(1, min(10, int(round(final_score))))


# Predefined user profiles representing different visitor archetypes
QUALITY_SEEKER = UserProfile(
    name="Quality Seeker",
    description="Discerning visitor who prioritizes cleanliness and atmosphere, willing to pay premium",
    visits_per_month=4.0,
    preferred_times=['afternoon', 'evening'],
    preferred_days=['weekend', 'any'],
    multi_onsen_probability=0.2,
    preferred_travel_modes={'car': 0.6, 'taxi': 0.3, 'train': 0.1},
    typical_travel_time_range=(10, 30),
    price_sensitivity=0.2,
    max_acceptable_price=1500,
    facility_preferences={
        'cleanliness': 1.0,
        'atmosphere': 0.9,
        'view': 0.7,
        'facilities': 0.6,
    },
    quality_standards={
        'cleanliness': 8.0,
        'atmosphere': 7.0,
        'accessibility': 6.0,
    },
    experience_seeking=0.4,
    rating_bias=0.5,
    rating_variance=0.8,
    rating_correlations={
        'cleanliness': 0.5,
        'atmosphere': 0.35,
        'view': 0.15,
    },
    exercise_probability=0.3,
    health_focused=0.5,
    relaxation_seeking=0.9,
    social_preference={
        'partner': 0.4,
        'family': 0.3,
        'alone': 0.2,
        'friend': 0.1,
    },
    crowd_tolerance=0.3,
    seasonal_preferences={
        'spring': 1.0,
        'summer': 0.7,
        'autumn': 1.0,
        'winter': 0.8,
    },
    weather_sensitivity=0.7,
)

BUDGET_TRAVELER = UserProfile(
    name="Budget Traveler",
    description="Price-conscious visitor seeking good value, less demanding on amenities",
    visits_per_month=6.0,
    preferred_times=['morning', 'afternoon'],
    preferred_days=['weekday', 'any'],
    multi_onsen_probability=0.4,
    preferred_travel_modes={'bus': 0.4, 'walk': 0.3, 'bike': 0.2, 'train': 0.1},
    typical_travel_time_range=(15, 45),
    price_sensitivity=0.9,
    max_acceptable_price=500,
    facility_preferences={
        'price': 1.0,
        'accessibility': 0.7,
        'cleanliness': 0.6,
        'atmosphere': 0.4,
    },
    quality_standards={
        'cleanliness': 6.0,
        'atmosphere': 5.0,
        'accessibility': 7.0,
    },
    experience_seeking=0.7,
    rating_bias=-0.3,
    rating_variance=1.2,
    rating_correlations={
        'cleanliness': 0.25,
        'atmosphere': 0.25,
        'view': 0.5,
    },
    exercise_probability=0.5,
    health_focused=0.6,
    relaxation_seeking=0.6,
    social_preference={
        'alone': 0.5,
        'friend': 0.3,
        'partner': 0.2,
    },
    crowd_tolerance=0.7,
    seasonal_preferences={
        'spring': 0.9,
        'summer': 1.0,
        'autumn': 0.9,
        'winter': 0.7,
    },
    weather_sensitivity=0.3,
)

HEALTH_ENTHUSIAST = UserProfile(
    name="Health Enthusiast",
    description="Fitness-focused visitor who exercises before onsen, values health benefits",
    visits_per_month=8.0,
    preferred_times=['morning', 'afternoon'],
    preferred_days=['any'],
    multi_onsen_probability=0.15,
    preferred_travel_modes={'run': 0.3, 'bike': 0.3, 'walk': 0.3, 'car': 0.1},
    typical_travel_time_range=(20, 40),
    price_sensitivity=0.4,
    max_acceptable_price=800,
    facility_preferences={
        'water_quality': 0.9,
        'temperature': 0.8,
        'cleanliness': 0.8,
        'outdoor_bath': 0.7,
    },
    quality_standards={
        'cleanliness': 7.5,
        'atmosphere': 6.0,
        'accessibility': 8.0,
    },
    experience_seeking=0.5,
    rating_bias=0.2,
    rating_variance=0.7,
    rating_correlations={
        'cleanliness': 0.35,
        'atmosphere': 0.3,
        'view': 0.35,
    },
    exercise_probability=0.85,
    health_focused=0.95,
    relaxation_seeking=0.7,
    social_preference={
        'alone': 0.7,
        'partner': 0.2,
        'friend': 0.1,
    },
    crowd_tolerance=0.4,
    seasonal_preferences={
        'spring': 1.0,
        'summer': 0.9,
        'autumn': 1.0,
        'winter': 0.6,
    },
    weather_sensitivity=0.4,
)

RELAXATION_SEEKER = UserProfile(
    name="Relaxation Seeker",
    description="Stress relief focused, seeks quiet times, values atmosphere and tranquility",
    visits_per_month=3.0,
    preferred_times=['evening', 'night'],
    preferred_days=['weekday', 'weekend'],
    multi_onsen_probability=0.1,
    preferred_travel_modes={'car': 0.5, 'taxi': 0.3, 'train': 0.2},
    typical_travel_time_range=(10, 25),
    price_sensitivity=0.3,
    max_acceptable_price=1200,
    facility_preferences={
        'atmosphere': 1.0,
        'view': 0.9,
        'rest_area': 0.8,
        'quiet': 1.0,
    },
    quality_standards={
        'cleanliness': 7.0,
        'atmosphere': 8.5,
        'accessibility': 5.0,
    },
    experience_seeking=0.2,
    rating_bias=0.8,
    rating_variance=0.6,
    rating_correlations={
        'cleanliness': 0.2,
        'atmosphere': 0.6,
        'view': 0.2,
    },
    exercise_probability=0.2,
    health_focused=0.6,
    relaxation_seeking=1.0,
    social_preference={
        'alone': 0.6,
        'partner': 0.3,
        'family': 0.1,
    },
    crowd_tolerance=0.1,
    seasonal_preferences={
        'spring': 0.9,
        'summer': 0.6,
        'autumn': 1.0,
        'winter': 1.0,
    },
    weather_sensitivity=0.5,
)

EXPLORER = UserProfile(
    name="Explorer",
    description="Adventurous visitor seeking variety, tries many different onsens",
    visits_per_month=10.0,
    preferred_times=['morning', 'afternoon', 'evening'],
    preferred_days=['any'],
    multi_onsen_probability=0.6,
    preferred_travel_modes={'car': 0.4, 'train': 0.3, 'bus': 0.2, 'bike': 0.1},
    typical_travel_time_range=(20, 60),
    price_sensitivity=0.5,
    max_acceptable_price=800,
    facility_preferences={
        'variety': 1.0,
        'uniqueness': 0.9,
        'view': 0.8,
        'atmosphere': 0.7,
    },
    quality_standards={
        'cleanliness': 6.5,
        'atmosphere': 6.5,
        'accessibility': 6.5,
    },
    experience_seeking=0.95,
    rating_bias=0.3,
    rating_variance=1.0,
    rating_correlations={
        'cleanliness': 0.3,
        'atmosphere': 0.35,
        'view': 0.35,
    },
    exercise_probability=0.4,
    health_focused=0.6,
    relaxation_seeking=0.6,
    social_preference={
        'friend': 0.4,
        'alone': 0.3,
        'group': 0.2,
        'partner': 0.1,
    },
    crowd_tolerance=0.6,
    seasonal_preferences={
        'spring': 1.0,
        'summer': 1.0,
        'autumn': 1.0,
        'winter': 0.9,
    },
    weather_sensitivity=0.3,
)

SOCIAL_VISITOR = UserProfile(
    name="Social Visitor",
    description="Enjoys onsen as social activity, visits with friends/family, tolerates crowds",
    visits_per_month=5.0,
    preferred_times=['afternoon', 'evening'],
    preferred_days=['weekend'],
    multi_onsen_probability=0.3,
    preferred_travel_modes={'car': 0.6, 'train': 0.3, 'bus': 0.1},
    typical_travel_time_range=(15, 35),
    price_sensitivity=0.6,
    max_acceptable_price=1000,
    facility_preferences={
        'rest_area': 0.9,
        'food_service': 0.8,
        'space': 0.8,
        'atmosphere': 0.7,
    },
    quality_standards={
        'cleanliness': 7.0,
        'atmosphere': 7.0,
        'accessibility': 7.5,
    },
    experience_seeking=0.5,
    rating_bias=0.5,
    rating_variance=0.9,
    rating_correlations={
        'cleanliness': 0.3,
        'atmosphere': 0.4,
        'view': 0.3,
    },
    exercise_probability=0.25,
    health_focused=0.4,
    relaxation_seeking=0.7,
    social_preference={
        'family': 0.4,
        'group': 0.3,
        'friend': 0.2,
        'partner': 0.1,
    },
    crowd_tolerance=0.8,
    seasonal_preferences={
        'spring': 0.9,
        'summer': 1.0,
        'autumn': 0.9,
        'winter': 0.7,
    },
    weather_sensitivity=0.6,
)

LOCAL_REGULAR = UserProfile(
    name="Local Regular",
    description="Neighborhood regular who visits same favorite onsens frequently",
    visits_per_month=12.0,
    preferred_times=['afternoon', 'evening'],
    preferred_days=['any'],
    multi_onsen_probability=0.05,
    preferred_travel_modes={'walk': 0.5, 'bike': 0.3, 'car': 0.2},
    typical_travel_time_range=(5, 15),
    price_sensitivity=0.7,
    max_acceptable_price=600,
    facility_preferences={
        'familiarity': 1.0,
        'convenience': 0.9,
        'cleanliness': 0.7,
        'price': 0.8,
    },
    quality_standards={
        'cleanliness': 7.0,
        'atmosphere': 6.0,
        'accessibility': 8.5,
    },
    experience_seeking=0.1,
    rating_bias=0.0,
    rating_variance=0.5,
    rating_correlations={
        'cleanliness': 0.4,
        'atmosphere': 0.3,
        'view': 0.3,
    },
    exercise_probability=0.4,
    health_focused=0.7,
    relaxation_seeking=0.8,
    social_preference={
        'alone': 0.7,
        'partner': 0.2,
        'friend': 0.1,
    },
    crowd_tolerance=0.5,
    seasonal_preferences={
        'spring': 1.0,
        'summer': 1.0,
        'autumn': 1.0,
        'winter': 1.0,
    },
    weather_sensitivity=0.2,
)

TOURIST = UserProfile(
    name="Tourist",
    description="Visitor from outside region, seeks highly-rated popular onsens",
    visits_per_month=15.0,  # Intensive during short trip
    preferred_times=['morning', 'afternoon'],
    preferred_days=['any'],
    multi_onsen_probability=0.7,
    preferred_travel_modes={'train': 0.4, 'bus': 0.3, 'taxi': 0.2, 'car': 0.1},
    typical_travel_time_range=(30, 90),
    price_sensitivity=0.3,
    max_acceptable_price=1500,
    facility_preferences={
        'reputation': 1.0,
        'uniqueness': 0.9,
        'view': 0.9,
        'atmosphere': 0.8,
    },
    quality_standards={
        'cleanliness': 8.0,
        'atmosphere': 7.5,
        'accessibility': 6.0,
    },
    experience_seeking=0.9,
    rating_bias=0.7,
    rating_variance=1.1,
    rating_correlations={
        'cleanliness': 0.25,
        'atmosphere': 0.45,
        'view': 0.3,
    },
    exercise_probability=0.3,
    health_focused=0.5,
    relaxation_seeking=0.8,
    social_preference={
        'partner': 0.4,
        'friend': 0.3,
        'family': 0.2,
        'alone': 0.1,
    },
    crowd_tolerance=0.5,
    seasonal_preferences={
        'spring': 1.0,
        'summer': 0.8,
        'autumn': 1.0,
        'winter': 0.7,
    },
    weather_sensitivity=0.6,
)


# Profile registry
ALL_PROFILES = [
    QUALITY_SEEKER,
    BUDGET_TRAVELER,
    HEALTH_ENTHUSIAST,
    RELAXATION_SEEKER,
    EXPLORER,
    SOCIAL_VISITOR,
    LOCAL_REGULAR,
    TOURIST,
]

PROFILE_MAP = {profile.name.lower().replace(' ', '_'): profile for profile in ALL_PROFILES}


def get_profile(name: str) -> UserProfile:
    """Get a user profile by name."""
    key = name.lower().replace(' ', '_')
    if key not in PROFILE_MAP:
        available = ', '.join(PROFILE_MAP.keys())
        raise ValueError(f"Unknown profile: {name}. Available: {available}")
    return PROFILE_MAP[key]


def get_random_profile() -> UserProfile:
    """Get a random user profile."""
    return random.choice(ALL_PROFILES)


def get_profile_mix(weights: Optional[dict[str, float]] = None) -> UserProfile:
    """
    Get a random profile with custom weights.

    Args:
        weights: Dict mapping profile names to selection weights

    Returns:
        Randomly selected profile based on weights
    """
    if weights is None:
        return get_random_profile()

    profiles = []
    profile_weights = []

    for name, weight in weights.items():
        profile = get_profile(name)
        profiles.append(profile)
        profile_weights.append(weight)

    return random.choices(profiles, weights=profile_weights)[0]
