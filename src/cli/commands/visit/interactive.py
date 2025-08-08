"""
Interactive visit commands.
"""

import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional
from src.db.conn import get_db
from src.db.models import Onsen, OnsenVisit
from src.const import CONST


class InteractiveSession:
    """Manages an interactive session with history tracking and navigation."""

    GO_BACK_COMMANDS = ["back", "b", "go back", "previous", "prev", "p"]
    GO_BACK_MULTIPLE_COMMANDS = ["back", "b", "go back", "previous", "prev", "p"]

    def __init__(self):
        self.visit_data: Dict[str, Any] = {}
        self.history: List[Tuple[str, Any, str]] = []  # (field_name, value, prompt)
        self.current_step = 0

    def add_to_history(self, field_name: str, value: Any, prompt: str):
        """Add a field to the conversation history."""
        self.history.append((field_name, value, prompt))
        self.current_step += 1

    def get_previous_answer(self, field_name: str) -> Optional[Any]:
        """Get the previous answer for a field."""
        for fname, value, _ in reversed(self.history):
            if fname == field_name:
                return value
        return None

    def go_back(self, steps: int = 1) -> int:
        """Go back a specified number of steps. Returns the number of steps actually gone back."""
        if steps <= 0 or self.current_step == 0:
            return 0

        steps_to_go_back = min(steps, self.current_step)
        self.current_step -= steps_to_go_back

        # Remove the last N entries from history
        for _ in range(steps_to_go_back):
            if self.history:
                field_name, _, _ = self.history.pop()
                if field_name in self.visit_data:
                    del self.visit_data[field_name]

        return steps_to_go_back

    def get_valid_input_with_navigation(
        self, prompt: str, validator: Callable, field_name: str, max_attempts: int = 3
    ) -> Optional[Any]:
        """Get valid input from user with navigation support."""
        # Show current value if it exists
        current_value = self.get_previous_answer(field_name)
        if current_value is not None:
            prompt = f"{prompt} (current: {current_value}) "

        # Add navigation hint
        prompt = f"{prompt} (type 'back' to go back, 'back N' to go back N steps): "

        for attempt in range(max_attempts):
            try:
                user_input = input(prompt).strip()

                # Check for navigation commands
                if user_input.lower() in self.GO_BACK_COMMANDS:
                    steps_gone_back = self.go_back(1)
                    if steps_gone_back > 0:
                        print(f"↩️  Went back {steps_gone_back} step(s)")
                        return None  # Signal to caller that we went back
                    else:
                        print("⚠️  Already at the beginning")
                        continue

                # Check for multiple step navigation (e.g., "back 3")
                if user_input.lower().startswith("back "):
                    try:
                        steps = int(user_input.split()[1])
                        steps_gone_back = self.go_back(steps)
                        if steps_gone_back > 0:
                            print(f"↩️  Went back {steps_gone_back} step(s)")
                            return None  # Signal to caller that we went back
                        else:
                            print("⚠️  Already at the beginning")
                            continue
                    except (ValueError, IndexError):
                        print(
                            "⚠️  Invalid format. Use 'back' or 'back N' where N is a number"
                        )
                        continue

                # Validate the input
                if validator(user_input):
                    return user_input

                print("Invalid input. Please try again.")

            except (ValueError, KeyboardInterrupt):
                if attempt == max_attempts - 1:
                    print("\nToo many invalid attempts. Exiting.")
                    sys.exit(1)
                print("Invalid input. Please try again.")

        return None

    def get_simple_input_with_navigation(
        self, prompt: str, field_name: str, allow_empty: bool = True
    ) -> Optional[str]:
        """Get simple text input with navigation support."""
        # Show current value if it exists
        current_value = self.get_previous_answer(field_name)
        if current_value is not None:
            prompt = f"{prompt} (current: {current_value}) "

        # Add navigation hint
        prompt = f"{prompt} (type 'back' to go back, 'back N' to go back N steps): "

        while True:
            user_input = input(prompt).strip()

            # Check for navigation commands
            if user_input.lower() in self.GO_BACK_COMMANDS:
                steps_gone_back = self.go_back(1)
                if steps_gone_back > 0:
                    print(f"↩️  Went back {steps_gone_back} step(s)")
                    return None  # Signal to caller that we went back
                else:
                    print("⚠️  Already at the beginning")
                    continue

            # Check for multiple step navigation (e.g., "back 3")
            if user_input.lower().startswith("back "):
                try:
                    steps = int(user_input.split()[1])
                    steps_gone_back = self.go_back(steps)
                    if steps_gone_back > 0:
                        print(f"↩️  Went back {steps_gone_back} step(s)")
                        return None  # Signal to caller that we went back
                    else:
                        print("⚠️  Already at the beginning")
                        continue
                except (ValueError, IndexError):
                    print(
                        "⚠️  Invalid format. Use 'back' or 'back N' where N is a number"
                    )
                    continue

            # Return the input (empty is allowed if allow_empty is True)
            if allow_empty or user_input:
                return user_input
            else:
                print("This field cannot be empty. Please provide a value.")


