"""
Integrated scenario generation combining visits with heart rate data.

This module creates complete, analysis-ready datasets with:
- Visit data from user profiles
- Heart rate data linked to visits
- Realistic correlations between visit characteristics and physiological response
- Ready for econometric analysis and heart rate impact studies
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import random
import numpy as np

from src.testing.mocks.scenario_builder import (
    RealisticDataGenerator,
    ScenarioConfig,
    create_analysis_ready_dataset,
)
from src.testing.mocks.user_profiles import UserProfile, get_profile, ALL_PROFILES
from src.testing.mocks.mock_visit_data import MockOnsenVisit
from src.testing.mocks.mock_heart_rate_data import MockHeartRateSession, MockHeartRateDataGenerator


@dataclass
class IntegratedVisitData:
    """Visit data with linked heart rate recording."""
    visit: MockOnsenVisit
    heart_rate_session: Optional[MockHeartRateSession] = None


def generate_heart_rate_for_visit(
    visit: MockOnsenVisit,
    profile: UserProfile,
) -> Optional[MockHeartRateSession]:
    """
    Generate realistic heart rate data linked to an onsen visit.

    Heart rate patterns influenced by:
    - Bath temperature (higher temp → higher HR)
    - Stay length (longer stay → more HR data)
    - Exercise before visit (affects baseline)
    - User profile health focus
    - Sauna use (significant HR elevation)
    """
    # Not all visits have heart rate data
    # Health enthusiasts more likely to track
    tracking_probability = 0.3 + (profile.health_focused * 0.6)

    if random.random() > tracking_probability:
        return None

    hr_generator = MockHeartRateDataGenerator()

    # Determine base heart rate
    if visit.exercise_before_onsen:
        # Elevated from exercise, recovering
        base_hr = random.randint(85, 110)
        scenario = 'recovery'
    else:
        # Normal resting
        base_hr = random.randint(65, 80)
        scenario = 'resting'

    # Calculate recording duration
    # Usually slightly longer than stay (arrive early, leave late)
    extra_time = random.randint(5, 15)
    recording_duration = visit.stay_length_minutes + extra_time

    # Recording starts slightly before visit
    recording_start = visit.visit_time - timedelta(minutes=random.randint(5, 10))
    recording_end = recording_start + timedelta(minutes=recording_duration)

    # Create session with realistic HR progression during onsen visit
    session = hr_generator.generate_session(
        scenario=scenario,
        start_time=recording_start,
        duration_minutes=recording_duration,
        base_heart_rate=base_hr,
        notes=f"Onsen visit to ID {visit.onsen_id} - {visit.time_of_day}",
    )

    # Adjust heart rate based on onsen characteristics
    session = _apply_onsen_effects_to_hr(session, visit)

    return session


def _apply_onsen_effects_to_hr(
    session: MockHeartRateSession,
    visit: MockOnsenVisit,
) -> MockHeartRateSession:
    """
    Apply realistic onsen effects to heart rate data.

    Effects:
    - Hot water increases HR (40-42°C → +10-20 BPM)
    - Sauna significantly increases HR (+20-40 BPM)
    - Outdoor bath in cold weather → larger HR fluctuation
    - Recovery period after leaving bath
    """
    # Calculate effects
    bath_temp = visit.main_bath_temperature or 41.0
    temp_effect = (bath_temp - 38.0) * 5  # +5 BPM per degree above 38°C

    # Find the middle portion of recording (in the bath)
    total_points = len(session.data_points)
    bath_start = int(total_points * 0.15)  # 15% in (getting ready)
    bath_end = int(total_points * 0.85)  # 85% in (getting dressed)

    new_data_points = []

    for i, (timestamp, hr, confidence) in enumerate(session.data_points):
        if bath_start <= i <= bath_end:
            # In the bath - apply temperature effect
            hr_adjusted = hr + temp_effect

            # If used sauna, add peak effect in middle of session
            if visit.sauna_visited and visit.sauna_duration_minutes:
                # Sauna in middle third of visit
                sauna_start = int(total_points * 0.4)
                sauna_end = int(total_points * 0.6)

                if sauna_start <= i <= sauna_end:
                    # Significant HR elevation in sauna
                    sauna_peak_effect = 30 + (visit.sauna_temperature - 80) * 0.5 if visit.sauna_temperature else 30
                    progress_in_sauna = (i - sauna_start) / max(sauna_end - sauna_start, 1)

                    # Peak in middle of sauna
                    sauna_factor = 1 - abs(progress_in_sauna - 0.5) * 2
                    hr_adjusted += sauna_peak_effect * sauna_factor

            # Add variability
            hr_adjusted += np.random.normal(0, 3)

            # Ensure realistic bounds
            hr_adjusted = max(50, min(180, int(hr_adjusted)))

            new_data_points.append((timestamp, hr_adjusted, confidence))
        else:
            # Before/after bath - keep original with slight recovery
            if i > bath_end:
                # Recovery period
                recovery_progress = (i - bath_end) / max(total_points - bath_end, 1)
                recovery_reduction = temp_effect * recovery_progress
                hr_recovered = hr - recovery_reduction
                hr_recovered = max(50, int(hr_recovered))
                new_data_points.append((timestamp, hr_recovered, confidence))
            else:
                new_data_points.append((timestamp, hr, confidence))

    session.data_points = new_data_points
    return session


def create_integrated_dataset(
    onsen_ids: list[int],
    num_visits: int = 100,
    start_date: Optional[datetime] = None,
    days: int = 90,
    hr_coverage: float = 0.6,  # Percentage of visits with HR data
) -> list[IntegratedVisitData]:
    """
    Create integrated dataset with visits and linked heart rate data.

    Args:
        onsen_ids: List of onsen IDs to visit
        num_visits: Total number of visits to generate
        start_date: Start date for visits
        days: Number of days to span
        hr_coverage: Proportion of visits with heart rate data (0.0-1.0)

    Returns:
        List of IntegratedVisitData with linked HR sessions
    """
    # Generate base visits
    visits = create_analysis_ready_dataset(
        onsen_ids=onsen_ids,
        num_visits=num_visits,
        start_date=start_date,
        days=days,
    )

    # Assign profiles to visits (group by proximity in time)
    visit_groups = _group_visits_by_user(visits)

    # Generate heart rate data
    integrated_data = []

    for profile, group_visits in visit_groups:
        for visit in group_visits:
            # Adjust HR coverage by profile health focus
            adjusted_coverage = hr_coverage * (0.5 + profile.health_focused * 0.5)

            if random.random() < adjusted_coverage:
                hr_session = generate_heart_rate_for_visit(visit, profile)
            else:
                hr_session = None

            integrated_data.append(IntegratedVisitData(
                visit=visit,
                heart_rate_session=hr_session,
            ))

    return integrated_data


def _group_visits_by_user(visits: list[MockOnsenVisit]) -> list[tuple[UserProfile, list[MockOnsenVisit]]]:
    """
    Group visits by likely user based on temporal proximity.

    Assumes visits close in time are from the same user.
    """
    if not visits:
        return []

    sorted_visits = sorted(visits, key=lambda v: v.visit_time)

    groups = []
    current_profile = random.choice(ALL_PROFILES)
    current_group = []

    for i, visit in enumerate(sorted_visits):
        if i == 0:
            current_group.append(visit)
            continue

        # Check time gap to previous visit
        time_gap = visit.visit_time - sorted_visits[i-1].visit_time

        # If gap > 3 days, probably different user
        if time_gap.days > 3:
            groups.append((current_profile, current_group))
            current_profile = random.choice(ALL_PROFILES)
            current_group = [visit]
        else:
            current_group.append(visit)

    # Add final group
    if current_group:
        groups.append((current_profile, current_group))

    return groups


def create_heart_rate_analysis_dataset(
    onsen_ids: list[int],
    num_visits: int = 150,
) -> list[IntegratedVisitData]:
    """
    Create dataset optimized for heart rate impact analysis.

    Features:
    - High HR coverage (80%+)
    - Health enthusiast profiles dominant
    - Clear temperature-HR correlations
    - Sauna usage variation
    - Exercise variation
    """
    # Use health-focused profiles
    config = ScenarioConfig(
        start_date=datetime.now() - timedelta(days=120),
        end_date=datetime.now(),
        profiles=[
            get_profile('health_enthusiast'),
            get_profile('relaxation_seeker'),
            get_profile('quality_seeker'),
        ],
        profile_weights=[0.6, 0.2, 0.2],  # Heavy on health enthusiast
        onsen_ids=onsen_ids,
        total_visits=num_visits,
        enable_seasonal_effects=True,
        enable_price_quality_correlation=True,
        enable_weather_effects=True,
        add_missing_data=False,  # Complete data for HR analysis
    )

    generator = RealisticDataGenerator(config)
    visits = generator.generate_scenario()

    # Group and assign profiles
    visit_groups = _group_visits_by_user(visits)

    integrated_data = []
    for profile, group_visits in visit_groups:
        for visit in group_visits:
            # Very high HR coverage for analysis
            if random.random() < 0.85:
                hr_session = generate_heart_rate_for_visit(visit, profile)
            else:
                hr_session = None

            integrated_data.append(IntegratedVisitData(
                visit=visit,
                heart_rate_session=hr_session,
            ))

    return integrated_data


def create_pricing_analysis_dataset(
    onsen_ids: list[int],
    num_visits: int = 200,
) -> list[MockOnsenVisit]:
    """
    Create dataset optimized for pricing/value analysis.

    Features:
    - Wide price range variation
    - Clear price-quality correlations
    - Budget vs quality seeker mix
    - Good sample at each price tier
    """
    config = ScenarioConfig(
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        profiles=[
            get_profile('quality_seeker'),
            get_profile('budget_traveler'),
            get_profile('social_visitor'),
            get_profile('tourist'),
        ],
        profile_weights=[0.3, 0.3, 0.2, 0.2],
        onsen_ids=onsen_ids,
        total_visits=num_visits,
        enable_seasonal_effects=True,
        enable_price_quality_correlation=True,  # Critical for this analysis
        enable_weather_effects=True,
        add_missing_data=True,
        missing_data_rate=0.04,
    )

    generator = RealisticDataGenerator(config)
    return generator.generate_scenario()


def create_spatial_analysis_dataset(
    onsen_ids: list[int],
    num_visits: int = 150,
) -> list[MockOnsenVisit]:
    """
    Create dataset optimized for spatial/geographic analysis.

    Features:
    - Explorer and tourist profiles dominant
    - Wide geographic coverage
    - Multi-onsen days
    - Travel pattern variation
    """
    config = ScenarioConfig(
        start_date=datetime.now() - timedelta(days=120),
        end_date=datetime.now(),
        profiles=[
            get_profile('explorer'),
            get_profile('tourist'),
            get_profile('local_regular'),
        ],
        profile_weights=[0.5, 0.3, 0.2],
        onsen_ids=onsen_ids,
        total_visits=num_visits,
        enable_seasonal_effects=True,
        enable_price_quality_correlation=True,
        enable_weather_effects=True,
        add_missing_data=True,
        missing_data_rate=0.05,
    )

    generator = RealisticDataGenerator(config)
    return generator.generate_scenario()


def create_temporal_analysis_dataset(
    onsen_ids: list[int],
    num_visits: int = 250,
    months: int = 12,
) -> list[MockOnsenVisit]:
    """
    Create dataset optimized for temporal/seasonal analysis.

    Features:
    - Full year coverage for seasonal patterns
    - Local regular dominant (consistent visitor)
    - Clear temporal trends
    - Day of week variation
    """
    config = ScenarioConfig(
        start_date=datetime.now() - timedelta(days=months * 30),
        end_date=datetime.now(),
        profiles=[
            get_profile('local_regular'),
            get_profile('health_enthusiast'),
            get_profile('relaxation_seeker'),
        ],
        profile_weights=[0.5, 0.3, 0.2],
        onsen_ids=onsen_ids,
        total_visits=num_visits,
        enable_seasonal_effects=True,  # Critical for temporal analysis
        enable_price_quality_correlation=True,
        enable_weather_effects=True,
        enable_learning_effects=True,  # Ratings improve over time
        add_missing_data=True,
        missing_data_rate=0.06,
    )

    generator = RealisticDataGenerator(config)
    return generator.generate_scenario()
