"""
Reusable datetime input utilities for CLI interactive workflows.

This module provides helper functions for collecting date and time input
from users with convenient shortcuts like "today", "tomorrow", and "now".
It also provides utilities for deriving time-of-day categories from datetime objects.
"""
# pylint: disable=bad-builtin  # input() is appropriate for CLI interaction

from datetime import datetime, timedelta
from typing import Optional


def get_date_input(prompt: str = "Enter date", allow_shortcuts: bool = True) -> Optional[datetime]:
    """
    Get date input from user with optional shortcuts.

    Args:
        prompt: The prompt to display to the user
        allow_shortcuts: If True, allows shortcuts (0/empty for today, 1 for tomorrow)

    Returns:
        datetime object with date (time set to 00:00:00), or None if cancelled

    Example:
        >>> date = get_date_input("Visit date")
        # User can enter:
        # - Nothing or "0" for today
        # - "1" for tomorrow
        # - "2025-10-28" for specific date
    """
    if allow_shortcuts:
        full_prompt = f"{prompt} (0 or Enter for today, 1 for tomorrow, or YYYY-MM-DD): "
    else:
        full_prompt = f"{prompt} (YYYY-MM-DD): "

    while True:
        user_input = input(full_prompt).strip()

        if not user_input:
            if allow_shortcuts:
                # Empty input = today
                return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                print("Date is required. Please enter a date.")
                continue

        if allow_shortcuts:
            # Check for shortcuts
            if user_input == "0":
                return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            elif user_input == "1":
                tomorrow = datetime.now() + timedelta(days=1)
                return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)

        # Try to parse as YYYY-MM-DD
        try:
            parsed_date = datetime.strptime(user_input, "%Y-%m-%d")
            return parsed_date
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")


def get_time_input(prompt: str = "Enter time", allow_now: bool = True) -> Optional[tuple[int, int]]:
    """
    Get time input from user.

    Args:
        prompt: The prompt to display to the user
        allow_now: If True, allows empty input for current time

    Returns:
        Tuple of (hour, minute) as integers, or None for "now" when allow_now=True

    Example:
        >>> time_tuple = get_time_input("Visit time")
        # User can enter:
        # - Nothing for now (if allow_now=True)
        # - "18:30" for specific time
    """
    if allow_now:
        full_prompt = f"{prompt} (HH:MM or Enter for now): "
    else:
        full_prompt = f"{prompt} (HH:MM): "

    while True:
        user_input = input(full_prompt).strip()

        if not user_input:
            if allow_now:
                # Empty input = now (return None to signal current time)
                return None
            else:
                print("Time is required. Please enter a time.")
                continue

        # Try to parse as HH:MM
        try:
            parsed_time = datetime.strptime(user_input, "%H:%M")
            return (parsed_time.hour, parsed_time.minute)
        except ValueError:
            print("Invalid time format. Please use HH:MM format (e.g., 18:30).")


def combine_date_time(
    date_obj: Optional[datetime],
    time_tuple: Optional[tuple[int, int]]
) -> datetime:
    """
    Combine date and time into a single datetime object.

    Args:
        date_obj: datetime object with date (time component ignored)
        time_tuple: Tuple of (hour, minute), or None for current time

    Returns:
        datetime object combining the date and time

    Example:
        >>> date = datetime(2025, 10, 28)
        >>> time = (18, 30)
        >>> result = combine_date_time(date, time)
        # Result: datetime(2025, 10, 28, 18, 30)
    """
    if date_obj is None:
        # If no date provided, use today
        date_obj = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if time_tuple is None:
        # If no time provided, use current time
        now = datetime.now()
        return date_obj.replace(hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)

    # Combine date from date_obj with time from time_tuple
    hour, minute = time_tuple
    return date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)


def get_datetime_input(
    date_prompt: str = "Enter date",
    time_prompt: str = "Enter time",
    allow_date_shortcuts: bool = True,
    allow_now: bool = True
) -> datetime:
    """
    Get both date and time from user in two separate questions.

    This is a convenience function that combines get_date_input() and get_time_input().

    Args:
        date_prompt: Prompt for date input
        time_prompt: Prompt for time input
        allow_date_shortcuts: If True, allows date shortcuts (0/1/empty)
        allow_now: If True, allows empty time input for current time

    Returns:
        datetime object combining user's date and time input

    Example:
        >>> dt = get_datetime_input("Visit date", "Visit time")
        # Prompts user for date first, then time
        # Returns combined datetime
    """
    date_obj = get_date_input(date_prompt, allow_shortcuts=allow_date_shortcuts)
    time_tuple = get_time_input(time_prompt, allow_now=allow_now)
    return combine_date_time(date_obj, time_tuple)


def get_time_of_day_from_datetime(dt: datetime) -> str:
    """
    Derive time of day category from a datetime object.

    Args:
        dt: datetime object to categorize

    Returns:
        One of: "morning", "afternoon", "evening"

    Time ranges:
        - morning: 05:00 - 11:59
        - afternoon: 12:00 - 17:59
        - evening: 18:00 - 04:59

    Example:
        >>> dt = datetime(2025, 10, 30, 8, 30)
        >>> get_time_of_day_from_datetime(dt)
        'morning'
    """
    hour = dt.hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"
