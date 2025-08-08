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

    steps = [
        {
            "name": "onsen_id",
            "prompt": "Enter the onsen ID: ",
            "validator": validate_onsen_id,
            "processor": lambda x: int(x),
            "required": True,
            "step_title": "Step 1: Select the onsen",
        },
        {
            "name": "visit_time",
            "prompt": "Enter visit time (YYYY-MM-DD HH:MM) or press Enter for now: ",
            "validator": lambda x: not x or validate_datetime(x),
            "processor": lambda x: (
                datetime.now() if not x else datetime.strptime(x, "%Y-%m-%d %H:%M")
            ),
            "required": True,
            "step_title": "Step 2: Visit time",
        },
        {
            "name": "entry_fee_yen",
            "prompt": "Entry fee (yen): ",
            "validator": validate_integer,
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 3: Basic information",
        },
        {
            "name": "stay_length_minutes",
            "prompt": "Stay length (minutes): ",
            "validator": validate_integer,
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 3: Basic information",
        },
        {
            "name": "travel_time_minutes",
            "prompt": "Travel time (minutes): ",
            "validator": validate_integer,
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 3: Basic information",
        },
        {
            "name": "accessibility_rating",
            "prompt": "Accessibility Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "cleanliness_rating",
            "prompt": "Cleanliness Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "navigability_rating",
            "prompt": "Navigability Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "view_rating",
            "prompt": "View Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "smell_intensity_rating",
            "prompt": "Smell Intensity Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "changing_room_cleanliness_rating",
            "prompt": "Changing Room Cleanliness Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "locker_availability_rating",
            "prompt": "Locker Availability Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "rest_area_rating",
            "prompt": "Rest Area Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "food_quality_rating",
            "prompt": "Food Quality Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "sauna_rating",
            "prompt": "Sauna Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "outdoor_bath_rating",
            "prompt": "Outdoor Bath Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "energy_level_change",
            "prompt": "Energy Level Change: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "hydration_level",
            "prompt": "Hydration Level: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "atmosphere_rating",
            "prompt": "Atmosphere Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "personal_rating",
            "prompt": "Personal Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        {
            "name": "main_bath_temperature",
            "prompt": "Main bath temperature (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "required": False,
            "step_title": "Step 5: Temperatures (press Enter to skip)",
        },
        {
            "name": "sauna_temperature",
            "prompt": "Sauna temperature (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "required": False,
            "step_title": "Step 5: Temperatures (press Enter to skip)",
        },
        {
            "name": "outdoor_bath_temperature",
            "prompt": "Outdoor bath temperature (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "required": False,
            "step_title": "Step 5: Temperatures (press Enter to skip)",
        },
        {
            "name": "temperature_outside_celsius",
            "prompt": "Outside temperature (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "required": False,
            "step_title": "Step 5: Temperatures (press Enter to skip)",
        },
        {
            "name": "payment_method",
            "prompt": "Payment Method: ",
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "weather",
            "prompt": "Weather: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "time_of_day",
            "prompt": "Time Of Day: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "visited_with",
            "prompt": "Visited With: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "travel_mode",
            "prompt": "Travel Mode: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "excercise_type",
            "prompt": "Excercise Type: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "crowd_level",
            "prompt": "Crowd Level: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "heart_rate_data",
            "prompt": "Heart Rate Data: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "main_bath_type",
            "prompt": "Main Bath Type: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "main_bath_water_type",
            "prompt": "Main Bath Water Type: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "water_color",
            "prompt": "Water Color: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "pre_visit_mood",
            "prompt": "Pre Visit Mood: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "post_visit_mood",
            "prompt": "Post Visit Mood: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        {
            "name": "excercise_before_onsen",
            "prompt": "Excercise Before Onsen? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "had_soap",
            "prompt": "Had Soap? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "had_sauna",
            "prompt": "Had Sauna? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "had_outdoor_bath",
            "prompt": "Had Outdoor Bath? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "had_rest_area",
            "prompt": "Had Rest Area? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "had_food_service",
            "prompt": "Had Food Service? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "massage_chair_available",
            "prompt": "Massage Chair Available? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "sauna_visited",
            "prompt": "Sauna Visited? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "sauna_steam",
            "prompt": "Sauna Steam? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "outdoor_bath_visited",
            "prompt": "Outdoor Bath Visited? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "multi_onsen_day",
            "prompt": "Multi Onsen Day? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        {
            "name": "excercise_length_minutes",
            "prompt": "Excercise Length Minutes: ",
            "validator": lambda x: not x or validate_integer(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 8: Additional details (press Enter to skip)",
        },
        {
            "name": "sauna_duration_minutes",
            "prompt": "Sauna Duration Minutes: ",
            "validator": lambda x: not x or validate_integer(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 8: Additional details (press Enter to skip)",
        },
        {
            "name": "previous_location",
            "prompt": "Previous Location: ",
            "validator": lambda x: not x or validate_integer(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 8: Additional details (press Enter to skip)",
        },
        {
            "name": "next_location",
            "prompt": "Next Location: ",
            "validator": lambda x: not x or validate_integer(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 8: Additional details (press Enter to skip)",
        },
        {
            "name": "visit_order",
            "prompt": "Visit Order: ",
            "validator": lambda x: not x or validate_integer(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 8: Additional details (press Enter to skip)",
        },
    ]

    # Execute the workflow
    current_step_index = 0
    last_step_title = None

    while current_step_index < len(steps):
        step = steps[current_step_index]

        # Print step title if it changed
        if step["step_title"] != last_step_title:
            print(f"\n{step['step_title']}")
            last_step_title = step["step_title"]

        # Get input for this step
        while True:
            # Show current value if it exists
            current_value = session.get_previous_answer(step["name"])
            prompt = step["prompt"]
            if current_value is not None:
                prompt = f"{prompt} (current: {current_value}) "

            user_input = input(prompt).strip()

            # Check for navigation commands
            if user_input.lower() in session.GO_BACK_COMMANDS:
                steps_gone_back = session.go_back(1)
                if steps_gone_back > 0:
                    print(f"↩️  Went back {steps_gone_back} step(s)")
                    # Go back in the step index
                    current_step_index = max(0, current_step_index - steps_gone_back)
                    break
                else:
                    print("⚠️  Already at the beginning")
                    continue

            # Check for multiple step navigation
            if user_input.lower().startswith("back "):
                try:
                    steps_to_go_back = int(user_input.split()[1])
                    steps_gone_back = session.go_back(steps_to_go_back)
                    if steps_gone_back > 0:
                        print(f"↩️  Went back {steps_gone_back} step(s)")
                        # Go back in the step index
                        current_step_index = max(
                            0, current_step_index - steps_gone_back
                        )
                        break
                    else:
                        print("⚠️  Already at the beginning")
                        continue
                except (ValueError, IndexError):
                    print(
                        "⚠️  Invalid format. Use 'back' or 'back N' where N is a number"
                    )
                    continue

            # Validate input
            if step["validator"](user_input):
                # Process the input
                processed_value = step["processor"](user_input)

                # Store the value if it's not None
                if processed_value is not None:
                    session.visit_data[step["name"]] = processed_value
                    session.add_to_history(
                        step["name"], processed_value, step["prompt"]
                    )

                # Move to next step
                current_step_index += 1
                break
            else:
                print("Invalid input. Please try again.")

        # # 1. Get onsen ID
        # print("Step 1: Select the onsen")
        # onsen_id_input = get_valid_input(
        #     "Enter the onsen ID: ", validate_onsen_id, max_attempts=3
        # )
        # if onsen_id_input is None:
        #     sys.exit(1)
        # visit_data["onsen_id"] = int(onsen_id_input)

        # # 2. Basic visit information
        # print("\nStep 2: Basic visit information")

        # # Entry fee
        # entry_fee = get_valid_input(
        #     "What was the entry fee in yen? (0 if free): ", validate_integer
        # )
        # visit_data["entry_fee_yen"] = int(entry_fee) if entry_fee else 0

        # # Payment method
        # payment_method = input("Payment method (cash/card/etc.): ").strip()
        # visit_data["payment_method"] = payment_method if payment_method else ""

        # # Visit time
        # visit_time = get_valid_input(
        #     "Visit time (YYYY-MM-DD HH:MM, or press Enter for now): ",
        #     lambda x: x == "" or validate_datetime(x),
        # )
        # if visit_time:
        #     visit_data["visit_time"] = visit_time
        # else:
        #     visit_data["visit_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        # # Weather
        # weather = input("Weather conditions: ").strip()
        # visit_data["weather"] = weather if weather else ""

        # # Time of day
        # time_of_day = input("Time of day (morning/afternoon/evening): ").strip()
        # visit_data["time_of_day"] = time_of_day if time_of_day else ""

        # # Temperature outside
        # temp_outside = get_valid_input("Temperature outside in Celsius: ", validate_float)
        # visit_data["temperature_outside_celsius"] = (
        #     float(temp_outside) if temp_outside else 0.0
        # )

        # # Stay length
        # stay_length = get_valid_input("How long did you stay (minutes): ", validate_integer)
        # visit_data["stay_length_minutes"] = int(stay_length) if stay_length else 0

        # # 3. Travel information
        # print("\nStep 3: Travel information")

        # visited_with = input("Who did you visit with (alone/friend/group): ").strip()
        # visit_data["visited_with"] = visited_with if visited_with else ""

        # travel_mode = input("Travel mode (car/train/bus/walk/run/bike): ").strip()
        # visit_data["travel_mode"] = travel_mode if travel_mode else ""

        # travel_time = get_valid_input("Travel time in minutes: ", validate_integer)
        # visit_data["travel_time_minutes"] = int(travel_time) if travel_time else 0

        # # 4. Exercise information
        # print("\nStep 4: Exercise information")

        # exercise_before = get_valid_input(
        #     "Did you exercise before the onsen? (y/n): ", validate_yes_no
        # )
        # visit_data["excercise_before_onsen"] = exercise_before.lower() in ["y", "yes"]

        # if visit_data["excercise_before_onsen"]:
        #     exercise_type = input("Exercise type (running/walking/cycling/other): ").strip()
        #     visit_data["excercise_type"] = exercise_type if exercise_type else ""

        #     exercise_length = get_valid_input(
        #         "Exercise duration in minutes: ", validate_integer
        #     )
        #     visit_data["excercise_length_minutes"] = (
        #         int(exercise_length) if exercise_length else 0
        #     )

        # # 5. Facility ratings
        # print("\nStep 5: Facility ratings (1-10 scale)")

        # accessibility = get_valid_input("Accessibility rating (1-10): ", validate_rating)
        # visit_data["accessibility_rating"] = int(accessibility) if accessibility else 0

        # cleanliness = get_valid_input("Cleanliness rating (1-10): ", validate_rating)
        # visit_data["cleanliness_rating"] = int(cleanliness) if cleanliness else 0

        # navigability = get_valid_input("Navigability rating (1-10): ", validate_rating)
        # visit_data["navigability_rating"] = int(navigability) if navigability else 0

        # view_rating = get_valid_input("View rating (1-10): ", validate_rating)
        # visit_data["view_rating"] = int(view_rating) if view_rating else 0

        # atmosphere = get_valid_input("Atmosphere rating (1-10): ", validate_rating)
        # visit_data["atmosphere_rating"] = int(atmosphere) if atmosphere else 0

        # # 6. Main bath information
        # print("\nStep 6: Main bath information")

        # main_bath_type = input("Main bath type (open air/indoor/other): ").strip()
        # visit_data["main_bath_type"] = main_bath_type if main_bath_type else ""

        # main_bath_temp = get_valid_input(
        #     "Main bath temperature in Celsius: ", validate_float
        # )
        # visit_data["main_bath_temperature"] = (
        #     float(main_bath_temp) if main_bath_temp else 0.0
        # )

        # main_bath_water = input("Main bath water type (sulfur/salt/other): ").strip()
        # visit_data["main_bath_water_type"] = main_bath_water if main_bath_water else ""

        # water_color = input("Water color (clear/brown/green/other): ").strip()
        # visit_data["water_color"] = water_color if water_color else ""

        # smell_intensity = get_valid_input(
        #     "Smell intensity rating (1-10): ", validate_rating
        # )
        # visit_data["smell_intensity_rating"] = (
        #     int(smell_intensity) if smell_intensity else 0
        # )

        # # 7. Changing room and facilities
        # print("\nStep 7: Changing room and facilities")

        # changing_cleanliness = get_valid_input(
        #     "Changing room cleanliness rating (1-10): ", validate_rating
        # )
        # visit_data["changing_room_cleanliness_rating"] = (
        #     int(changing_cleanliness) if changing_cleanliness else 0
        # )

        # locker_availability = get_valid_input(
        #     "Locker availability rating (1-10): ", validate_rating
        # )
        # visit_data["locker_availability_rating"] = (
        #     int(locker_availability) if locker_availability else 0
        # )

        # had_soap = get_valid_input("Was soap available? (y/n): ", validate_yes_no)
        # visit_data["had_soap"] = had_soap.lower() in ["y", "yes"]

        # # 8. Sauna information
        # print("\nStep 8: Sauna information")

        # had_sauna = get_valid_input(
        #     "Was there a sauna at the facility? (y/n): ", validate_yes_no
        # )
        # visit_data["had_sauna"] = had_sauna.lower() in ["y", "yes"]

        # if visit_data["had_sauna"]:
        #     sauna_visited = get_valid_input(
        #         "Did you use the sauna? (y/n): ", validate_yes_no
        #     )
        #     visit_data["sauna_visited"] = sauna_visited.lower() in ["y", "yes"]

        #     if visit_data["sauna_visited"]:
        #         sauna_temp = get_valid_input(
        #             "Sauna temperature in Celsius: ", validate_float
        #         )
        #         visit_data["sauna_temperature"] = float(sauna_temp) if sauna_temp else 0.0

        #         sauna_steam = get_valid_input(
        #             "Did the sauna have steam? (y/n): ", validate_yes_no
        #         )
        #         visit_data["sauna_steam"] = sauna_steam.lower() in ["y", "yes"]

        #         sauna_duration = get_valid_input(
        #             "How long did you stay in the sauna (minutes): ", validate_integer
        #         )
        #         visit_data["sauna_duration_minutes"] = (
        #             int(sauna_duration) if sauna_duration else 0
        #         )

        #         sauna_rating = get_valid_input("Sauna rating (1-10): ", validate_rating)
        #         visit_data["sauna_rating"] = int(sauna_rating) if sauna_rating else 0

        # # 9. Outdoor bath information
        # print("\nStep 9: Outdoor bath information")

        # had_outdoor_bath = get_valid_input(
        #     "Was there an outdoor bath at the facility? (y/n): ", validate_yes_no
        # )
        # visit_data["had_outdoor_bath"] = had_outdoor_bath.lower() in ["y", "yes"]

        # if visit_data["had_outdoor_bath"]:
        #     outdoor_bath_visited = get_valid_input(
        #         "Did you use the outdoor bath? (y/n): ", validate_yes_no
        #     )
        #     visit_data["outdoor_bath_visited"] = outdoor_bath_visited.lower() in [
        #         "y",
        #         "yes",
        #     ]

        #     if visit_data["outdoor_bath_visited"]:
        #         outdoor_bath_temp = get_valid_input(
        #             "Outdoor bath temperature in Celsius: ", validate_float
        #         )
        #         visit_data["outdoor_bath_temperature"] = (
        #             float(outdoor_bath_temp) if outdoor_bath_temp else 0.0
        #         )

        #         outdoor_bath_rating = get_valid_input(
        #             "Outdoor bath rating (1-10): ", validate_rating
        #         )
        #         visit_data["outdoor_bath_rating"] = (
        #             int(outdoor_bath_rating) if outdoor_bath_rating else 0
        #         )

        # # 10. Rest area and food
        # print("\nStep 10: Rest area and food")

        # # TODO add if I had visited a rest area
        # had_rest_area = get_valid_input("Was there a rest area? (y/n): ", validate_yes_no)
        # visit_data["had_rest_area"] = had_rest_area.lower() in ["y", "yes"]

        # if visit_data["had_rest_area"]:
        #     rest_area_rating = get_valid_input("Rest area rating (1-10): ", validate_rating)
        #     visit_data["rest_area_rating"] = (
        #         int(rest_area_rating) if rest_area_rating else 0
        #     )

        # # TODO add if I had tried the food
        # had_food_service = get_valid_input(
        #     "Was there food service? (y/n): ", validate_yes_no
        # )
        # visit_data["had_food_service"] = had_food_service.lower() in ["y", "yes"]

        # if visit_data["had_food_service"]:
        #     food_quality = get_valid_input("Food quality rating (1-10): ", validate_rating)
        #     visit_data["food_quality_rating"] = int(food_quality) if food_quality else 0

        # massage_chair = get_valid_input(
        #     "Were massage chairs available? (y/n): ", validate_yes_no
        # )
        # visit_data["massage_chair_available"] = massage_chair.lower() in ["y", "yes"]

        # # 11. Crowd and mood
        # print("\nStep 11: Crowd and mood")

        # crowd_level = input("Crowd level (busy/moderate/quiet/empty): ").strip()
        # visit_data["crowd_level"] = crowd_level if crowd_level else ""

        # pre_visit_mood = input(
        #     "Mood before visit (relaxed/stressed/anxious/other): "
        # ).strip()
        # visit_data["pre_visit_mood"] = pre_visit_mood if pre_visit_mood else ""

        # post_visit_mood = input(
        #     "Mood after visit (relaxed/stressed/anxious/other): "
        # ).strip()
        # visit_data["post_visit_mood"] = post_visit_mood if post_visit_mood else ""

        # # 12. Health and energy
        # print("\nStep 12: Health and energy")

        # energy_change = get_valid_input(
        #     "Energy level change (-5 to +5, negative = less energy): ",
        #     lambda x: validate_integer(x) and -5 <= int(x) <= 5,
        # )
        # visit_data["energy_level_change"] = int(energy_change) if energy_change else 0

        # hydration = get_valid_input(
        #     "Hydration level before entering (1-10): ", validate_rating
        # )
        # visit_data["hydration_level"] = int(hydration) if hydration else 0

        # # 13. Multi-onsen day
        # print("\nStep 13: Multi-onsen day")

        # multi_onsen = get_valid_input(
        #     "Was this part of a multi-onsen day? (y/n): ", validate_yes_no
        # )
        # visit_data["multi_onsen_day"] = multi_onsen.lower() in ["y", "yes"]

        # if visit_data["multi_onsen_day"]:
        #     visit_order = get_valid_input(
        #         "Visit order (1st, 2nd, etc.): ", validate_integer
        #     )
        #     visit_data["visit_order"] = int(visit_order) if visit_order else 0

        # # 14. Personal rating
        # print("\nStep 14: Personal rating")

        # personal_rating = get_valid_input(
        #     "Personal overall rating (1-10): ", validate_rating
        # )
        # visit_data["personal_rating"] = int(personal_rating) if personal_rating else 0

        # # 15. Additional information
        # print("\nStep 15: Additional information")

        # heart_rate_data = input("Heart rate data (optional): ").strip()
        # visit_data["heart_rate_data"] = heart_rate_data if heart_rate_data else ""

        # # Set defaults for fields that weren't explicitly set
        # defaults = {
        #     "previous_location": 0,
        #     "next_location": 0,
        # }

        # for key, default_value in defaults.items():
        #     if key not in visit_data:
        #         visit_data[key] = default_value

        # # Build the command
        # print("\n" + "=" * 50)
        # print("SUMMARY OF YOUR VISIT")
        # print("=" * 50)

        # # Show key information
        # with get_db(url=CONST.DATABASE_URL) as db:
        #     onsen = db.query(Onsen).filter(Onsen.id == visit_data["onsen_id"]).first()
        #     print(f"Onsen: {onsen.name} (ID: {onsen.id})")

        # print(f"Entry fee: {visit_data['entry_fee_yen']} yen")
        # print(f"Stay length: {visit_data['stay_length_minutes']} minutes")
        # print(f"Personal rating: {visit_data['personal_rating']}/10")

        # # Ask for confirmation
        # confirm = get_valid_input(
        #     "\nProceed with adding this visit? (y/n): ", validate_yes_no
        # )

        # if confirm.lower() in ["y", "yes"]:
        #     # Build command arguments
        #     cmd_args = ["onsendo", "add-visit"]

        #     for key, value in visit_data.items():
        #         if isinstance(value, bool):
        #             if value:
        #                 cmd_args.append(f"--{key}")
        #         elif value is not None and value != "":
        #             cmd_args.append(f"--{key}")
        #             cmd_args.append(str(value))

        #     print(f"\nExecuting command: {' '.join(cmd_args)}")

    # Save the visit
    print("\nSaving visit data...")
    with get_db(url=CONST.DATABASE_URL) as db:
        onsen = (
            db.query(Onsen).filter(Onsen.id == session.visit_data["onsen_id"]).first()
        )
        visit = OnsenVisit(**session.visit_data)
        # TODO Disable for now
        # db.add(visit)
        # db.commit()

        print(f"✅ Successfully recorded visit to {onsen.name}!")
        print(f"Visit ID: {visit.id}")
        print(f"Visit time: {visit.visit_time}")
        print(f"Personal rating: {visit.personal_rating}/10")
