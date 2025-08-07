"""
Mock data for interactive CLI tests.

This module provides predefined user input sequences for testing the interactive
add-visit functionality. Each function returns a list of strings that simulate
user responses to the interactive questionnaire.
"""

from typing import List
from faker import Faker

fake = Faker()

# TODO
# - Use faker to generate more realistic data
# - Use keys to access values instead of indices


def get_complete_flow_inputs() -> List[str]:
    """
    Get user inputs for a complete interactive flow with all features enabled.

    This simulates a user who:
    - Visits an onsen with ID 1
    - Pays 500 yen in cash
    - Has a full experience with sauna, outdoor bath, and rest area
    - Rates everything highly
    - Confirms the visit
    """
    return [
        "1",  # onsen_id
        "500",  # entry_fee_yen
        "cash",  # payment_method
        "",  # visit_time (use current time)
        "sunny",  # weather
        "afternoon",  # time_of_day
        "25.5",  # temperature_outside_celsius
        "60",  # stay_length_minutes
        "alone",  # visited_with
        "car",  # travel_mode
        "15",  # travel_time_minutes
        "n",  # exercise_before_onsen
        "8",  # accessibility_rating
        "9",  # cleanliness_rating
        "7",  # navigability_rating
        "8",  # view_rating
        "9",  # atmosphere_rating
        "open air",  # main_bath_type
        "42.0",  # main_bath_temperature
        "sulfur",  # main_bath_water_type
        "clear",  # water_color
        "6",  # smell_intensity_rating
        "8",  # changing_room_cleanliness_rating
        "7",  # locker_availability_rating
        "y",  # had_soap
        "y",  # had_sauna
        "y",  # sauna_visited
        "85.0",  # sauna_temperature
        "y",  # sauna_steam
        "15",  # sauna_duration_minutes
        "8",  # sauna_rating
        "y",  # had_outdoor_bath
        "y",  # outdoor_bath_visited
        "40.0",  # outdoor_bath_temperature
        "9",  # outdoor_bath_rating
        "y",  # had_rest_area
        "8",  # rest_area_rating
        "n",  # had_food_service
        "n",  # massage_chair_available
        "moderate",  # crowd_level
        "relaxed",  # pre_visit_mood
        "very relaxed",  # post_visit_mood
        "2",  # energy_level_change
        "7",  # hydration_level
        "n",  # multi_onsen_day
        "9",  # personal_rating
        "",  # heart_rate_data
        "y",  # confirm
    ]


def get_exercise_flow_inputs() -> List[str]:
    """
    Get user inputs for a flow where the user exercised before the onsen.

    This simulates a user who:
    - Exercised before visiting (running for 30 minutes)
    - Has a simpler onsen experience (no sauna, outdoor bath, etc.)
    - Uses different travel mode and companions
    """
    return [
        "1",  # onsen_id
        "300",  # entry_fee_yen
        "card",  # payment_method
        "",  # visit_time
        "cloudy",  # weather
        "morning",  # time_of_day
        "20.0",  # temperature_outside_celsius
        "45",  # stay_length_minutes
        "friend",  # visited_with
        "walk",  # travel_mode
        "10",  # travel_time_minutes
        "y",  # exercise_before_onsen
        "running",  # exercise_type
        "30",  # exercise_length_minutes
        "7",  # accessibility_rating
        "8",  # cleanliness_rating
        "6",  # navigability_rating
        "7",  # view_rating
        "8",  # atmosphere_rating
        "indoor",  # main_bath_type
        "40.0",  # main_bath_temperature
        "salt",  # main_bath_water_type
        "brown",  # water_color
        "5",  # smell_intensity_rating
        "7",  # changing_room_cleanliness_rating
        "6",  # locker_availability_rating
        "n",  # had_soap
        "n",  # had_sauna
        "n",  # had_outdoor_bath
        "n",  # had_rest_area
        "n",  # had_food_service
        "n",  # massage_chair_available
        "quiet",  # crowd_level
        "stressed",  # pre_visit_mood
        "relaxed",  # post_visit_mood
        "3",  # energy_level_change
        "6",  # hydration_level
        "n",  # multi_onsen_day
        "8",  # personal_rating
        "",  # heart_rate_data
        "y",  # confirm
    ]


