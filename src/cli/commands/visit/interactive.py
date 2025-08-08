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

    # Define all steps in the workflow
    steps = [
        # Step 1: Onsen ID
        {
            "name": "onsen_id",
            "prompt": "Enter the onsen ID: ",
            "validator": validate_onsen_id,
            "processor": lambda x: int(x),
            "required": True,
            "step_title": "Step 1: Select the onsen",
        },
        # Step 2: Visit time
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
        # Step 3: Entry fee
        {
            "name": "entry_fee_yen",
            "prompt": "Entry fee (yen): ",
            "validator": validate_integer,
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 3: Basic information",
        },
        # Step 4: Stay length
        {
            "name": "stay_length_minutes",
            "prompt": "Stay length (minutes): ",
            "validator": validate_integer,
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 3: Basic information",
        },
        # Step 5: Travel time
        {
            "name": "travel_time_minutes",
            "prompt": "Travel time (minutes): ",
            "validator": validate_integer,
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 3: Basic information",
        },
        # Step 6: Accessibility rating
        {
            "name": "accessibility_rating",
            "prompt": "Accessibility Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 7: Cleanliness rating
        {
            "name": "cleanliness_rating",
            "prompt": "Cleanliness Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 8: Navigability rating
        {
            "name": "navigability_rating",
            "prompt": "Navigability Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 9: View rating
        {
            "name": "view_rating",
            "prompt": "View Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 10: Smell intensity rating
        {
            "name": "smell_intensity_rating",
            "prompt": "Smell Intensity Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 11: Changing room cleanliness rating
        {
            "name": "changing_room_cleanliness_rating",
            "prompt": "Changing Room Cleanliness Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 12: Locker availability rating
        {
            "name": "locker_availability_rating",
            "prompt": "Locker Availability Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 13: Rest area rating
        {
            "name": "rest_area_rating",
            "prompt": "Rest Area Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 14: Food quality rating
        {
            "name": "food_quality_rating",
            "prompt": "Food Quality Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 15: Sauna rating
        {
            "name": "sauna_rating",
            "prompt": "Sauna Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 16: Outdoor bath rating
        {
            "name": "outdoor_bath_rating",
            "prompt": "Outdoor Bath Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 17: Energy level change
        {
            "name": "energy_level_change",
            "prompt": "Energy Level Change: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 18: Hydration level
        {
            "name": "hydration_level",
            "prompt": "Hydration Level: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 19: Atmosphere rating
        {
            "name": "atmosphere_rating",
            "prompt": "Atmosphere Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 20: Personal rating
        {
            "name": "personal_rating",
            "prompt": "Personal Rating: ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 4: Ratings (1-10, press Enter to skip)",
        },
        # Step 21: Main bath temperature
        {
            "name": "main_bath_temperature",
            "prompt": "Main bath temperature (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "required": False,
            "step_title": "Step 5: Temperatures (press Enter to skip)",
        },
        # Step 22: Sauna temperature
        {
            "name": "sauna_temperature",
            "prompt": "Sauna temperature (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "required": False,
            "step_title": "Step 5: Temperatures (press Enter to skip)",
        },
        # Step 23: Outdoor bath temperature
        {
            "name": "outdoor_bath_temperature",
            "prompt": "Outdoor bath temperature (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "required": False,
            "step_title": "Step 5: Temperatures (press Enter to skip)",
        },
        # Step 24: Outside temperature
        {
            "name": "temperature_outside_celsius",
            "prompt": "Outside temperature (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "required": False,
            "step_title": "Step 5: Temperatures (press Enter to skip)",
        },
        # Step 25: Payment method
        {
            "name": "payment_method",
            "prompt": "Payment Method: ",
            "validator": lambda x: True,  # Any text is valid
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 26: Weather
        {
            "name": "weather",
            "prompt": "Weather: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 27: Time of day
        {
            "name": "time_of_day",
            "prompt": "Time Of Day: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 28: Visited with
        {
            "name": "visited_with",
            "prompt": "Visited With: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 29: Travel mode
        {
            "name": "travel_mode",
            "prompt": "Travel Mode: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 30: Exercise type
        {
            "name": "excercise_type",
            "prompt": "Excercise Type: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 31: Crowd level
        {
            "name": "crowd_level",
            "prompt": "Crowd Level: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 32: Heart rate data
        {
            "name": "heart_rate_data",
            "prompt": "Heart Rate Data: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 33: Main bath type
        {
            "name": "main_bath_type",
            "prompt": "Main Bath Type: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 34: Main bath water type
        {
            "name": "main_bath_water_type",
            "prompt": "Main Bath Water Type: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 35: Water color
        {
            "name": "water_color",
            "prompt": "Water Color: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 36: Pre visit mood
        {
            "name": "pre_visit_mood",
            "prompt": "Pre Visit Mood: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 37: Post visit mood
        {
            "name": "post_visit_mood",
            "prompt": "Post Visit Mood: ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "required": False,
            "step_title": "Step 6: Additional information (press Enter to skip)",
        },
        # Step 38: Exercise before onsen
        {
            "name": "excercise_before_onsen",
            "prompt": "Excercise Before Onsen? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 39: Had soap
        {
            "name": "had_soap",
            "prompt": "Had Soap? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 40: Had sauna
        {
            "name": "had_sauna",
            "prompt": "Had Sauna? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 41: Had outdoor bath
        {
            "name": "had_outdoor_bath",
            "prompt": "Had Outdoor Bath? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 42: Had rest area
        {
            "name": "had_rest_area",
            "prompt": "Had Rest Area? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 43: Had food service
        {
            "name": "had_food_service",
            "prompt": "Had Food Service? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 44: Massage chair available
        {
            "name": "massage_chair_available",
            "prompt": "Massage Chair Available? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 45: Sauna visited
        {
            "name": "sauna_visited",
            "prompt": "Sauna Visited? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 46: Sauna steam
        {
            "name": "sauna_steam",
            "prompt": "Sauna Steam? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 47: Outdoor bath visited
        {
            "name": "outdoor_bath_visited",
            "prompt": "Outdoor Bath Visited? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 48: Multi onsen day
        {
            "name": "multi_onsen_day",
            "prompt": "Multi Onsen Day? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "required": False,
            "step_title": "Step 7: Yes/No questions",
        },
        # Step 49: Exercise length minutes
        {
            "name": "excercise_length_minutes",
            "prompt": "Excercise Length Minutes: ",
            "validator": lambda x: not x or validate_integer(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 8: Additional details (press Enter to skip)",
        },
        # Step 50: Sauna duration minutes
        {
            "name": "sauna_duration_minutes",
            "prompt": "Sauna Duration Minutes: ",
            "validator": lambda x: not x or validate_integer(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 8: Additional details (press Enter to skip)",
        },
        # Step 51: Previous location
        {
            "name": "previous_location",
            "prompt": "Previous Location: ",
            "validator": lambda x: not x or validate_integer(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 8: Additional details (press Enter to skip)",
        },
        # Step 52: Next location
        {
            "name": "next_location",
            "prompt": "Next Location: ",
            "validator": lambda x: not x or validate_integer(x),
            "processor": lambda x: int(x) if x else None,
            "required": False,
            "step_title": "Step 8: Additional details (press Enter to skip)",
        },
        # Step 53: Visit order
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
