"""
functions.py

Functions for the CLI commands.
"""

import argparse
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from loguru import logger
from src.db.conn import get_db
from src.db.models import Onsen, OnsenVisit
from src.const import CONST


def add_onsen(args: argparse.Namespace) -> None:
    """
    Add a new onsen to the database.
    """
    with get_db(url=CONST.DATABASE_URL) as db:
        args_dict = vars(args)
        args_dict.pop("func", None)

        onsen = Onsen(**args_dict)
        db.add(onsen)
        db.commit()
        logger.info(f"Added onsen {onsen.name}")


def add_visit(args: argparse.Namespace) -> None:
    """
    Add a new onsen visit to the database.
    """
    # Check if interactive mode is requested
    if hasattr(args, "interactive") and args.interactive:
        interactive_add_visit()
        return

    with get_db(url=CONST.DATABASE_URL) as db:
        if not hasattr(args, "onsen_id") or args.onsen_id is None:
            logger.error("onsen_id is required!")
            return

        onsen = db.query(Onsen).filter(Onsen.id == args.onsen_id).first()
        if not onsen:
            logger.error(f"No onsen with id={args.onsen_id} found!")
            return

        args_dict = vars(args)
        args_dict.pop("onsen_id", None)
        args_dict.pop("func", None)  # Not a model field
        args_dict.pop("interactive", None)  # Not a model field

        # Create the visit with dynamic arguments
        visit = OnsenVisit(onsen_id=onsen.id, **args_dict)
        db.add(visit)
        db.commit()
        logger.info(f"Added a visit to onsen {onsen.name} (id={onsen.id})")