def get_minimal_flow_inputs() -> List[str]:
    """
    Get user inputs for a minimal flow with basic information only.

    This simulates a user who:
    - Provides only essential information
    - Skips most optional features
    - Has a simple onsen experience
    """
    return [
        "1",  # onsen_id
        "200",  # entry_fee_yen
        "cash",  # payment_method
        "",  # visit_time
        "clear",  # weather
        "evening",  # time_of_day
        "18.0",  # temperature_outside_celsius
        "30",  # stay_length_minutes
        "alone",  # visited_with
        "train",  # travel_mode
        "20",  # travel_time_minutes
        "n",  # exercise_before_onsen
        "6",  # accessibility_rating
        "7",  # cleanliness_rating
        "5",  # navigability_rating
        "6",  # view_rating
        "7",  # atmosphere_rating
        "indoor",  # main_bath_type
        "38.0",  # main_bath_temperature
        "sulfur",  # main_bath_water_type
        "clear",  # water_color
        "4",  # smell_intensity_rating
        "6",  # changing_room_cleanliness_rating
        "5",  # locker_availability_rating
        "y",  # had_soap
        "n",  # had_sauna
        "n",  # had_outdoor_bath
        "n",  # had_rest_area
        "n",  # had_food_service
        "n",  # massage_chair_available
        "quiet",  # crowd_level
        "tired",  # pre_visit_mood
        "relaxed",  # post_visit_mood
        "1",  # energy_level_change
        "5",  # hydration_level
        "n",  # multi_onsen_day
        "7",  # personal_rating
        "",  # heart_rate_data
        "y",  # confirm
    ]


def get_invalid_onsen_retry_inputs() -> List[str]:
    """
    Get user inputs that include an invalid onsen ID followed by a valid one.

    This simulates a user who:
    - First enters an invalid onsen ID (999)
    - Then enters a valid onsen ID (1)
    - Completes the rest of the flow normally
    """
    return [
        "999",  # invalid onsen_id
        "1",  # valid onsen_id (second attempt)
        "500",  # entry_fee_yen
        "cash",  # payment_method
        "",  # visit_time
        "sunny",  # weather
        "afternoon",  # time_of_day
        "25.0",  # temperature_outside_celsius
        "60",  # stay_length_minutes
        "alone",  # visited_with
        "car",  # travel_mode
        "15",  # travel_time_minutes
        "n",  # exercise_before_onsen
        "8",  # accessibility_rating
        "9",  # cleanliness_rating
        "7",  # navigability_rating
        "8",  # view_rating
        "9",  # atmosphere_rating
        "open air",  # main_bath_type
        "42.0",  # main_bath_temperature
        "sulfur",  # main_bath_water_type
        "clear",  # water_color
        "6",  # smell_intensity_rating
        "8",  # changing_room_cleanliness_rating
        "7",  # locker_availability_rating
        "y",  # had_soap
        "n",  # had_sauna
        "n",  # had_outdoor_bath
        "n",  # had_rest_area
        "n",  # had_food_service
        "n",  # massage_chair_available
        "moderate",  # crowd_level
        "relaxed",  # pre_visit_mood
        "relaxed",  # post_visit_mood
        "1",  # energy_level_change
        "7",  # hydration_level
        "n",  # multi_onsen_day
        "8",  # personal_rating
        "",  # heart_rate_data
        "y",  # confirm
    ]


def get_invalid_rating_retry_inputs() -> List[str]:
    """
    Get user inputs that include an invalid rating followed by a valid one.

    This simulates a user who:
    - First enters an invalid rating (15)
    - Then enters a valid rating (8)
    - Completes the rest of the flow normally
    """
    return [
        "1",  # onsen_id
        "500",  # entry_fee_yen
        "cash",  # payment_method
        "",  # visit_time
        "sunny",  # weather
        "afternoon",  # time_of_day
        "25.0",  # temperature_outside_celsius
        "60",  # stay_length_minutes
        "alone",  # visited_with
        "car",  # travel_mode
        "15",  # travel_time_minutes
        "n",  # exercise_before_onsen
        "15",  # accessibility_rating (invalid - should be 1-10)
        "8",  # accessibility_rating (valid retry)
        "9",  # cleanliness_rating
        "7",  # navigability_rating
        "8",  # view_rating
        "9",  # atmosphere_rating
        "open air",  # main_bath_type
        "42.0",  # main_bath_temperature
        "sulfur",  # main_bath_water_type
        "clear",  # water_color
        "6",  # smell_intensity_rating
        "8",  # changing_room_cleanliness_rating
        "7",  # locker_availability_rating
        "y",  # had_soap
        "n",  # had_sauna
        "n",  # had_outdoor_bath
        "n",  # had_rest_area
        "n",  # had_food_service
        "n",  # massage_chair_available
        "moderate",  # crowd_level
        "relaxed",  # pre_visit_mood
        "relaxed",  # post_visit_mood
        "1",  # energy_level_change
        "7",  # hydration_level
        "n",  # multi_onsen_day
        "8",  # personal_rating
        "",  # heart_rate_data
        "y",  # confirm
    ]


