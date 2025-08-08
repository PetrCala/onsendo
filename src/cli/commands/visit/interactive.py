"""
Interactive visit commands.
"""

import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict
from src.db.conn import get_db
from src.db.models import Onsen, OnsenVisit
from src.const import CONST


def add_visit_interactive() -> None:
    """
    Interactive version of add_visit that guides users through a series of questions.
    """
    print("🌊 Welcome to the Interactive Onsen Visit Recorder! 🌊")
    print("I'll guide you through recording your onsen visit experience.\n")

    # Initialize data dictionary
    visit_data: Dict[str, Any] = {}

    # Helper function for input validation
    def get_valid_input(prompt: str, validator: Callable, max_attempts: int = 3) -> Any:
        """Get valid input from user with retry logic."""
        for attempt in range(max_attempts):
            try:
                user_input = input(prompt).strip()
                if validator(user_input):
                    return user_input
                print("Invalid input. Please try again.")
            except (ValueError, KeyboardInterrupt):
                if attempt == max_attempts - 1:
                    print("\nToo many invalid attempts. Exiting.")
                    sys.exit(1)
                print("Invalid input. Please try again.")
        return None

    def validate_onsen_id(input_str: str) -> bool:
        """Validate onsen ID input."""
        try:
            onsen_id = int(input_str)
            # Check if onsen exists
            with get_db(url=CONST.DATABASE_URL) as db:
                onsen = db.query(Onsen).filter(Onsen.id == onsen_id).first()
                if not onsen:
                    print(f"No onsen found with ID {onsen_id}")
                    return False
                print(f"Found onsen: {onsen.name}")
                return True
        except ValueError:
            return False

    def validate_yes_no(input_str: str) -> bool:
        """Validate yes/no input."""
        return input_str.lower() in ["y", "yes", "n", "no"]

    def validate_rating(input_str: str) -> bool:
        """Validate rating input (1-10)."""
        try:
            rating = int(input_str)
            return 1 <= rating <= 10
        except ValueError:
            return False

    def validate_integer(input_str: str) -> bool:
        """Validate integer input."""
        try:
            int(input_str)
            return True
        except ValueError:
            return False

    def validate_float(input_str: str) -> bool:
        """Validate float input."""
        try:
            float(input_str)
            return True
        except ValueError:
            return False

    def validate_datetime(input_str: str) -> bool:
        """Validate datetime input (YYYY-MM-DD HH:MM)."""
        try:
            datetime.strptime(input_str, "%Y-%m-%d %H:%M")
            return True
        except ValueError:
            return False

    # 1. Get onsen ID
    print("Step 1: Select the onsen")
    onsen_id_input = get_valid_input(
        "Enter the onsen ID: ", validate_onsen_id, max_attempts=3
    )
    if onsen_id_input is None:
        sys.exit(1)
    visit_data["onsen_id"] = int(onsen_id_input)

    # 2. Get visit time
    print("\nStep 2: Visit time")
    while True:
        time_input = input(
            "Enter visit time (YYYY-MM-DD HH:MM) or press Enter for now: "
        ).strip()
        if not time_input:
            visit_data["visit_time"] = datetime.now()
            break
        if validate_datetime(time_input):
            visit_data["visit_time"] = datetime.strptime(time_input, "%Y-%m-%d %H:%M")
            break
        print("Invalid datetime format. Please use YYYY-MM-DD HH:MM")

    # 3. Basic information
    print("\nStep 3: Basic information")

    # Entry fee
    fee_input = get_valid_input("Entry fee (yen): ", validate_integer)
    if fee_input:
        visit_data["entry_fee_yen"] = int(fee_input)

    # Stay length
    stay_input = get_valid_input("Stay length (minutes): ", validate_integer)
    if stay_input:
        visit_data["stay_length_minutes"] = int(stay_input)

    # Travel time
    travel_input = get_valid_input("Travel time (minutes): ", validate_integer)
    if travel_input:
        visit_data["travel_time_minutes"] = int(travel_input)

    # 4. Ratings
    print("\nStep 4: Ratings (1-10, press Enter to skip)")

    ratings = [
        "accessibility_rating",
        "cleanliness_rating",
        "navigability_rating",
        "view_rating",
        "smell_intensity_rating",
        "changing_room_cleanliness_rating",
        "locker_availability_rating",
        "rest_area_rating",
        "food_quality_rating",
        "sauna_rating",
        "outdoor_bath_rating",
        "energy_level_change",
        "hydration_level",
        "atmosphere_rating",
        "personal_rating",
    ]

    for rating in ratings:
        rating_input = get_valid_input(
            f"{rating.replace('_', ' ').title()}: ",
            lambda x: not x or validate_rating(x),
        )
        if rating_input:
            visit_data[rating] = int(rating_input)

    # 5. Temperatures
    print("\nStep 5: Temperatures (press Enter to skip)")

    temp_input = get_valid_input(
        "Main bath temperature (°C): ", lambda x: not x or validate_float(x)
    )
    if temp_input:
        visit_data["main_bath_temperature"] = float(temp_input)

    sauna_temp_input = get_valid_input(
        "Sauna temperature (°C): ", lambda x: not x or validate_float(x)
    )
    if sauna_temp_input:
        visit_data["sauna_temperature"] = float(sauna_temp_input)

    outdoor_temp_input = get_valid_input(
        "Outdoor bath temperature (°C): ", lambda x: not x or validate_float(x)
    )
    if outdoor_temp_input:
        visit_data["outdoor_bath_temperature"] = float(outdoor_temp_input)

    outside_temp_input = get_valid_input(
        "Outside temperature (°C): ", lambda x: not x or validate_float(x)
    )
    if outside_temp_input:
        visit_data["temperature_outside_celsius"] = float(outside_temp_input)

    # 6. Text fields
    print("\nStep 6: Additional information (press Enter to skip)")

    text_fields = [
        "payment_method",
        "weather",
        "time_of_day",
        "visited_with",
        "travel_mode",
        "excercise_type",
        "crowd_level",
        "heart_rate_data",
        "main_bath_type",
        "main_bath_water_type",
        "water_color",
        "pre_visit_mood",
        "post_visit_mood",
    ]

    for field in text_fields:
        value = input(f"{field.replace('_', ' ').title()}: ").strip()
        if value:
            visit_data[field] = value

    # 7. Boolean fields
    print("\nStep 7: Yes/No questions")

    boolean_fields = [
        "excercise_before_onsen",
        "had_soap",
        "had_sauna",
        "had_outdoor_bath",
        "had_rest_area",
        "had_food_service",
        "massage_chair_available",
        "sauna_visited",
        "sauna_steam",
        "outdoor_bath_visited",
        "multi_onsen_day",
    ]

    for field in boolean_fields:
        while True:
            response = (
                input(f"{field.replace('_', ' ').title()}? (y/n): ").strip().lower()
            )
            if response in ["y", "yes"]:
                visit_data[field] = True
                break
            elif response in ["n", "no"]:
                visit_data[field] = False
                break
            else:
                print("Please enter 'y' or 'n'")

    # 8. Additional integer fields
    print("\nStep 8: Additional details (press Enter to skip)")

    int_fields = [
        "excercise_length_minutes",
        "sauna_duration_minutes",
        "previous_location",
        "next_location",
        "visit_order",
    ]

    for field in int_fields:
        value = get_valid_input(
            f"{field.replace('_', ' ').title()}: ",
            lambda x: not x or validate_integer(x),
        )
        if value:
            visit_data[field] = int(value)

    # Save the visit
    print("\nSaving visit data...")
    with get_db(url=CONST.DATABASE_URL) as db:
        onsen = db.query(Onsen).filter(Onsen.id == visit_data["onsen_id"]).first()
        visit = OnsenVisit(**visit_data)
        db.add(visit)
        db.commit()

        print(f"✅ Successfully recorded visit to {onsen.name}!")
        print(f"Visit ID: {visit.id}")
        print(f"Visit time: {visit.visit_time}")
        print(f"Personal rating: {visit.personal_rating}/10")
