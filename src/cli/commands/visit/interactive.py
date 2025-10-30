"""
Interactive visit commands.
"""

import sys
import argparse
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any, Optional
from src.db.conn import get_db
from src.db.models import Onsen, OnsenVisit
from src.config import get_database_config
from src.lib.cli_display import show_database_banner


class InteractiveSession:
    """Manages an interactive session with history tracking and navigation."""

    GO_BACK_COMMANDS = ["back", "b", "go back", "previous", "prev", "p"]
    GO_BACK_MULTIPLE_COMMANDS = ["back", "b", "go back", "previous", "prev", "p"]

    def __init__(self):
        self.visit_data: dict[str, Any] = {}
        self.history: list[tuple[str, Any, str]] = []  # (field_name, value, prompt)
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


def visit_to_dict(visit: OnsenVisit) -> dict:
    """
    Convert an OnsenVisit ORM object to a dictionary for editing.
    Handles special conversions like visit_time → visit_date + visit_time_str.
    """
    data = {}

    # Copy all non-None attributes
    for column in visit.__table__.columns:
        value = getattr(visit, column.name)
        if value is not None:
            data[column.name] = value

    # Special handling for visit_time: split into date and time strings
    if "visit_time" in data and data["visit_time"]:
        visit_dt = data["visit_time"]
        data["visit_date"] = visit_dt
        data["visit_time_str"] = visit_dt.strftime("%H:%M")

    return data


def update_visit_from_dict(visit: OnsenVisit, data: dict) -> None:
    """
    Update an OnsenVisit ORM object from a dictionary.
    Handles special conversions like visit_date + visit_time_str → visit_time.
    """
    for key, value in data.items():
        # Skip internal fields that shouldn't be updated
        if key in ("id", "visit_date", "visit_time_str"):
            continue

        # Only update if the attribute exists on the model
        if hasattr(visit, key):
            setattr(visit, key, value)


