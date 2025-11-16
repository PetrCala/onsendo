"""Apple Reminders integration for macOS using AppleScript."""

import os
import platform
import stat
import subprocess
from datetime import datetime
from loguru import logger


def create_reminder(
    title: str, reminder_datetime: datetime, body: str | None = None
) -> bool:
    """
    Create a reminder in Apple Reminders app using AppleScript.

    Args:
        title: The reminder title/name
        reminder_datetime: When the reminder should trigger
        body: Optional reminder body/notes with additional details

    Returns:
        True if reminder was created successfully, False otherwise

    Raises:
        RuntimeError: If not running on macOS
    """
    # Check if running on macOS
    if platform.system() != "Darwin":
        logger.error("Apple Reminders integration only works on macOS")
        raise RuntimeError("Apple Reminders is only available on macOS")

    try:
        # Extract date components for AppleScript
        # Construct date from components to avoid locale-specific parsing issues
        year = reminder_datetime.year
        month = reminder_datetime.month
        day = reminder_datetime.day
        hour = reminder_datetime.hour
        minute = reminder_datetime.minute
        second = reminder_datetime.second

        # Escape special characters in title and body for AppleScript
        escaped_title = title.replace('"', '\\"').replace("\\", "\\\\")

        # Build properties dictionary
        if body:
            escaped_body = body.replace('"', '\\"').replace("\\", "\\\\")
            properties = (
                f'{{name:"{escaped_title}", due date:theDate, body:"{escaped_body}"}}'
            )
        else:
            properties = f'{{name:"{escaped_title}", due date:theDate}}'

        # Construct AppleScript command
        # Build date from components for reliable cross-locale operation
        applescript = f"""
        set theDate to current date
        set year of theDate to {year}
        set month of theDate to {month}
        set day of theDate to {day}
        set hours of theDate to {hour}
        set minutes of theDate to {minute}
        set seconds of theDate to {second}

        tell application "Reminders"
            tell list "Reminders" -- Default list
                make new reminder with properties {properties}
            end tell
        end tell
        """

        # Execute AppleScript via osascript
        subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )

        logger.debug(f"Successfully created reminder: {title} for {reminder_datetime}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"AppleScript execution failed: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("AppleScript execution timed out")
        return False
    except (OSError, ValueError) as e:
        logger.error(f"Unexpected error creating reminder: {e}")
        return False


def generate_reminder_script(
    title: str, reminder_datetime: datetime, script_path: str, body: str | None = None
) -> None:
    """
    Generate a shell script (.command file) that creates an Apple Reminder.

    This creates an executable script that can be clicked to create the reminder.
    The .command extension makes it executable via Finder on macOS.

    Args:
        title: The reminder title/name
        reminder_datetime: When the reminder should trigger
        script_path: Absolute path where the script should be saved
        body: Optional reminder body/notes with additional details

    Raises:
        RuntimeError: If not running on macOS
        OSError: If the script file cannot be created or made executable
    """
    # Check if running on macOS
    if platform.system() != "Darwin":
        logger.warning("Reminder script generation skipped (not on macOS)")
        return

    # Extract date components for AppleScript
    year = reminder_datetime.year
    month = reminder_datetime.month
    day = reminder_datetime.day
    hour = reminder_datetime.hour
    minute = reminder_datetime.minute
    second = reminder_datetime.second

    # Escape special characters for shell script
    escaped_title = title.replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")

    # Build properties for AppleScript
    if body:
        escaped_body = (
            body.replace('"', '\\"')
            .replace("$", "\\$")
            .replace("`", "\\`")
            .replace("\n", "\\n")
        )
        properties_line = (
            f'{{name:"{escaped_title}", due date:theDate, body:"{escaped_body}"}}'
        )
    else:
        properties_line = f'{{name:"{escaped_title}", due date:theDate}}'

    # Create shell script content
    script_content = f"""#!/bin/bash
# Onsen Reminder Creation Script
# This script creates a reminder in Apple Reminders

# Create the reminder
osascript -e '
set theDate to current date
set year of theDate to {year}
set month of theDate to {month}
set day of theDate to {day}
set hours of theDate to {hour}
set minutes of theDate to {minute}
set seconds of theDate to {second}

tell application "Reminders"
    tell list "Reminders"
        make new reminder with properties {properties_line}
    end tell
end tell
'

# Check if it succeeded
if [ $? -eq 0 ]; then
    # Show success notification
    osascript -e 'display notification "Reminder created: {title}" with title "Onsen Recommendation"'
    echo "✅ Success! Reminder created: {title}"
else
    # Show error notification
    osascript -e 'display notification "Failed to create reminder. Check permissions." with title "Onsen Recommendation"'
    echo "❌ Error: Failed to create reminder"
    echo "Please check that you have granted permission to access Reminders"
fi

# Keep terminal window open for 3 seconds so user can see the result
sleep 3
"""

    # Write the script file
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        # Make it executable
        os.chmod(
            script_path,
            os.stat(script_path).st_mode | stat.S_IEXEC | stat.S_IXUSR | stat.S_IXGRP,
        )

        logger.debug(f"Generated reminder script at: {script_path}")

    except OSError as e:
        logger.error(f"Failed to create reminder script: {e}")
        raise


def is_reminders_available() -> bool:
    """
    Check if Apple Reminders integration is available.

    Returns:
        True if running on macOS, False otherwise
    """
    return platform.system() == "Darwin"


def format_onsen_details_for_reminder(
    recommendations: list[tuple], location_name: str
) -> str:
    """
    Format onsen recommendation details for reminder body.

    Creates a formatted text description with details about each recommended onsen,
    similar to the information shown in the interactive map popup.

    Args:
        recommendations: List of tuples (onsen, distance_km, metadata)
        location_name: Name of the user's location

    Returns:
        Formatted string with onsen details for reminder body
    """
    # pylint: disable=too-complex
    # This function formats many optional fields, complexity is unavoidable
    lines = []

    # Header
    lines.append(f"📍 From: {location_name}")
    lines.append("")

    # Add details for each recommendation
    for i, (onsen, distance, metadata) in enumerate(recommendations, 1):
        if i > 1:
            lines.append("")
            lines.append("-" * 40)
            lines.append("")

        # Onsen name and ranking
        lines.append(f"{i}. {onsen.name}")

        # Ban number
        if onsen.ban_number:
            lines.append(f"   BAN: {onsen.ban_number}")

        # Distance and category
        distance_cat = metadata.get("distance_category", "N/A")
        lines.append(f"   Distance: {distance:.1f} km ({distance_cat})")

        # Address
        if onsen.address:
            lines.append(f"   Address: {onsen.address}")

        # Coordinates
        if onsen.latitude and onsen.longitude:
            lines.append(f"   Coordinates: {onsen.latitude:.6f}, {onsen.longitude:.6f}")

        # Operating hours
        if onsen.usage_time:
            lines.append(f"   Hours: {onsen.usage_time}")

        # Closed days
        if onsen.closed_days:
            lines.append(f"   Closed: {onsen.closed_days}")

        # Admission fee
        if onsen.admission_fee:
            lines.append(f"   Fee: {onsen.admission_fee}")

        # Spring quality
        if onsen.spring_quality:
            lines.append(f"   Spring: {onsen.spring_quality}")

        # Parking
        if onsen.parking:
            lines.append(f"   Parking: {onsen.parking}")

        # Status information
        status_parts = []
        if metadata.get("is_available"):
            status_parts.append("✅ Available")
        else:
            status_parts.append("🔒 Closed")

        if metadata.get("has_been_visited"):
            status_parts.append("✓ Visited")

        if metadata.get("stay_restricted"):
            status_parts.append("🏨 Stay-restricted")

        if status_parts:
            lines.append(f"   Status: {', '.join(status_parts)}")

        # Stay restriction notes
        if metadata.get("stay_restriction_notes"):
            for note in metadata["stay_restriction_notes"]:
                lines.append(f"   Note: {note}")

        # Remarks
        if onsen.remarks:
            lines.append(f"   Remarks: {onsen.remarks}")

        # Google Maps link
        if metadata.get("google_maps_link"):
            lines.append(f"   Maps: {metadata['google_maps_link']}")

    return "\n".join(lines)
