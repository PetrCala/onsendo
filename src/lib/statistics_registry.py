"""Registry of available statistics for map visualization.

Defines metadata for all statistics that can be displayed on analysis maps,
including display names, field types, and formatting functions.
"""

from typing import Optional


class StatisticsRegistry:
    """Registry of available statistics with metadata."""

    # Define all available statistics from OnsenVisit model
    STATISTICS = [
        # Ratings (1-10 scale)
        {
            "field_name": "personal_rating",
            "display_name": "Personal Rating",
            "type": "rating",
            "description": "Overall personal rating (1-10)",
        },
        {
            "field_name": "accessibility_rating",
            "display_name": "Accessibility Rating",
            "type": "rating",
            "description": "Ease of finding/entering (1-10)",
        },
        {
            "field_name": "cleanliness_rating",
            "display_name": "Cleanliness Rating",
            "type": "rating",
            "description": "Cleanliness rating (1-10)",
        },
        {
            "field_name": "navigability_rating",
            "display_name": "Navigability Rating",
            "type": "rating",
            "description": "Ease of navigation inside (1-10)",
        },
        {
            "field_name": "view_rating",
            "display_name": "View Rating",
            "type": "rating",
            "description": "View quality rating (1-10)",
        },
        {
            "field_name": "atmosphere_rating",
            "display_name": "Atmosphere Rating",
            "type": "rating",
            "description": "Atmosphere rating (1-10)",
        },
        {
            "field_name": "rest_area_rating",
            "display_name": "Rest Area Rating",
            "type": "rating",
            "description": "Rest area quality (1-10)",
        },
        {
            "field_name": "food_quality_rating",
            "display_name": "Food Quality Rating",
            "type": "rating",
            "description": "Food service quality (1-10)",
        },
        {
            "field_name": "sauna_rating",
            "display_name": "Sauna Rating",
            "type": "rating",
            "description": "Sauna quality (1-10)",
        },
        {
            "field_name": "outdoor_bath_rating",
            "display_name": "Outdoor Bath Rating",
            "type": "rating",
            "description": "Outdoor bath quality (1-10)",
        },
        {
            "field_name": "smell_intensity_rating",
            "display_name": "Smell Intensity Rating",
            "type": "rating",
            "description": "Smell intensity (1-10)",
        },
        {
            "field_name": "changing_room_cleanliness_rating",
            "display_name": "Changing Room Cleanliness",
            "type": "rating",
            "description": "Changing room cleanliness (1-10)",
        },
        {
            "field_name": "locker_availability_rating",
            "display_name": "Locker Availability",
            "type": "rating",
            "description": "Locker availability (1-10)",
        },
        {
            "field_name": "local_interaction_quality_rating",
            "display_name": "Local Interaction Quality",
            "type": "rating",
            "description": "Quality of interaction with locals (1-10)",
        },
        {
            "field_name": "hydration_level",
            "display_name": "Hydration Level",
            "type": "rating",
            "description": "Hydration level before visit (1-10)",
        },
        # Durations (minutes)
        {
            "field_name": "stay_length_minutes",
            "display_name": "Stay Length",
            "type": "duration",
            "description": "Duration of stay (minutes)",
        },
        {
            "field_name": "travel_time_minutes",
            "display_name": "Travel Time",
            "type": "duration",
            "description": "Travel time to onsen (minutes)",
        },
        {
            "field_name": "sauna_duration_minutes",
            "display_name": "Sauna Duration",
            "type": "duration",
            "description": "Time spent in sauna (minutes)",
        },
        # Numeric values
        {
            "field_name": "entry_fee_yen",
            "display_name": "Entry Fee",
            "type": "numeric",
            "description": "Entry fee in yen",
        },
        {
            "field_name": "temperature_outside_celsius",
            "display_name": "Outside Temperature",
            "type": "numeric",
            "description": "Outside temperature (°C)",
        },
        {
            "field_name": "main_bath_temperature",
            "display_name": "Main Bath Temperature",
            "type": "numeric",
            "description": "Main bath temperature (°C)",
        },
        {
            "field_name": "sauna_temperature",
            "display_name": "Sauna Temperature",
            "type": "numeric",
            "description": "Sauna temperature (°C)",
        },
        {
            "field_name": "outdoor_bath_temperature",
            "display_name": "Outdoor Bath Temperature",
            "type": "numeric",
            "description": "Outdoor bath temperature (°C)",
        },
        {
            "field_name": "energy_level_change",
            "display_name": "Energy Level Change",
            "type": "numeric",
            "description": "Energy change (-5 to +5)",
        },
    ]

    @classmethod
    def get_all_statistics(cls) -> list[dict]:
        """Get all available statistics.

        Returns:
            List of statistic dictionaries with metadata
        """
        return cls.STATISTICS.copy()

    @classmethod
    def get_statistic(cls, field_name: str) -> Optional[dict]:
        """Get statistic metadata by field name.

        Args:
            field_name: The OnsenVisit field name

        Returns:
            Statistic dictionary if found, None otherwise
        """
        for stat in cls.STATISTICS:
            if stat["field_name"] == field_name:
                return stat.copy()
        return None

    @classmethod
    def get_statistic_display_name(cls, field_name: str) -> str:
        """Convert field name to human-readable display name.

        Args:
            field_name: The OnsenVisit field name

        Returns:
            Display name, or formatted field name if not found
        """
        stat = cls.get_statistic(field_name)
        if stat:
            return stat["display_name"]

        # Fallback: format field name
        return field_name.replace("_", " ").title()

    @classmethod
    def format_statistic_value(cls, field_name: str, value: float | int) -> str:
        """Format statistic value for display.

        Args:
            field_name: The OnsenVisit field name
            value: The value to format

        Returns:
            Formatted string representation
        """
        stat = cls.get_statistic(field_name)
        if not stat:
            return str(value)

        stat_type = stat.get("type", "numeric")

        if stat_type == "rating":
            # Ratings: show with 1 decimal place
            return f"{value:.1f}/10"

        if stat_type == "duration":
            # Durations: show as minutes
            return f"{int(value)} min"

        if stat_type == "numeric":
            # Numeric: check if it's currency
            if "fee" in field_name.lower() or "yen" in field_name.lower():
                return f"¥{int(value)}"
            # Check if it's temperature
            if "temperature" in field_name.lower():
                return f"{value:.1f}°C"
            # Default: show with appropriate precision
            if isinstance(value, float):
                return f"{value:.1f}"
            return str(int(value))

        return str(value)

    @classmethod
    def get_field_names(cls) -> list[str]:
        """Get list of all field names.

        Returns:
            List of field names
        """
        return [stat["field_name"] for stat in cls.STATISTICS]