def add_visit_interactive() -> None:
    """
    Interactive version of add_visit that guides users through a series of questions.
    Supports navigation back to previous answers.
    """
    print("🌊 Welcome to the Interactive Onsen Visit Recorder! 🌊")
    print("I'll guide you through recording your onsen visit experience.")
    print("💡 Tip: Type 'back' to go back one step, or 'back N' to go back N steps.\n")

    session = InteractiveSession()

    # Helper validation functions
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

    # Step 1: Get onsen ID
    print("Step 1: Select the onsen")
    while True:
        onsen_id_input = session.get_valid_input_with_navigation(
            "Enter the onsen ID: ", validate_onsen_id, "onsen_id", max_attempts=3
        )
        if onsen_id_input is None:  # User went back
            continue
        if onsen_id_input is not None:
            session.visit_data["onsen_id"] = int(onsen_id_input)
            session.add_to_history(
                "onsen_id", int(onsen_id_input), "Enter the onsen ID: "
            )
            break

    # Step 2: Get visit time
    print("\nStep 2: Visit time")
    while True:
        time_input = session.get_simple_input_with_navigation(
            "Enter visit time (YYYY-MM-DD HH:MM) or press Enter for now: ", "visit_time"
        )
        if time_input is None:  # User went back
            continue
        if not time_input:
            session.visit_data["visit_time"] = datetime.now()
            session.add_to_history("visit_time", datetime.now(), "Enter visit time")
            break
        if validate_datetime(time_input):
            session.visit_data["visit_time"] = datetime.strptime(
                time_input, "%Y-%m-%d %H:%M"
            )
            session.add_to_history(
                "visit_time",
                datetime.strptime(time_input, "%Y-%m-%d %H:%M"),
                "Enter visit time",
            )
            break
        print("Invalid datetime format. Please use YYYY-MM-DD HH:MM")

    # Step 3: Basic information
    print("\nStep 3: Basic information")

    # Entry fee
    while True:
        fee_input = session.get_valid_input_with_navigation(
            "Entry fee (yen): ", validate_integer, "entry_fee_yen"
        )
        if fee_input is None:  # User went back
            continue
        if fee_input:
            session.visit_data["entry_fee_yen"] = int(fee_input)
            session.add_to_history("entry_fee_yen", int(fee_input), "Entry fee (yen): ")
        break

    # Stay length
    while True:
        stay_input = session.get_valid_input_with_navigation(
            "Stay length (minutes): ", validate_integer, "stay_length_minutes"
        )
        if stay_input is None:  # User went back
            continue
        if stay_input:
            session.visit_data["stay_length_minutes"] = int(stay_input)
            session.add_to_history(
                "stay_length_minutes", int(stay_input), "Stay length (minutes): "
            )
        break

    # Travel time
    while True:
        travel_input = session.get_valid_input_with_navigation(
            "Travel time (minutes): ", validate_integer, "travel_time_minutes"
        )
        if travel_input is None:  # User went back
            continue
        if travel_input:
            session.visit_data["travel_time_minutes"] = int(travel_input)
            session.add_to_history(
                "travel_time_minutes", int(travel_input), "Travel time (minutes): "
            )
        break

    # Step 4: Ratings
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
        while True:
            rating_input = session.get_valid_input_with_navigation(
                f"{rating.replace('_', ' ').title()}: ",
                lambda x: not x or validate_rating(x),
                rating,
            )
            if rating_input is None:  # User went back
                continue
            if rating_input:
                session.visit_data[rating] = int(rating_input)
                session.add_to_history(
                    rating, int(rating_input), f"{rating.replace('_', ' ').title()}: "
                )
            break

    # Step 5: Temperatures
    print("\nStep 5: Temperatures (press Enter to skip)")

    # Main bath temperature
    while True:
        temp_input = session.get_valid_input_with_navigation(
            "Main bath temperature (°C): ",
            lambda x: not x or validate_float(x),
            "main_bath_temperature",
        )
        if temp_input is None:  # User went back
            continue
        if temp_input:
            session.visit_data["main_bath_temperature"] = float(temp_input)
            session.add_to_history(
                "main_bath_temperature",
                float(temp_input),
                "Main bath temperature (°C): ",
            )
        break

    # Sauna temperature
    while True:
        sauna_temp_input = session.get_valid_input_with_navigation(
            "Sauna temperature (°C): ",
            lambda x: not x or validate_float(x),
            "sauna_temperature",
        )
        if sauna_temp_input is None:  # User went back
            continue
        if sauna_temp_input:
            session.visit_data["sauna_temperature"] = float(sauna_temp_input)
            session.add_to_history(
                "sauna_temperature", float(sauna_temp_input), "Sauna temperature (°C): "
            )
        break

    # Outdoor bath temperature
    while True:
        outdoor_temp_input = session.get_valid_input_with_navigation(
            "Outdoor bath temperature (°C): ",
            lambda x: not x or validate_float(x),
            "outdoor_bath_temperature",
        )
        if outdoor_temp_input is None:  # User went back
            continue
        if outdoor_temp_input:
            session.visit_data["outdoor_bath_temperature"] = float(outdoor_temp_input)
            session.add_to_history(
                "outdoor_bath_temperature",
                float(outdoor_temp_input),
                "Outdoor bath temperature (°C): ",
            )
        break

    # Outside temperature
    while True:
        outside_temp_input = session.get_valid_input_with_navigation(
            "Outside temperature (°C): ",
            lambda x: not x or validate_float(x),
            "temperature_outside_celsius",
        )
        if outside_temp_input is None:  # User went back
            continue
        if outside_temp_input:
            session.visit_data["temperature_outside_celsius"] = float(
                outside_temp_input
            )
            session.add_to_history(
                "temperature_outside_celsius",
                float(outside_temp_input),
                "Outside temperature (°C): ",
            )
        break

    # Step 6: Text fields
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
        while True:
            value = session.get_simple_input_with_navigation(
                f"{field.replace('_', ' ').title()}: ", field
            )
            if value is None:  # User went back
                continue
            if value:
                session.visit_data[field] = value
                session.add_to_history(
                    field, value, f"{field.replace('_', ' ').title()}: "
                )
            break

    # Step 7: Boolean fields
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
            # Show current value if it exists
            current_value = session.get_previous_answer(field)
            if current_value is not None:
                prompt = f"{field.replace('_', ' ').title()}? (y/n) (current: {current_value}): "
            else:
                prompt = f"{field.replace('_', ' ').title()}? (y/n): "

            # Add navigation hint
            prompt = f"{prompt} (type 'back' to go back, 'back N' to go back N steps): "

            response = input(prompt).strip().lower()

            # Check for navigation commands
            if response in session.GO_BACK_COMMANDS:
                steps_gone_back = session.go_back(1)
                if steps_gone_back > 0:
                    print(f"↩️  Went back {steps_gone_back} step(s)")
                    continue
                else:
                    print("⚠️  Already at the beginning")
                    continue

            # Check for multiple step navigation
            if response.startswith("back "):
                try:
                    steps = int(response.split()[1])
                    steps_gone_back = session.go_back(steps)
                    if steps_gone_back > 0:
                        print(f"↩️  Went back {steps_gone_back} step(s)")
                        continue
                    else:
                        print("⚠️  Already at the beginning")
                        continue
                except (ValueError, IndexError):
                    print(
                        "⚠️  Invalid format. Use 'back' or 'back N' where N is a number"
                    )
                    continue

            if response in ["y", "yes"]:
                session.visit_data[field] = True
                session.add_to_history(
                    field, True, f"{field.replace('_', ' ').title()}? (y/n): "
                )
                break
            elif response in ["n", "no"]:
                session.visit_data[field] = False
                session.add_to_history(
                    field, False, f"{field.replace('_', ' ').title()}? (y/n): "
                )
                break
            else:
                print("Please enter 'y' or 'n'")

    # Step 8: Additional integer fields
    print("\nStep 8: Additional details (press Enter to skip)")

    int_fields = [
        "excercise_length_minutes",
        "sauna_duration_minutes",
        "previous_location",
        "next_location",
        "visit_order",
    ]

    for field in int_fields:
        while True:
            value = session.get_valid_input_with_navigation(
                f"{field.replace('_', ' ').title()}: ",
                lambda x: not x or validate_integer(x),
                field,
            )
            if value is None:  # User went back
                continue
            if value:
                session.visit_data[field] = int(value)
                session.add_to_history(
                    field, int(value), f"{field.replace('_', ' ').title()}: "
                )
            break

    # Save the visit
    print("\nSaving visit data...")
    with get_db(url=CONST.DATABASE_URL) as db:
        onsen = (
            db.query(Onsen).filter(Onsen.id == session.visit_data["onsen_id"]).first()
        )
        visit = OnsenVisit(**session.visit_data)
        db.add(visit)
        db.commit()

        print(f"✅ Successfully recorded visit to {onsen.name}!")
        print(f"Visit ID: {visit.id}")
        print(f"Visit time: {visit.visit_time}")
        print(f"Personal rating: {visit.personal_rating}/10")
