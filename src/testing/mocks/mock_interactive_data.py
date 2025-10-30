"""
Mock data for interactive CLI tests.

This module provides predefined user input sequences for testing the interactive
add-visit functionality. Each function returns a list of strings that simulate
user responses to the interactive questionnaire.
"""

from faker import Faker

fake = Faker()


def get_complete_flow_inputs() -> list[str]:
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
        "",  # visit_time (use current time)
        "500",  # entry_fee_yen
        "60",  # stay_length_minutes
        "15",  # travel_time_minutes
        "8",  # accessibility_rating
        "9",  # cleanliness_rating
        "7",  # navigability_rating
        "8",  # view_rating
        "6",  # smell_intensity_rating
        "8",  # changing_room_cleanliness_rating
        "7",  # locker_availability_rating
        "8",  # rest_area_rating
        "",  # food_quality_rating (skip)
        "",  # sauna_rating (skip)
        "",  # outdoor_bath_rating (skip)
        "2",  # energy_level_change
        "7",  # hydration_level
        "9",  # atmosphere_rating
        "9",  # personal_rating
        "42.0",  # main_bath_temperature
        "",  # sauna_temperature (skip)
        "",  # outdoor_bath_temperature (skip)
        "25.5",  # outside_temperature
        "cash",  # payment_method
        "sunny",  # weather
        "afternoon",  # time_of_day
        "alone",  # visited_with
        "car",  # travel_mode
        "moderate",  # crowd_level
        "open air",  # main_bath_type
        "clear",  # water_color
        "relaxed",  # pre_visit_mood
        "very relaxed",  # post_visit_mood
        "y",  # had_soap
        "y",  # had_sauna
        "y",  # had_outdoor_bath
        "y",  # had_rest_area
        "y",  # rest_area_used
        "y",  # had_food_service
        "n",  # food_service_used
        "n",  # massage_chair_available
        "y",  # sauna_visited
        "y",  # sauna_steam
        "y",  # outdoor_bath_visited
        "n",  # multi_onsen_day
        "15",  # sauna_duration_minutes
        "",  # previous_location (skip)
        "",  # next_location (skip)
        "",  # visit_order (skip)
    ]


def get_exercise_flow_inputs() -> list[str]:
    """
    Get user inputs for a flow where the user exercised before the onsen.

    This simulates a user who:
    - Exercised before visiting (running for 30 minutes)
    - Has a simpler onsen experience (no sauna, outdoor bath, etc.)
    - Uses different travel mode and companions
    """
    return [
        "1",  # onsen_id
        "",  # visit_time
        "300",  # entry_fee_yen
        "45",  # stay_length_minutes
        "10",  # travel_time_minutes
        "7",  # accessibility_rating
        "8",  # cleanliness_rating
        "6",  # navigability_rating
        "7",  # view_rating
        "5",  # smell_intensity_rating
        "7",  # changing_room_cleanliness_rating
        "6",  # locker_availability_rating
        "",  # rest_area_rating (skip)
        "",  # food_quality_rating (skip)
        "",  # sauna_rating (skip)
        "",  # outdoor_bath_rating (skip)
        "3",  # energy_level_change
        "6",  # hydration_level
        "8",  # atmosphere_rating
        "8",  # personal_rating
        "40.0",  # main_bath_temperature
        "",  # sauna_temperature (skip)
        "",  # outdoor_bath_temperature (skip)
        "20.0",  # outside_temperature
        "card",  # payment_method
        "cloudy",  # weather
        "morning",  # time_of_day
        "friend",  # visited_with
        "walk",  # travel_mode
        "quiet",  # crowd_level
        "indoor",  # main_bath_type
        "brown",  # water_color
        "stressed",  # pre_visit_mood
        "relaxed",  # post_visit_mood
        "n",  # had_soap
        "n",  # had_sauna
        "n",  # had_outdoor_bath
        "n",  # had_rest_area
        "n",  # had_food_service
        "n",  # massage_chair_available
        "n",  # sauna_visited
        "n",  # sauna_steam
        "n",  # outdoor_bath_visited
        "n",  # multi_onsen_day
        "",  # sauna_duration_minutes (skip)
        "",  # previous_location (skip)
        "",  # next_location (skip)
        "",  # visit_order (skip)
    ]