def get_visit_steps(skip_onsen_selection: bool = False) -> list[dict]:
    """
    Get the complete list of steps for the visit workflow.

    Args:
        skip_onsen_selection: If True, skips the onsen_id step (for modify mode)

    Returns:
        List of step dictionaries with name, prompt, validator, processor, etc.
    """
    # Helper validation functions (defined inline for closure access)
    def validate_onsen_id(input_str: str) -> bool:
        """Validate onsen ID input - note: needs db access, handled by caller"""
        try:
            int(input_str)
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

    def validate_date(input_str: str) -> bool:
        """Validate date input (YYYY-MM-DD, or shortcuts: 0/empty for today, 1 for tomorrow)."""
        if not input_str or input_str == "0":
            return True  # Empty or "0" = today
        if input_str == "1":
            return True  # "1" = tomorrow
        try:
            datetime.strptime(input_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def validate_time(input_str: str) -> bool:
        """Validate time input (HH:MM or empty for now)."""
        if not input_str:
            return True  # Empty = now
        try:
            datetime.strptime(input_str, "%H:%M")
            return True
        except ValueError:
            return False

    steps = []

    # Onsen selection step (only if not skipped)
    if not skip_onsen_selection:
        steps.append({
            "name": "onsen_id",
            "prompt": "Enter the onsen ID: ",
            "validator": validate_onsen_id,
            "processor": lambda x: int(x),
            "step_title": "Select the onsen",
        })

    # All other steps (full workflow continues below)
    steps.extend([
        {
            "name": "entry_fee_yen",
            "prompt": "What was the entry fee in yen? (0 if free): ",
            "validator": validate_integer,
            "processor": lambda x: int(x) if x else None,
            "step_title": "Basic visit information",
        },
        {
            "name": "payment_method",
            "prompt": "Payment method (cash/card/other): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Basic visit information",
        },
        {
            "name": "visit_date",
            "prompt": "Enter visit date (0 or Enter for today, 1 for tomorrow, or YYYY-MM-DD): ",
            "validator": validate_date,
            "processor": lambda x: (
                datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if not x or x == "0"
                else (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                if x == "1"
                else datetime.strptime(x, "%Y-%m-%d")
            ),
            "step_title": "Basic visit information",
        },
        {
            "name": "visit_time_str",
            "prompt": "Enter visit time (HH:MM or Enter for now): ",
            "validator": validate_time,
            "processor": lambda x: x,  # Store as string, will combine with date later
            "step_title": "Basic visit information",
        },
        {
            "name": "weather",
            "prompt": "Weather conditions (sunny/cloudy/rainy/snowy/other): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Basic visit information",
        },
        {
            "name": "time_of_day",
            "prompt": "Time of day (morning/afternoon/evening): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Basic visit information",
        },
        {
            "name": "temperature_outside_celsius",
            "prompt": "Temperature outside (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "step_title": "Basic visit information",
        },
        {
            "name": "stay_length_minutes",
            "prompt": "How long did you stay? (minutes): ",
            "validator": validate_integer,
            "processor": lambda x: int(x) if x else None,
            "step_title": "Basic visit information",
        },
        {
            "name": "visited_with",
            "prompt": "Who did you visit with? (friend/group/alone/other): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Travel information",
        },
        {
            "name": "travel_mode",
            "prompt": "Travel mode (car/train/bus/walk/run/bike/other): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Travel information",
        },
        {
            "name": "travel_time_minutes",
            "prompt": "Travel time in minutes: ",
            "validator": validate_integer,
            "processor": lambda x: int(x) if x else None,
            "step_title": "Travel information",
        },
        {
            "name": "accessibility_rating",
            "prompt": "Accessibility rating (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "step_title": "Facility ratings",
        },
        {
            "name": "cleanliness_rating",
            "prompt": "Cleanliness rating (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "step_title": "Facility ratings",
        },
        {
            "name": "navigability_rating",
            "prompt": "Navigability rating (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "step_title": "Facility ratings",
        },
        {
            "name": "view_rating",
            "prompt": "View rating (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "step_title": "Facility ratings",
        },
        {
            "name": "atmosphere_rating",
            "prompt": "Atmosphere rating (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "step_title": "Facility ratings",
        },
        {
            "name": "main_bath_type",
            "prompt": "Main bath type (open air/indoor/other): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Main bath information",
        },
        {
            "name": "main_bath_temperature",
            "prompt": "Main bath temperature (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "step_title": "Main bath information",
        },
        {
            "name": "water_color",
            "prompt": "Water color (clear/brown/green/other): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Main bath information",
        },
        {
            "name": "smell_intensity_rating",
            "prompt": "Smell intensity rating (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "step_title": "Main bath information",
        },
        {
            "name": "changing_room_cleanliness_rating",
            "prompt": "Changing room cleanliness rating (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "step_title": "Changing room and facilities",
        },
        {
            "name": "locker_availability_rating",
            "prompt": "Locker aviailability rating (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "step_title": "Changing room and facilities",
        },
        {
            "name": "had_soap",
            "prompt": "Was soap available? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "step_title": "Changing room and facilities",
        },
        {
            "name": "had_sauna",
            "prompt": "Was there a sauna at the facility? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "step_title": "Sauna information",
        },
        {
            "name": "sauna_visited",
            "prompt": "Did you use the sauna? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "condition": lambda session: session.visit_data.get("had_sauna", False),
            "step_title": "Sauna information",
        },
        {
            "name": "sauna_duration_minutes",
            "prompt": "How long did you stay in the sauna? (minutes): ",
            "validator": lambda x: not x or validate_integer(x),
            "processor": lambda x: int(x) if x else None,
            "condition": lambda session: session.visit_data.get("had_sauna", False)
            and session.visit_data.get("sauna_visited", False),
            "step_title": "Sauna information",
        },
        {
            "name": "sauna_temperature",
            "prompt": "What was the temperature of the sauna? (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "condition": lambda session: session.visit_data.get("had_sauna", False)
            and session.visit_data.get("sauna_visited", False),
            "step_title": "Sauna information",
        },
        {
            "name": "sauna_steam",
            "prompt": "Did the sauna have steam? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "condition": lambda session: session.visit_data.get("had_sauna", False)
            and session.visit_data.get("sauna_visited", False),
            "step_title": "Sauna information",
        },
        {
            "name": "sauna_rating",
            "prompt": "How do you rate the sauna? (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "condition": lambda session: session.visit_data.get("had_sauna", False)
            and session.visit_data.get("sauna_visited", False),
            "step_title": "Sauna information",
        },
        {
            "name": "had_outdoor_bath",
            "prompt": "Was there an outdoor bath at the facility? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "step_title": "Outdoor bath information",
        },
        {
            "name": "outdoor_bath_visited",
            "prompt": "Did you use the outdoor bath? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "condition": lambda session: session.visit_data.get(
                "had_outdoor_bath", True
            ),
            "step_title": "Outdoor bath information",
        },
        {
            "name": "outdoor_bath_temperature",
            "prompt": "Outdoor bath temperature (°C): ",
            "validator": lambda x: not x or validate_float(x),
            "processor": lambda x: float(x) if x else None,
            "condition": lambda session: session.visit_data.get(
                "had_outdoor_bath", False
            )
            and session.visit_data.get("outdoor_bath_visited", False),
            "step_title": "Outdoor bath information",
        },
        {
            "name": "outdoor_bath_rating",
            "prompt": "Outdoor bath rating (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "condition": lambda session: session.visit_data.get(
                "had_outdoor_bath", False
            )
            and session.visit_data.get("outdoor_bath_visited", False),
            "step_title": "Outdoor bath information",
        },
        {
            "name": "had_rest_area",
            "prompt": "Was there a rest area? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "step_title": "Rest area and food",
        },
        {
            "name": "rest_area_used",
            "prompt": "Did you use the rest area? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "condition": lambda session: session.visit_data.get("had_rest_area", False),
            "step_title": "Rest area and food",
        },
        {
            "name": "rest_area_rating",
            "prompt": "How do you rate the rest area? (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "condition": lambda session: session.visit_data.get("had_rest_area", False)
            and session.visit_data.get("rest_area_used", False),
            "step_title": "Rest area and food",
        },
        {
            "name": "had_food_service",
            "prompt": "Was there food service? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "step_title": "Rest area and food",
        },
        {
            "name": "food_service_used",
            "prompt": "Did you use the food service? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "condition": lambda session: session.visit_data.get(
                "had_food_service", True
            ),
            "step_title": "Rest area and food",
        },
        {
            "name": "food_quality_rating",
            "prompt": "How do you rate the food quality? (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "condition": lambda session: session.visit_data.get(
                "had_food_service", False
            )
            and session.visit_data.get("food_service_used", False),
            "step_title": "Rest area and food",
        },
        {
            "name": "massage_chair_available",
            "prompt": "Was there a massage chair? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "step_title": "Rest area and food",
        },
        {
            "name": "crowd_level",
            "prompt": "Crowd level (busy/moderate/quiet/empty): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Crowd and mood",
        },
        {
            "name": "interacted_with_locals",
            "prompt": "Did you interact with locals inside the onsen? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "condition": lambda session: session.visit_data.get("crowd_level", "").lower() != "empty",
            "step_title": "Crowd and mood",
        },
        {
            "name": "local_interaction_quality_rating",
            "prompt": "How pleasant was the interaction with locals? (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "condition": lambda session: session.visit_data.get("interacted_with_locals", False),
            "step_title": "Crowd and mood",
        },
        {
            "name": "pre_visit_mood",
            "prompt": "Mood before visit (relaxed/stressed/anxious/other): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Crowd and mood",
        },
        {
            "name": "post_visit_mood",
            "prompt": "Mood after visit (relaxed/stressed/anxious/other): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Crowd and mood",
        },
        {
            "name": "energy_level_change",
            "prompt": "Energy level change (-5 to +5, negative = less energy): ",
            "validator": lambda x: not x or validate_integer(x) and -5 <= int(x) <= 5,
            "processor": lambda x: int(x) if x else None,
            "step_title": "Health and energy",
        },
        {
            "name": "hydration_level",
            "prompt": "Hydration level before entering (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "step_title": "Health and energy",
        },
        {
            "name": "multi_onsen_day",
            "prompt": "Was this a part of a multi-onsen day? (y/n): ",
            "validator": validate_yes_no,
            "processor": lambda x: x.lower() in ["y", "yes"],
            "step_title": "Multi-onsen day",
        },
        {
            "name": "visit_order",
            "prompt": "Visit order (1st, 2nd, etc.): ",
            "validator": lambda x: not x or validate_integer(x) and int(x) > 0,
            "processor": lambda x: int(x) if x else None,
            "condition": lambda session: session.visit_data.get(
                "multi_onsen_day", False
            ),
            "step_title": "Multi-onsen day",
        },
        {
            "name": "previous_location",
            "prompt": "What is the ID of the previous onsen visit?: ",
            "validator": lambda x: not x or validate_integer(x) and int(x) > 0,
            "processor": lambda x: int(x) if x else None,
            "condition": lambda session: session.visit_data.get(
                "multi_onsen_day", False
            ),
            "step_title": "Multi-onsen day",
        },
        {
            "name": "next_location",
            "prompt": "What is the ID of the next onsen visit?: ",
            "validator": lambda x: not x or validate_integer(x) and int(x) > 0,
            "processor": lambda x: int(x) if x else None,
            "condition": lambda session: session.visit_data.get(
                "multi_onsen_day", False
            ),
            "step_title": "Multi-onsen day",
        },
        {
            "name": "personal_rating",
            "prompt": "Personal overall rating (1-10): ",
            "validator": lambda x: not x or validate_rating(x),
            "processor": lambda x: int(x) if x else None,
            "step_title": "Personal rating",
        },
        {
            "name": "notes",
            "prompt": "Any additional notes about this visit? (optional): ",
            "validator": lambda x: True,
            "processor": lambda x: x if x else None,
            "step_title": "Additional notes",
        },
    ])

    return steps


