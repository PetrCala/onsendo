"""
Tests for mock visit data generation and logic chains.
"""

import pytest
from datetime import datetime
from src.testing.mocks.mock_visit_data import (
    MockOnsenVisit,
    MockVisitDataGenerator,
    create_single_visit,
    create_multi_onsen_day,
)


class TestMockOnsenVisit:
    """Test the MockOnsenVisit dataclass and its validation logic."""

    def test_sauna_logic_validation(self):
        """Test that sauna-related data is consistent when sauna is not available."""
        visit = MockOnsenVisit(
            onsen_id=1,
            entry_fee_yen=500,
            payment_method="cash",
            weather="sunny",
            time_of_day="afternoon",
            temperature_outside_celsius=25.0,
            visit_time=datetime.now(),
            stay_length_minutes=60,
            visited_with="alone",
            travel_mode="car",
            travel_time_minutes=15,
            exercise_before_onsen=False,
            accessibility_rating=8,
            crowd_level="moderate",
            view_rating=8,
            navigability_rating=7,
            cleanliness_rating=9,
            main_bath_type="indoor",
            main_bath_temperature=40.0,
            water_color="clear",
            smell_intensity_rating=5,
            changing_room_cleanliness_rating=8,
            locker_availability_rating=7,
            had_soap=True,
            had_sauna=False,  # No sauna
            had_outdoor_bath=True,
            had_rest_area=True,
            had_food_service=False,
            massage_chair_available=False,
            pre_visit_mood="relaxed",
            post_visit_mood="very relaxed",
            energy_level_change=1,
            hydration_level=7,
            atmosphere_rating=8,
            personal_rating=8,
        )

        # Verify sauna logic
        assert visit.had_sauna is False
        assert visit.sauna_visited is False
        assert visit.sauna_temperature is None
        assert visit.sauna_steam is None
        assert visit.sauna_duration_minutes is None
        assert visit.sauna_rating is None

    def test_outdoor_bath_logic_validation(self):
        """Test that outdoor bath-related data is consistent when outdoor bath is not available."""
        visit = MockOnsenVisit(
            onsen_id=1,
            entry_fee_yen=500,
            payment_method="cash",
            weather="sunny",
            time_of_day="afternoon",
            temperature_outside_celsius=25.0,
            visit_time=datetime.now(),
            stay_length_minutes=60,
            visited_with="alone",
            travel_mode="car",
            travel_time_minutes=15,
            exercise_before_onsen=False,
            accessibility_rating=8,
            crowd_level="moderate",
            view_rating=8,
            navigability_rating=7,
            cleanliness_rating=9,
            main_bath_type="indoor",
            main_bath_temperature=40.0,
            water_color="clear",
            smell_intensity_rating=5,
            changing_room_cleanliness_rating=8,
            locker_availability_rating=7,
            had_soap=True,
            had_sauna=True,
            had_outdoor_bath=False,  # No outdoor bath
            had_rest_area=True,
            had_food_service=False,
            massage_chair_available=False,
            pre_visit_mood="relaxed",
            post_visit_mood="very relaxed",
            energy_level_change=1,
            hydration_level=7,
            atmosphere_rating=8,
            personal_rating=8,
        )

        # Verify outdoor bath logic
        assert visit.had_outdoor_bath is False
        assert visit.outdoor_bath_visited is False
        assert visit.outdoor_bath_temperature is None
        assert visit.outdoor_bath_rating is None

    def test_exercise_logic_validation(self):
        """Test that exercise-related data is consistent when no exercise before onsen."""
        visit = MockOnsenVisit(
            onsen_id=1,
            entry_fee_yen=500,
            payment_method="cash",
            weather="sunny",
            time_of_day="afternoon",
            temperature_outside_celsius=25.0,
            visit_time=datetime.now(),
            stay_length_minutes=60,
            visited_with="alone",
            travel_mode="car",
            travel_time_minutes=15,
            exercise_before_onsen=False,  # No exercise
            accessibility_rating=8,
            crowd_level="moderate",
            view_rating=8,
            navigability_rating=7,
            cleanliness_rating=9,
            main_bath_type="indoor",
            main_bath_temperature=40.0,
            water_color="clear",
            smell_intensity_rating=5,
            changing_room_cleanliness_rating=8,
            locker_availability_rating=7,
            had_soap=True,
            had_sauna=True,
            had_outdoor_bath=True,
            had_rest_area=True,
            had_food_service=False,
            massage_chair_available=False,
            pre_visit_mood="relaxed",
            post_visit_mood="very relaxed",
            energy_level_change=1,
            hydration_level=7,
            atmosphere_rating=8,
            personal_rating=8,
        )

        # Verify exercise logic
        assert visit.exercise_before_onsen is False
        assert visit.exercise_type is None
        assert visit.exercise_length_minutes is None

    def test_multi_onsen_logic_validation(self):
        """Test that multi-onsen day data is consistent when not a multi-onsen day."""
        visit = MockOnsenVisit(
            onsen_id=1,
            entry_fee_yen=500,
            payment_method="cash",
            weather="sunny",
            time_of_day="afternoon",
            temperature_outside_celsius=25.0,
            visit_time=datetime.now(),
            stay_length_minutes=60,
            visited_with="alone",
            travel_mode="car",
            travel_time_minutes=15,
            exercise_before_onsen=False,
            accessibility_rating=8,
            crowd_level="moderate",
            view_rating=8,
            navigability_rating=7,
            cleanliness_rating=9,
            main_bath_type="indoor",
            main_bath_temperature=40.0,
            water_color="clear",
            smell_intensity_rating=5,
            changing_room_cleanliness_rating=8,
            locker_availability_rating=7,
            had_soap=True,
            had_sauna=True,
            had_outdoor_bath=True,
            had_rest_area=True,
            had_food_service=False,
            massage_chair_available=False,
            pre_visit_mood="relaxed",
            post_visit_mood="very relaxed",
            energy_level_change=1,
            hydration_level=7,
            atmosphere_rating=8,
            personal_rating=8,
            multi_onsen_day=False,  # Not a multi-onsen day
        )

        # Verify multi-onsen logic
        assert visit.multi_onsen_day is False
        assert visit.visit_order is None
        assert visit.previous_location is None
        assert visit.next_location is None