def get_minimal_flow_inputs() -> list[str]:
    """
    Get user inputs for a minimal flow with basic information only.

    This simulates a user who:
    - Provides only essential information
    - Skips most optional features
    - Has a simple onsen experience
    """
    return [
        "1",  # onsen_id
        "",  # visit_time
        "200",  # entry_fee_yen
        "30",  # stay_length_minutes
        "20",  # travel_time_minutes
        "6",  # accessibility_rating
        "7",  # cleanliness_rating
        "5",  # navigability_rating
        "6",  # view_rating
        "4",  # smell_intensity_rating
        "6",  # changing_room_cleanliness_rating
        "5",  # locker_availability_rating
        "",  # rest_area_rating (skip)
        "",  # food_quality_rating (skip)
        "",  # sauna_rating (skip)
        "",  # outdoor_bath_rating (skip)
        "1",  # energy_level_change
        "5",  # hydration_level
        "7",  # atmosphere_rating
        "7",  # personal_rating
        "38.0",  # main_bath_temperature
        "",  # sauna_temperature (skip)
        "",  # outdoor_bath_temperature (skip)
        "18.0",  # outside_temperature
        "cash",  # payment_method
        "clear",  # weather
        "evening",  # time_of_day
        "alone",  # visited_with
        "train",  # travel_mode
        "quiet",  # crowd_level
        "indoor",  # main_bath_type
        "clear",  # water_color
        "tired",  # pre_visit_mood
        "relaxed",  # post_visit_mood
        "y",  # had_soap
        "n",  # had_sauna
        "n",  # had_outdoor_bath
        "n",  # had_rest_area
        "n",  # rest_area_used
        "n",  # had_food_service
        "n",  # food_service_used
        "n",  # massage_chair_available
        "n",  # sauna_visited
        "n",  # sauna_steam
        "n",  # outdoor_bath_visited
        "n",  # multi_onsen_day
        "",  # sauna_duration_minutes (skip)
        "",  # previous_location (skip)
        "",  # next_location (skip)
        "",  # visit_order (skip)
    ]


def get_invalid_onsen_retry_inputs() -> list[str]:
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
        "",  # visit_time
        "500",  # entry_fee_yen
        "60",  # stay_length_minutes
        "15",  # travel_time_minutes
        "8",  # accessibility_rating
        "9",  # cleanliness_rating
        "7",  # navigability_rating
        "8",  # view_rating
        "6",  # smell_intensity_rating
        "8",  # changing_room_cleanliness_rating
        "7",  # locker_availability_rating
        "",  # rest_area_rating (skip)
        "",  # food_quality_rating (skip)
        "",  # sauna_rating (skip)
        "",  # outdoor_bath_rating (skip)
        "1",  # energy_level_change
        "7",  # hydration_level
        "9",  # atmosphere_rating
        "8",  # personal_rating
        "42.0",  # main_bath_temperature
        "",  # sauna_temperature (skip)
        "",  # outdoor_bath_temperature (skip)
        "25.0",  # outside_temperature
        "cash",  # payment_method
        "sunny",  # weather
        "afternoon",  # time_of_day
        "alone",  # visited_with
        "car",  # travel_mode
        "",  # exercise_type (skip)
        "moderate",  # crowd_level
        "open air",  # main_bath_type
        "clear",  # water_color
        "relaxed",  # pre_visit_mood
        "relaxed",  # post_visit_mood
        "y",  # had_soap
        "n",  # had_sauna
        "n",  # had_outdoor_bath
        "n",  # had_rest_area
        "n",  # rest_area_used
        "n",  # had_food_service
        "n",  # food_service_used
        "n",  # massage_chair_available
        "n",  # sauna_visited
        "n",  # sauna_steam
        "n",  # outdoor_bath_visited
        "n",  # multi_onsen_day
        "",  # sauna_duration_minutes (skip)
        "",  # previous_location (skip)
        "",  # next_location (skip)
        "",  # visit_order (skip)
    ]


