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
    "fill-db": CommandConfig(
        func=commands.fill_db,
        help="Fill the database with onsen data.",
        args={
            "database_folder": ArgumentConfig(type=str, default=CONST.DATABASE_FOLDER),
            "database_name": ArgumentConfig(
                type=str,
                default=CONST.DATABASE_NAME,
                help=f"Database file name, including the .db extension. Default: {CONST.DATABASE_NAME}",
            ),
            "json_path": ArgumentConfig(
                type=str,
                required=True,
                help="Full path to scraped onsen JSON (output of individual scraping). If provided, data will be imported from this file.",
            ),
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