def get_cancellation_inputs() -> List[str]:
    """
    Get user inputs that end with cancellation.

    This simulates a user who:
    - Goes through the entire questionnaire
    - But cancels at the final confirmation step
    """
    return [
        "1",  # onsen_id
        "500",  # entry_fee_yen
        "cash",  # payment_method
        "",  # visit_time
        "sunny",  # weather
        "afternoon",  # time_of_day
        "25.0",  # temperature_outside_celsius
        "60",  # stay_length_minutes
        "alone",  # visited_with
        "car",  # travel_mode
        "15",  # travel_time_minutes
        "n",  # exercise_before_onsen
        "8",  # accessibility_rating
        "9",  # cleanliness_rating
        "7",  # navigability_rating
        "8",  # view_rating
        "9",  # atmosphere_rating
        "open air",  # main_bath_type
        "42.0",  # main_bath_temperature
        "sulfur",  # main_bath_water_type
        "clear",  # water_color
        "6",  # smell_intensity_rating
        "8",  # changing_room_cleanliness_rating
        "7",  # locker_availability_rating
        "y",  # had_soap
        "n",  # had_sauna
        "n",  # had_outdoor_bath
        "n",  # had_rest_area
        "n",  # had_food_service
        "n",  # massage_chair_available
        "moderate",  # crowd_level
        "relaxed",  # pre_visit_mood
        "relaxed",  # post_visit_mood
        "1",  # energy_level_change
        "7",  # hydration_level
        "n",  # multi_onsen_day
        "8",  # personal_rating
        "",  # heart_rate_data
        "n",  # confirm (cancel)
    ]


def get_multi_onsen_day_inputs() -> List[str]:
    """
    Get user inputs for a multi-onsen day scenario.

    This simulates a user who:
    - Visits multiple onsens in one day
    - This is the second visit of the day
    """
    return [
        "2",  # onsen_id (different onsen)
        "400",  # entry_fee_yen
        "card",  # payment_method
        "",  # visit_time
        "partly cloudy",  # weather
        "afternoon",  # time_of_day
        "22.0",  # temperature_outside_celsius
        "45",  # stay_length_minutes
        "group",  # visited_with
        "bus",  # travel_mode
        "25",  # travel_time_minutes
        "n",  # exercise_before_onsen
        "7",  # accessibility_rating
        "8",  # cleanliness_rating
        "6",  # navigability_rating
        "7",  # view_rating
        "8",  # atmosphere_rating
        "open air",  # main_bath_type
        "41.0",  # main_bath_temperature
        "salt",  # main_bath_water_type
        "brown",  # water_color
        "5",  # smell_intensity_rating
        "7",  # changing_room_cleanliness_rating
        "6",  # locker_availability_rating
        "y",  # had_soap
        "y",  # had_sauna
        "n",  # sauna_visited (didn't use it this time)
        "n",  # had_outdoor_bath
        "y",  # had_rest_area
        "7",  # rest_area_rating
        "y",  # had_food_service
        "8",  # food_quality_rating
        "y",  # massage_chair_available
        "busy",  # crowd_level
        "relaxed",  # pre_visit_mood
        "very relaxed",  # post_visit_mood
        "2",  # energy_level_change
        "8",  # hydration_level
        "y",  # multi_onsen_day
        "2",  # visit_order
        "8",  # personal_rating
        "",  # heart_rate_data
        "y",  # confirm
    ]
