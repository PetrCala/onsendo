"""
cli_commands.py

Defines CLI commands using dataclasses for better structure and type safety.
"""

import argparse
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from src.const import CONST
import src.cli.commands as commands


@dataclass
class ArgumentConfig:
    """Configuration for a single CLI argument."""

    type: "type | None" = None
    required: bool = False
    default: Any = None
    help: Optional[str] = None
    action: Optional[str] = None


@dataclass
class CommandConfig:
    """Configuration for a CLI command."""

    func: Callable[[argparse.Namespace], None]
    help: str
    args: Dict[str, ArgumentConfig]


# Define all CLI commands
CLI_COMMANDS = {
    "init-db": CommandConfig(
        func=commands.init_db,
        help="Initialize the database.",
        args={
            "force": ArgumentConfig(action="store_true"),
        },
    ),
    "print-onsen-summary": CommandConfig(
        func=commands.print_onsen_summary,
        help="Print a summary for an onsen by ID or ban number.",
        args={
            "onsen_id": ArgumentConfig(type=int, required=False, help="Onsen ID"),
            "ban_number": ArgumentConfig(
                type=str, required=False, help="Onsen BAN number"
            ),
            "name": ArgumentConfig(
                type=str, required=False, help="Onsen name (exact match)"
            ),
        },
    ),
    "fill-db": CommandConfig(
        func=commands.fill_db,
        help="Fill the database with onsen data.",
        args={
            "json_path": ArgumentConfig(type=str, required=True),
        },
    ),
    "add-onsen": CommandConfig(
        func=commands.add_onsen,
        help="Add a new onsen.",
        args={
            "ban_number": ArgumentConfig(type=str, required=True),
            "name": ArgumentConfig(type=str, required=True),
            "address": ArgumentConfig(type=str, default=""),
        },
    ),
    "add-visit": CommandConfig(
        func=commands.add_visit,
        help="Add a new onsen visit.",
        args={
            # Interactive mode flag
            "interactive": ArgumentConfig(
                action="store_true", help="Run in interactive mode"
            ),
            # Required fields (only required when not in interactive mode)
            "onsen_id": ArgumentConfig(type=int, required=False),
            # Integer fields
            "entry_fee_yen": ArgumentConfig(type=int, default=0),
            "stay_length_minutes": ArgumentConfig(type=int, default=0),
            "travel_time_minutes": ArgumentConfig(type=int, default=0),
            "accessibility_rating": ArgumentConfig(type=int, default=0),
            "excercise_length_minutes": ArgumentConfig(type=int, default=0),
            "cleanliness_rating": ArgumentConfig(type=int, default=0),
            "navigability_rating": ArgumentConfig(type=int, default=0),
            "view_rating": ArgumentConfig(type=int, default=0),
            "main_bath_temperature": ArgumentConfig(type=float, default=0),
            "smell_intensity_rating": ArgumentConfig(type=int, default=0),
            "changing_room_cleanliness_rating": ArgumentConfig(type=int, default=0),
            "locker_availability_rating": ArgumentConfig(type=int, default=0),
            "rest_area_rating": ArgumentConfig(type=int, default=0),
            "food_quality_rating": ArgumentConfig(type=int, default=0),
            "sauna_temperature": ArgumentConfig(type=float, default=0),
            "sauna_duration_minutes": ArgumentConfig(type=int, default=0),
            "sauna_rating": ArgumentConfig(type=int, default=0),
            "outdoor_bath_temperature": ArgumentConfig(type=float, default=0),
            "outdoor_bath_rating": ArgumentConfig(type=int, default=0),
            "energy_level_change": ArgumentConfig(type=int, default=0),
            "hydration_level": ArgumentConfig(type=int, default=0),
            "previous_location": ArgumentConfig(type=int, default=0),
            "next_location": ArgumentConfig(type=int, default=0),
            "visit_order": ArgumentConfig(type=int, default=0),
            "atmosphere_rating": ArgumentConfig(type=int, default=0),
            "personal_rating": ArgumentConfig(type=int, default=0),
            # Float fields
            "temperature_outside_celsius": ArgumentConfig(type=float, default=0),
            # String fields
            "payment_method": ArgumentConfig(type=str, default=""),
            "weather": ArgumentConfig(type=str, default=""),
            "time_of_day": ArgumentConfig(type=str, default=""),
            "visited_with": ArgumentConfig(type=str, default=""),
            "travel_mode": ArgumentConfig(type=str, default=""),
            "excercise_type": ArgumentConfig(type=str, default=""),
            "crowd_level": ArgumentConfig(type=str, default=""),
            "heart_rate_data": ArgumentConfig(type=str, default=""),
            "main_bath_type": ArgumentConfig(type=str, default=""),
            "main_bath_water_type": ArgumentConfig(type=str, default=""),
            "water_color": ArgumentConfig(type=str, default=""),
            "pre_visit_mood": ArgumentConfig(type=str, default=""),
            "post_visit_mood": ArgumentConfig(type=str, default=""),
            # Special fields
            "visit_time": ArgumentConfig(help="YYYY-MM-DD HH:MM", default=None),
            # Boolean fields
            "excercise_before_onsen": ArgumentConfig(action="store_true"),
            "had_soap": ArgumentConfig(action="store_true"),
            "had_sauna": ArgumentConfig(action="store_true"),
            "had_outdoor_bath": ArgumentConfig(action="store_true"),
            "had_rest_area": ArgumentConfig(action="store_true"),
            "had_food_service": ArgumentConfig(action="store_true"),
            "massage_chair_available": ArgumentConfig(action="store_true"),
            "sauna_visited": ArgumentConfig(action="store_true"),
            "sauna_steam": ArgumentConfig(action="store_true"),
            "outdoor_bath_visited": ArgumentConfig(action="store_true"),
            "multi_onsen_day": ArgumentConfig(action="store_true"),
        },
    ),
    "add-visit-interactive": CommandConfig(
        func=lambda args: commands.add_visit_interactive(),
        help="Add a new onsen visit using an interactive questionnaire.",
        args={},
    ),
    "scrape-onsen-data": CommandConfig(
        func=commands.scrape_onsen_data,
        help="Scrape onsen data from the web.",
        args={
            "fetch_mapping_only": ArgumentConfig(
                action="store_true",
                help="Only fetch the onsen mapping (list of all onsens), skip individual scraping",
            ),
            "scrape_individual_only": ArgumentConfig(
                action="store_true",
                help="Only scrape individual onsen pages, skip fetching the mapping (requires existing mapping file)",
            ),
        },
    ),
    # Location management commands
    "add-location": CommandConfig(
        func=commands.add_location,
        help="Add a new location for distance calculations.",
        args={
            "name": ArgumentConfig(type=str, required=True, help="Location name"),
            "latitude": ArgumentConfig(
                type=float, required=True, help="Latitude in decimal degrees"
            ),
            "longitude": ArgumentConfig(
                type=float, required=True, help="Longitude in decimal degrees"
            ),
            "description": ArgumentConfig(
                type=str, required=False, help="Optional description"
            ),
        },
    ),
    "add-location-interactive": CommandConfig(
        func=lambda args: commands.add_location_interactive(),
        help="Add a new location using interactive prompts.",
        args={},
    ),
    "list-locations": CommandConfig(
        func=commands.list_locations,
        help="List all locations in the database.",
        args={},
    ),
    "delete-location": CommandConfig(
        func=commands.delete_location,
        help="Delete a location from the database.",
        args={
            "identifier": ArgumentConfig(
                type=str, required=True, help="Location ID or name"
            ),
            "force": ArgumentConfig(
                action="store_true", help="Skip confirmation prompt"
            ),
        },
    ),
    "delete-location-interactive": CommandConfig(
        func=lambda args: commands.delete_location_interactive(),
        help="Delete a location using interactive prompts.",
        args={},
    ),
    "modify-location": CommandConfig(
        func=commands.modify_location,
        help="Modify an existing location.",
        args={
            "identifier": ArgumentConfig(
                type=str, required=True, help="Location ID or name"
            ),
            "name": ArgumentConfig(type=str, required=False, help="New location name"),
            "latitude": ArgumentConfig(type=float, required=False, help="New latitude"),
            "longitude": ArgumentConfig(
                type=float, required=False, help="New longitude"
            ),
            "description": ArgumentConfig(
                type=str, required=False, help="New description"
            ),
        },
    ),
    "modify-location-interactive": CommandConfig(
        func=lambda args: commands.modify_location_interactive(),
        help="Modify a location using interactive prompts.",
        args={},
    ),
    # Recommendation commands
    "recommend-onsen": CommandConfig(
        func=commands.recommend_onsen,
        help="Get onsen recommendations based on location and criteria.",
        args={
            "location": ArgumentConfig(
                type=str, required=True, help="Location ID or name"
            ),
            "time": ArgumentConfig(
                type=str, required=False, help="Target time (YYYY-MM-DD HH:MM)"
            ),
            "distance": ArgumentConfig(
                type=str,
                default="medium",
                help="Distance category (very_close, close, medium, far)",
            ),
            "exclude_closed": ArgumentConfig(
                action="store_true", default=True, help="Exclude closed onsens"
            ),
            "exclude_visited": ArgumentConfig(
                action="store_true", default=False, help="Exclude visited onsens"
            ),
            "min_hours_after": ArgumentConfig(
                type=int,
                required=False,
                default=2,
                help="Minimum hours onsen should be open after target time (0 to disable)",
            ),
            "limit": ArgumentConfig(
                type=int, required=False, help="Maximum number of recommendations"
            ),
        },
    ),
    "recommend-onsen-interactive": CommandConfig(
        func=lambda args: commands.recommend_onsen_interactive(),
        help="Get onsen recommendations using interactive prompts.",
        args={},
    ),
}


def get_argument_kwargs(arg_config: ArgumentConfig) -> Dict[str, Any]:
    """Convert ArgumentConfig to argparse kwargs."""
    kwargs = {}

    if arg_config.type is not None:
        kwargs["type"] = arg_config.type
    if arg_config.required:
        kwargs["required"] = arg_config.required
    if arg_config.default is not None:
        kwargs["default"] = arg_config.default
    if arg_config.help is not None:
        kwargs["help"] = arg_config.help
    if arg_config.action is not None:
        kwargs["action"] = arg_config.action

    return kwargs
