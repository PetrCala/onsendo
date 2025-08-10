"""
cli_commands.py

Defines CLI commands using dataclasses for better structure and type safety.
"""

import argparse
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
from src.const import CONST
import src.cli.commands.location as location_commands
import src.cli.commands.visit as visit_commands
import src.cli.commands.onsen as onsen_commands
import src.cli.commands.system as system_commands
import src.cli.commands.database as database_commands


@dataclass
class ArgumentConfig:
    """Configuration for a single CLI argument."""

    type: "type | None" = None
    required: bool = False
    default: Any = None
    help: Optional[str] = None
    action: Optional[str] = None
    positional: bool = False
    short: Optional[str] = None


@dataclass
class CommandConfig:
    """Configuration for a CLI command."""

    func: Callable[[argparse.Namespace], None]
    help: str
    args: Dict[str, ArgumentConfig]


# Define all CLI commands with new grouped structure
CLI_COMMANDS = {
    # Location commands
    "location-add": CommandConfig(
        func=location_commands.add_location,
        help="Add a new location for distance calculations.",
        args={
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "name": ArgumentConfig(type=str, required=False, help="Location name"),
            "latitude": ArgumentConfig(
                type=float, required=False, help="Latitude in decimal degrees"
            ),
            "longitude": ArgumentConfig(
                type=float, required=False, help="Longitude in decimal degrees"
            ),
            "description": ArgumentConfig(
                type=str, required=False, help="Optional description"
            ),
        },
    ),
    "location-list": CommandConfig(
        func=location_commands.list_locations,
        help="List all locations in the database.",
        args={},
    ),
    "location-delete": CommandConfig(
        func=location_commands.delete_location,
        help="Delete a location from the database.",
        args={
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "identifier": ArgumentConfig(
                type=str, required=False, help="Location ID or name"
            ),
            "force": ArgumentConfig(
                action="store_true", help="Skip confirmation prompt"
            ),
        },
    ),
    "location-modify": CommandConfig(
        func=location_commands.modify_location,
        help="Modify an existing location.",
        args={
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "identifier": ArgumentConfig(
                type=str, required=False, help="Location ID or name"
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
    # Visit commands
    "visit-add": CommandConfig(
        func=visit_commands.add_visit,
        help="Add a new onsen visit.",
        args={
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "onsen_id": ArgumentConfig(type=int, required=False),
            "entry_fee_yen": ArgumentConfig(type=int, default=0),
            "stay_length_minutes": ArgumentConfig(type=int, default=0),
            "travel_time_minutes": ArgumentConfig(type=int, default=0),
            "accessibility_rating": ArgumentConfig(type=int, default=0),
            "exercise_length_minutes": ArgumentConfig(type=int, default=0),
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
            "temperature_outside_celsius": ArgumentConfig(type=float, default=0),
            "payment_method": ArgumentConfig(type=str, default=""),
            "weather": ArgumentConfig(type=str, default=""),
            "time_of_day": ArgumentConfig(type=str, default=""),
            "visited_with": ArgumentConfig(type=str, default=""),
            "travel_mode": ArgumentConfig(type=str, default=""),
            "exercise_type": ArgumentConfig(type=str, default=""),
            "crowd_level": ArgumentConfig(type=str, default=""),
            "heart_rate_data": ArgumentConfig(type=str, default=""),
            "main_bath_type": ArgumentConfig(type=str, default=""),
            "main_bath_water_type": ArgumentConfig(type=str, default=""),
            "water_color": ArgumentConfig(type=str, default=""),
            "pre_visit_mood": ArgumentConfig(type=str, default=""),
            "post_visit_mood": ArgumentConfig(type=str, default=""),
            "visit_time": ArgumentConfig(help="YYYY-MM-DD HH:MM", default=None),
            "exercise_before_onsen": ArgumentConfig(action="store_true"),
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
    "visit-list": CommandConfig(
        func=visit_commands.list_visits,
        help="List all visits in the database.",
        args={},
    ),
    "visit-delete": CommandConfig(
        func=visit_commands.delete_visit,
        help="Delete a visit from the database.",
        args={
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "visit_id": ArgumentConfig(type=int, required=False, help="Visit ID"),
            "force": ArgumentConfig(
                action="store_true", help="Skip confirmation prompt"
            ),
        },
    ),
    "visit-modify": CommandConfig(
        func=visit_commands.modify_visit,
        help="Modify an existing visit.",
        args={
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "visit_id": ArgumentConfig(type=int, required=False, help="Visit ID"),
            "entry_fee_yen": ArgumentConfig(
                type=int, required=False, help="New entry fee"
            ),
            "stay_length_minutes": ArgumentConfig(
                type=int, required=False, help="New stay length"
            ),
            "personal_rating": ArgumentConfig(
                type=int, required=False, help="New personal rating (1-10)"
            ),
            "weather": ArgumentConfig(type=str, required=False, help="New weather"),
            "travel_mode": ArgumentConfig(
                type=str, required=False, help="New travel mode"
            ),
        },
    ),
    # Onsen commands
    "onsen-add": CommandConfig(
        func=onsen_commands.add_onsen,
        help="Add a new onsen.",
        args={
            "ban_number": ArgumentConfig(type=str, required=True),
            "name": ArgumentConfig(type=str, required=True),
            "address": ArgumentConfig(type=str, default=""),
        },
    ),
    "onsen-print-summary": CommandConfig(
        func=onsen_commands.print_summary,
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
    "onsen-recommend": CommandConfig(
        func=onsen_commands.recommend_onsen,
        help="Get onsen recommendations based on location and criteria.",
        args={
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "location": ArgumentConfig(
                type=str, required=False, help="Location ID or name"
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
                action="store_true", default=True, help="Exclude visited onsens"
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
    "onsen-scrape-data": CommandConfig(
        func=onsen_commands.scrape_onsen_data,
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
    # Database commands
    "database-init": CommandConfig(
        func=database_commands.init_db,
        help="Initialize the database.",
        args={
            "force": ArgumentConfig(action="store_true"),
        },
    ),
    "database-fill": CommandConfig(
        func=database_commands.fill_db,
        help="Fill the database with onsen data.",
        args={
            "json_path": ArgumentConfig(type=str, required=True),
        },
    ),
    "database-backup": CommandConfig(
        func=database_commands.backup_db,
        help="Backup the current database to a specified folder. In interactive mode, type 'browse' to open folder selection dialog.",
        args={
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "backup_folder": ArgumentConfig(
                type=str,
                required=False,
                help="Folder path where the backup should be stored (optional in interactive mode)",
            ),
        },
    ),
    "calculate-milestones": CommandConfig(
        func=system_commands.calculate_milestones,
        help="Calculate distance milestones for a location based on onsen distribution.",
        args={
            "location_identifier": ArgumentConfig(
                type=str, required=True, help="Location ID or name", positional=True
            ),
            "update_engine": ArgumentConfig(
                action="store_true",
                help="Update the recommendation engine with calculated milestones",
            ),
            "show_recommendations": ArgumentConfig(
                action="store_true",
                help="Show sample recommendations using the new milestones",
            ),
        },
    ),
}


def get_argument_kwargs(arg_config: ArgumentConfig) -> Dict[str, Any]:
    """Convert ArgumentConfig to argparse kwargs."""
    kwargs = {}

    if arg_config.type is not None:
        kwargs["type"] = arg_config.type
    # 'required' is not valid for positional arguments
    if arg_config.required and not arg_config.positional:
        kwargs["required"] = arg_config.required
    if arg_config.default is not None:
        kwargs["default"] = arg_config.default
    if arg_config.help is not None:
        kwargs["help"] = arg_config.help
    if arg_config.action is not None:
        kwargs["action"] = arg_config.action

    return kwargs