def interactive_add_visit() -> None:
    """
    Interactive version of add_visit that guides users through a series of questions.
    """
    print("🌊 Welcome to the Interactive Onsen Visit Recorder! 🌊")
    print("I'll guide you through recording your onsen visit experience.\n")

    # Initialize data dictionary
    visit_data: Dict[str, Any] = {}

    # Helper function for input validation
    def get_valid_input(prompt: str, validator: callable, max_attempts: int = 3) -> Any:
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

    # 2. Basic visit information
    print("\nStep 2: Basic visit information")

    # Entry fee
    entry_fee = get_valid_input(
        "What was the entry fee in yen? (0 if free): ", validate_integer
    )
    visit_data["entry_fee_yen"] = int(entry_fee) if entry_fee else 0

    # Payment method
    payment_method = input("Payment method (cash/card/etc.): ").strip()
    visit_data["payment_method"] = payment_method if payment_method else ""

    # Visit time
    visit_time = get_valid_input(
        "Visit time (YYYY-MM-DD HH:MM, or press Enter for now): ",
        lambda x: x == "" or validate_datetime(x),
    )
    if visit_time:
        visit_data["visit_time"] = visit_time
    else:
        visit_data["visit_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Weather
    weather = input("Weather conditions: ").strip()
    visit_data["weather"] = weather if weather else ""

    # Time of day
    time_of_day = input("Time of day (morning/afternoon/evening): ").strip()
    visit_data["time_of_day"] = time_of_day if time_of_day else ""

    # Temperature outside
    temp_outside = get_valid_input("Temperature outside in Celsius: ", validate_float)
    visit_data["temperature_outside_celsius"] = (
        float(temp_outside) if temp_outside else 0.0
    )

    # Stay length
    stay_length = get_valid_input("How long did you stay (minutes): ", validate_integer)
    visit_data["stay_length_minutes"] = int(stay_length) if stay_length else 0

    # 3. Travel information
    print("\nStep 3: Travel information")

    visited_with = input("Who did you visit with (alone/friend/group): ").strip()
    visit_data["visited_with"] = visited_with if visited_with else ""

    travel_mode = input("Travel mode (car/train/bus/walk/run/bike): ").strip()
    visit_data["travel_mode"] = travel_mode if travel_mode else ""

    travel_time = get_valid_input("Travel time in minutes: ", validate_integer)
    visit_data["travel_time_minutes"] = int(travel_time) if travel_time else 0

    # 4. Exercise information
    print("\nStep 4: Exercise information")

    exercise_before = get_valid_input(
        "Did you exercise before the onsen? (y/n): ", validate_yes_no
    )
    visit_data["excercise_before_onsen"] = exercise_before.lower() in ["y", "yes"]

    if visit_data["excercise_before_onsen"]:
        exercise_type = input("Exercise type (running/walking/cycling/other): ").strip()
        visit_data["excercise_type"] = exercise_type if exercise_type else ""

        exercise_length = get_valid_input(
            "Exercise duration in minutes: ", validate_integer
        )
        visit_data["excercise_length_minutes"] = (
            int(exercise_length) if exercise_length else 0
        )

    # 5. Facility ratings
    print("\nStep 5: Facility ratings (1-10 scale)")

    accessibility = get_valid_input("Accessibility rating (1-10): ", validate_rating)
    visit_data["accessibility_rating"] = int(accessibility) if accessibility else 0

    cleanliness = get_valid_input("Cleanliness rating (1-10): ", validate_rating)
    visit_data["cleanliness_rating"] = int(cleanliness) if cleanliness else 0

    navigability = get_valid_input("Navigability rating (1-10): ", validate_rating)
    visit_data["navigability_rating"] = int(navigability) if navigability else 0

    view_rating = get_valid_input("View rating (1-10): ", validate_rating)
    visit_data["view_rating"] = int(view_rating) if view_rating else 0

    atmosphere = get_valid_input("Atmosphere rating (1-10): ", validate_rating)
    visit_data["atmosphere_rating"] = int(atmosphere) if atmosphere else 0

    # 6. Main bath information
    print("\nStep 6: Main bath information")

    main_bath_type = input("Main bath type (open air/indoor/other): ").strip()
    visit_data["main_bath_type"] = main_bath_type if main_bath_type else ""

    main_bath_temp = get_valid_input(
        "Main bath temperature in Celsius: ", validate_float
    )
    visit_data["main_bath_temperature"] = (
        float(main_bath_temp) if main_bath_temp else 0.0
    )

    main_bath_water = input("Main bath water type (sulfur/salt/other): ").strip()
    visit_data["main_bath_water_type"] = main_bath_water if main_bath_water else ""

    water_color = input("Water color (clear/brown/green/other): ").strip()
    visit_data["water_color"] = water_color if water_color else ""

    smell_intensity = get_valid_input(
        "Smell intensity rating (1-10): ", validate_rating
    )
    visit_data["smell_intensity_rating"] = (
        int(smell_intensity) if smell_intensity else 0
    )

    # 7. Changing room and facilities
    print("\nStep 7: Changing room and facilities")

    changing_cleanliness = get_valid_input(
        "Changing room cleanliness rating (1-10): ", validate_rating
    )
    visit_data["changing_room_cleanliness_rating"] = (
        int(changing_cleanliness) if changing_cleanliness else 0
    )

    locker_availability = get_valid_input(
        "Locker availability rating (1-10): ", validate_rating
    )
    visit_data["locker_availability_rating"] = (
        int(locker_availability) if locker_availability else 0
    )

    had_soap = get_valid_input("Was soap available? (y/n): ", validate_yes_no)
    visit_data["had_soap"] = had_soap.lower() in ["y", "yes"]

    # 8. Sauna information
    print("\nStep 8: Sauna information")

    had_sauna = get_valid_input(
        "Was there a sauna at the facility? (y/n): ", validate_yes_no
    )
    visit_data["had_sauna"] = had_sauna.lower() in ["y", "yes"]

    if visit_data["had_sauna"]:
        sauna_visited = get_valid_input(
            "Did you use the sauna? (y/n): ", validate_yes_no
        )
        visit_data["sauna_visited"] = sauna_visited.lower() in ["y", "yes"]

        if visit_data["sauna_visited"]:
            sauna_temp = get_valid_input(
                "Sauna temperature in Celsius: ", validate_float
            )
            visit_data["sauna_temperature"] = float(sauna_temp) if sauna_temp else 0.0

            sauna_steam = get_valid_input(
                "Did the sauna have steam? (y/n): ", validate_yes_no
            )
            visit_data["sauna_steam"] = sauna_steam.lower() in ["y", "yes"]

            sauna_duration = get_valid_input(
                "How long did you stay in the sauna (minutes): ", validate_integer
            )
            visit_data["sauna_duration_minutes"] = (
                int(sauna_duration) if sauna_duration else 0
            )

            sauna_rating = get_valid_input("Sauna rating (1-10): ", validate_rating)
            visit_data["sauna_rating"] = int(sauna_rating) if sauna_rating else 0

    # 9. Outdoor bath information
    print("\nStep 9: Outdoor bath information")

    had_outdoor_bath = get_valid_input(
        "Was there an outdoor bath at the facility? (y/n): ", validate_yes_no
    )
    visit_data["had_outdoor_bath"] = had_outdoor_bath.lower() in ["y", "yes"]

    if visit_data["had_outdoor_bath"]:
        outdoor_bath_visited = get_valid_input(
            "Did you use the outdoor bath? (y/n): ", validate_yes_no
        )
        visit_data["outdoor_bath_visited"] = outdoor_bath_visited.lower() in [
            "y",
            "yes",
        ]

        if visit_data["outdoor_bath_visited"]:
            outdoor_bath_temp = get_valid_input(
                "Outdoor bath temperature in Celsius: ", validate_float
            )
            visit_data["outdoor_bath_temperature"] = (
                float(outdoor_bath_temp) if outdoor_bath_temp else 0.0
            )

            outdoor_bath_rating = get_valid_input(
                "Outdoor bath rating (1-10): ", validate_rating
            )
            visit_data["outdoor_bath_rating"] = (
                int(outdoor_bath_rating) if outdoor_bath_rating else 0
            )

    # 10. Rest area and food
    print("\nStep 10: Rest area and food")

    had_rest_area = get_valid_input("Was there a rest area? (y/n): ", validate_yes_no)
    visit_data["had_rest_area"] = had_rest_area.lower() in ["y", "yes"]

    if visit_data["had_rest_area"]:
        rest_area_rating = get_valid_input("Rest area rating (1-10): ", validate_rating)
        visit_data["rest_area_rating"] = (
            int(rest_area_rating) if rest_area_rating else 0
        )

    had_food_service = get_valid_input(
        "Was there food service? (y/n): ", validate_yes_no
    )
    visit_data["had_food_service"] = had_food_service.lower() in ["y", "yes"]

    if visit_data["had_food_service"]:
        food_quality = get_valid_input("Food quality rating (1-10): ", validate_rating)
        visit_data["food_quality_rating"] = int(food_quality) if food_quality else 0

    massage_chair = get_valid_input(
        "Were massage chairs available? (y/n): ", validate_yes_no
    )
    visit_data["massage_chair_available"] = massage_chair.lower() in ["y", "yes"]

    # 11. Crowd and mood
    print("\nStep 11: Crowd and mood")

    crowd_level = input("Crowd level (busy/moderate/quiet/empty): ").strip()
    visit_data["crowd_level"] = crowd_level if crowd_level else ""

    pre_visit_mood = input(
        "Mood before visit (relaxed/stressed/anxious/other): "
    ).strip()
    visit_data["pre_visit_mood"] = pre_visit_mood if pre_visit_mood else ""

    post_visit_mood = input(
        "Mood after visit (relaxed/stressed/anxious/other): "
    ).strip()
    visit_data["post_visit_mood"] = post_visit_mood if post_visit_mood else ""

    # 12. Health and energy
    print("\nStep 12: Health and energy")

    energy_change = get_valid_input(
        "Energy level change (-5 to +5, negative = less energy): ",
        lambda x: validate_integer(x) and -5 <= int(x) <= 5,
    )
    visit_data["energy_level_change"] = int(energy_change) if energy_change else 0

    hydration = get_valid_input(
        "Hydration level before entering (1-10): ", validate_rating
    )
    visit_data["hydration_level"] = int(hydration) if hydration else 0

    # 13. Multi-onsen day
    print("\nStep 13: Multi-onsen day")

    multi_onsen = get_valid_input(
        "Was this part of a multi-onsen day? (y/n): ", validate_yes_no
    )
    visit_data["multi_onsen_day"] = multi_onsen.lower() in ["y", "yes"]

    if visit_data["multi_onsen_day"]:
        visit_order = get_valid_input(
            "Visit order (1st, 2nd, etc.): ", validate_integer
        )
        visit_data["visit_order"] = int(visit_order) if visit_order else 0

    # 14. Personal rating
    print("\nStep 14: Personal rating")

    personal_rating = get_valid_input(
        "Personal overall rating (1-10): ", validate_rating
    )
    visit_data["personal_rating"] = int(personal_rating) if personal_rating else 0

    # 15. Additional information
    print("\nStep 15: Additional information")

    heart_rate_data = input("Heart rate data (optional): ").strip()
    visit_data["heart_rate_data"] = heart_rate_data if heart_rate_data else ""

    # Set defaults for fields that weren't explicitly set
    defaults = {
        "previous_location": 0,
        "next_location": 0,
    }

    for key, default_value in defaults.items():
        if key not in visit_data:
            visit_data[key] = default_value

    # Build the command
    print("\n" + "=" * 50)
    print("SUMMARY OF YOUR VISIT")
    print("=" * 50)

    # Show key information
    with get_db(url=CONST.DATABASE_URL) as db:
        onsen = db.query(Onsen).filter(Onsen.id == visit_data["onsen_id"]).first()
        print(f"Onsen: {onsen.name} (ID: {onsen.id})")

    print(f"Entry fee: {visit_data['entry_fee_yen']} yen")
    print(f"Stay length: {visit_data['stay_length_minutes']} minutes")
    print(f"Personal rating: {visit_data['personal_rating']}/10")

    # Ask for confirmation
    confirm = get_valid_input(
        "\nProceed with adding this visit? (y/n): ", validate_yes_no
    )

    if confirm.lower() in ["y", "yes"]:
        # Build command arguments
        cmd_args = ["onsendo", "add-visit"]

        for key, value in visit_data.items():
            if isinstance(value, bool):
                if value:
                    cmd_args.append(f"--{key}")
            elif value is not None and value != "":
                cmd_args.append(f"--{key}")
                cmd_args.append(str(value))

        print(f"\nExecuting command: {' '.join(cmd_args)}")

        try:
            # Execute the command
            result = subprocess.run(
                cmd_args, capture_output=True, text=True, check=True
            )
            print("✅ Visit successfully added!")
            if result.stdout:
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error adding visit: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
            sys.exit(1)
    else:
        print("Visit recording cancelled.")
        sys.exit(0)