def execute_workflow(session: InteractiveSession, steps: list[dict], db=None) -> InteractiveSession:
    """
    Execute the step-by-step workflow for collecting visit data.

    Args:
        session: InteractiveSession instance (may be pre-populated for modify mode)
        steps: List of step dictionaries from get_visit_steps()
        db: Optional database session for onsen_id validation

    Returns:
        The session with visit_data populated
    """
    current_step_index = 0
    last_step_title = None
    step_number = 1

    while current_step_index < len(steps):
        step = steps[current_step_index]

        # Print step title if it changed
        if step["step_title"] != last_step_title:
            print(f"\nStep {step_number}: {step['step_title']}")
            last_step_title = step["step_title"]
            step_number += 1

        if "condition" in step and not step["condition"](session):
            current_step_index += 1
            continue

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

            # Special validation for onsen_id (requires db access)
            if step["name"] == "onsen_id" and db:
                try:
                    onsen_id = int(user_input)
                    onsen = db.query(Onsen).filter(Onsen.id == onsen_id).first()
                    if not onsen:
                        print(f"No onsen found with ID {onsen_id}")
                        continue
                    print(f"Found onsen: {onsen.name}")
                except ValueError:
                    print("Invalid onsen ID")
                    continue

            # Validate input (allow empty input for all fields)
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

    # Combine visit_date and visit_time_str into visit_time
    print("\nProcessing visit data...")
    if "visit_date" in session.visit_data and "visit_time_str" in session.visit_data:
        visit_date = session.visit_data.pop("visit_date")
        visit_time_str = session.visit_data.pop("visit_time_str")

        if not visit_time_str:
            # No time specified, use current time
            now = datetime.now()
            visit_time = visit_date.replace(
                hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond
            )
        else:
            # Parse time and combine with date
            time_obj = datetime.strptime(visit_time_str, "%H:%M")
            visit_time = visit_date.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)

        session.visit_data["visit_time"] = visit_time

    return session


def add_visit_interactive(args: argparse.Namespace) -> None:
    """
    Interactive version of add_visit that guides users through a series of questions.
    Supports navigation back to previous answers.
    """
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )

    # Show banner for destructive operation
    show_database_banner(config, operation="Add visit")

    print("🌊 Welcome to the Interactive Onsen Visit Recorder! 🌊")
    print("I'll guide you through recording your onsen visit experience.")
    print("💡 Tip: Type 'back' to go back one step, or 'back N' to go back N steps.\n")

    # Create session and get steps
    session = InteractiveSession()
    steps = get_visit_steps(skip_onsen_selection=False)

    # Execute workflow with database for onsen validation
    with get_db(url=config.url) as db:
        session = execute_workflow(session, steps, db=db)

    # Save the visit
    print("Saving visit data...")
    with get_db(url=config.url) as db:
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