def get_invalid_rating_retry_inputs() -> list[str]:
    """
    Get user inputs that include an invalid rating followed by a valid one.

    This simulates a user who:
    - First enters an invalid rating (15)
    - Then enters a valid rating (8)
    - Completes the rest of the flow normally
    """
    return [
        "1",  # onsen_id
        "",  # visit_time
        "500",  # entry_fee_yen
        "60",  # stay_length_minutes
        "15",  # travel_time_minutes
        "15",  # accessibility_rating (invalid - should be 1-10)
        "8",  # accessibility_rating (valid retry)
        "9",  # cleanliness_rating
        "7",  # navigability_rating
        "8",  # view_rating
        "6",  # smell_intensity_rating
        "8",  # changing_room_cleanliness_rating
        "7",  # locker_availability_rating
        "",  # rest_area_rating (skip)
        "",  # food_quality_rating (skip)
        "",  # sauna_rating (skip)
        "",  # outdoor_bath_rating (skip)
        "1",  # energy_level_change
        "7",  # hydration_level
        "9",  # atmosphere_rating
        "8",  # personal_rating
        "42.0",  # main_bath_temperature
        "",  # sauna_temperature (skip)
        "",  # outdoor_bath_temperature (skip)
        "25.0",  # outside_temperature
        "cash",  # payment_method
        "sunny",  # weather
        "afternoon",  # time_of_day
        "alone",  # visited_with
        "car",  # travel_mode
        "",  # exercise_type (skip)
        "moderate",  # crowd_level
        "open air",  # main_bath_type
        "clear",  # water_color
        "relaxed",  # pre_visit_mood
        "relaxed",  # post_visit_mood
        "y",  # had_soap
        "n",  # had_sauna
        "n",  # had_outdoor_bath
        "n",  # had_rest_area
        "n",  # rest_area_used
        "n",  # had_food_service
        "n",  # food_service_used
        "n",  # massage_chair_available
        "n",  # sauna_visited
        "n",  # sauna_steam
        "n",  # outdoor_bath_visited
        "n",  # multi_onsen_day
        "",  # sauna_duration_minutes (skip)
        "",  # previous_location (skip)
        "",  # next_location (skip)
        "",  # visit_order (skip)
    ]


def get_multi_onsen_day_inputs() -> list[str]:
    """
    Get user inputs for a multi-onsen day scenario.

    This simulates a user who:
    - Visits multiple onsens in one day
    - This is the second visit of the day
    """
    return [
        "2",  # onsen_id (different onsen)
        "",  # visit_time
        "400",  # entry_fee_yen
        "45",  # stay_length_minutes
        "25",  # travel_time_minutes
        "7",  # accessibility_rating
        "8",  # cleanliness_rating
        "6",  # navigability_rating
        "7",  # view_rating
        "5",  # smell_intensity_rating
        "7",  # changing_room_cleanliness_rating
        "6",  # locker_availability_rating
        "7",  # rest_area_rating
        "8",  # food_quality_rating
        "",  # sauna_rating (skip)
        "",  # outdoor_bath_rating (skip)
        "2",  # energy_level_change
        "8",  # hydration_level
        "8",  # atmosphere_rating
        "8",  # personal_rating
        "41.0",  # main_bath_temperature
        "",  # sauna_temperature (skip)
        "",  # outdoor_bath_temperature (skip)
        "22.0",  # outside_temperature
        "card",  # payment_method
        "partly cloudy",  # weather
        "afternoon",  # time_of_day
        "group",  # visited_with
        "bus",  # travel_mode
        "",  # exercise_type (skip)
        "busy",  # crowd_level
        "open air",  # main_bath_type
        "brown",  # water_color
        "relaxed",  # pre_visit_mood
        "very relaxed",  # post_visit_mood
        "n",  # exercise_before_onsen
        "y",  # had_soap
        "y",  # had_sauna
        "n",  # had_outdoor_bath
        "y",  # had_rest_area
        "y",  # rest_area_used
        "y",  # had_food_service
        "y",  # food_service_used
        "y",  # massage_chair_available
        "n",  # sauna_visited (didn't use it this time)
        "n",  # sauna_steam
        "n",  # outdoor_bath_visited
        "y",  # multi_onsen_day
        "",  # sauna_duration_minutes (skip)
        "",  # previous_location (skip)
        "",  # next_location (skip)
        "2",  # visit_order
    ]