class TestMockVisitDataGenerator:
    """Test the MockVisitDataGenerator class."""

    def test_generate_single_visit(self):
        """Test generating a single visit."""
        generator = MockVisitDataGenerator()
        visit = generator.generate_single_visit(onsen_id=1)

        assert visit.onsen_id == 1
        assert isinstance(visit.entry_fee_yen, int)
        assert visit.payment_method in generator.PAYMENT_METHODS
        assert visit.weather in generator.WEATHER_CONDITIONS
        assert visit.time_of_day in generator.TIME_OF_DAY
        assert isinstance(visit.temperature_outside_celsius, float)
        assert isinstance(visit.visit_time, datetime)
        assert isinstance(visit.stay_length_minutes, int)
        assert visit.visited_with in generator.VISITED_WITH
        assert visit.travel_mode in generator.TRAVEL_MODES
        assert isinstance(visit.travel_time_minutes, int)
        assert isinstance(visit.exercise_before_onsen, bool)
        assert visit.accessibility_rating in range(1, 11)
        assert visit.crowd_level in generator.CROWD_LEVELS
        assert visit.view_rating in range(1, 11)
        assert visit.navigability_rating in range(1, 11)
        assert visit.cleanliness_rating in range(1, 11)
        assert visit.main_bath_type in generator.MAIN_BATH_TYPES
        assert isinstance(visit.main_bath_temperature, float)
        assert visit.water_color in generator.WATER_COLORS
        assert visit.smell_intensity_rating in range(1, 11)
        assert visit.changing_room_cleanliness_rating in range(1, 11)
        assert visit.locker_availability_rating in range(1, 11)
        assert isinstance(visit.had_soap, bool)
        assert isinstance(visit.had_sauna, bool)
        assert isinstance(visit.had_outdoor_bath, bool)
        assert isinstance(visit.had_rest_area, bool)
        assert isinstance(visit.had_food_service, bool)
        assert isinstance(visit.massage_chair_available, bool)
        assert visit.pre_visit_mood in generator.MOODS
        assert isinstance(visit.post_visit_mood, str)
        assert visit.energy_level_change in range(-5, 6)
        assert visit.hydration_level in range(1, 11)
        assert visit.atmosphere_rating in range(1, 11)
        assert visit.personal_rating in range(1, 11)

    def test_generate_multi_onsen_day(self):
        """Test generating multiple visits for the same day."""
        generator = MockVisitDataGenerator()
        visits = generator.generate_multi_onsen_day([1, 2, 3])

        assert len(visits) == 3
        assert all(visit.multi_onsen_day for visit in visits)
        assert [visit.visit_order for visit in visits] == [1, 2, 3]
        assert [visit.onsen_id for visit in visits] == [1, 2, 3]

        # Check that all visits are on the same day
        first_date = visits[0].visit_time.date()
        assert all(visit.visit_time.date() == first_date for visit in visits)

        # Check visit order timing
        for i in range(1, len(visits)):
            assert visits[i].visit_time > visits[i - 1].visit_time

    def test_seasonal_temperature_logic(self):
        """Test that seasonal temperatures are realistic."""
        generator = MockVisitDataGenerator()

        # Test summer visits (should avoid afternoon)
        summer_visits = generator.generate_seasonal_visits([1], "summer", 5)
        for visit in summer_visits:
            assert visit.time_of_day in ["morning", "evening"]
            assert 25.0 <= visit.temperature_outside_celsius <= 35.0

        # Test winter visits (should avoid morning)
        winter_visits = generator.generate_seasonal_visits([1], "winter", 5)
        for visit in winter_visits:
            assert visit.time_of_day in ["afternoon", "evening"]
            assert 5.0 <= visit.temperature_outside_celsius <= 15.0


class TestConvenienceFunctions:
    """Test the convenience functions."""

    def test_create_single_visit(self):
        """Test the create_single_visit convenience function."""
        visit = create_single_visit(onsen_id=1)
        assert visit.onsen_id == 1
        assert isinstance(visit, MockOnsenVisit)

    def test_create_multi_onsen_day(self):
        """Test the create_multi_onsen_day convenience function."""
        visits = create_multi_onsen_day([1, 2, 3])
        assert len(visits) == 3
        assert all(isinstance(visit, MockOnsenVisit) for visit in visits)
        assert [visit.onsen_id for visit in visits] == [1, 2, 3]
