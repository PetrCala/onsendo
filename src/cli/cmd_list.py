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
import src.cli.commands.heart_rate as heart_rate_commands
import src.cli.commands.analysis as analysis_commands


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
            "stay_restriction_filter": ArgumentConfig(
                type=str,
                required=False,
                default="non_stay_restricted",
                help="Stay restriction filter (non_stay_restricted, all)",
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
        help="Fill the database with onsen data. In interactive mode, will search for scraped data files.",
        args={
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "json_path": ArgumentConfig(
                type=str,
                required=False,
                help="Path to JSON file with onsen data (optional in interactive mode)",
            ),
        },
    ),
    "database-backup": CommandConfig(
        func=database_commands.backup_db,
        help="Backup the current database to a specified folder. In interactive mode, type 'browse' to open folder selection dialog, or type 'artifact' to backup to latest artifact.",
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
            "to_latest_artifact": ArgumentConfig(
                action="store_true",
                short="a",
                help="Backup directly to the latest artifact path (artifacts/db/onsen_latest.db)",
            ),
        },
    ),
    "database-insert-mock-visits": CommandConfig(
        func=database_commands.insert_mock_visits,
        help="Insert mock onsen visit data into the database for testing purposes.",
        args={
            "scenario": ArgumentConfig(
                type=str,
                default="random",
                help="Mock data scenario (random, weekend_warrior, daily_visitor, seasonal_explorer, multi_onsen_enthusiast, custom, seasonal)",
            ),
            "num_days": ArgumentConfig(
                type=int,
                default=44,
                help="Number of days for custom scenario (default: 44)",
            ),
            "visits_per_day": ArgumentConfig(
                type=int,
                default=2,
                help="Visits per day for custom scenario (default: 2)",
            ),
            "num_visits": ArgumentConfig(
                type=int,
                default=10,
                help="Number of visits for seasonal scenario (default: 10)",
            ),
            "season": ArgumentConfig(
                type=str,
                default="summer",
                help="Season for seasonal scenario (spring, summer, autumn, winter)",
            ),
            "start_date": ArgumentConfig(
                type=str,
                help="Start date for custom scenario (YYYY-MM-DD)",
            ),
        },
    ),
    "database-drop-visits": CommandConfig(
        func=database_commands.drop_all_visits,
        help="Drop all onsen visits from the database.",
        args={
            "force": ArgumentConfig(
                action="store_true",
                help="Skip confirmation prompt",
            ),
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
        },
    ),
    "database-drop-visits-by-criteria": CommandConfig(
        func=database_commands.drop_visits_by_criteria,
        help="Drop visits from the database based on specific criteria.",
        args={
            "onsen_id": ArgumentConfig(
                type=int,
                help="Filter visits by specific onsen ID",
            ),
            "before_date": ArgumentConfig(
                type=str,
                help="Filter visits before this date (YYYY-MM-DD)",
            ),
            "after_date": ArgumentConfig(
                type=str,
                help="Filter visits after this date (YYYY-MM-DD)",
            ),
            "rating_below": ArgumentConfig(
                type=int,
                help="Filter visits with rating below this value (1-10)",
            ),
            "rating_above": ArgumentConfig(
                type=int,
                help="Filter visits with rating above this value (1-10)",
            ),
            "force": ArgumentConfig(
                action="store_true",
                help="Skip confirmation prompt",
            ),
            "no_interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
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
    "update-artifacts": CommandConfig(
        func=system_commands.update_artifacts,
        help="Update database artifacts in the artifacts/db folder for presentation purposes.",
        args={},
    ),
    # Heart rate commands
    "heart-rate-import": CommandConfig(
        func=heart_rate_commands.import_heart_rate_data,
        help="Import heart rate data from a file",
        args={
            "file_path": ArgumentConfig(
                type=str,
                required=True,
                help="Path to heart rate data file",
                positional=True,
            ),
            "format": ArgumentConfig(
                type=str,
                required=False,
                help="Force specific file format (csv, json, text)",
            ),
            "notes": ArgumentConfig(
                type=str,
                required=False,
                help="Optional notes about the recording session",
            ),
            "validate_only": ArgumentConfig(
                action="store_true", help="Only validate data without importing"
            ),
        },
    ),
    "heart-rate-list": CommandConfig(
        func=heart_rate_commands.list_heart_rate_data,
        help="List and manage heart rate data records",
        args={
            "linked_only": ArgumentConfig(
                action="store_true", help="Show only records linked to visits"
            ),
            "unlinked_only": ArgumentConfig(
                action="store_true", help="Show only records not linked to visits"
            ),
            "visit_id": ArgumentConfig(
                type=int,
                required=False,
                help="Show heart rate data for specific visit ID",
            ),
            "details": ArgumentConfig(
                action="store_true",
                help="Show detailed information including file integrity",
            ),
        },
    ),
    "heart-rate-link": CommandConfig(
        func=heart_rate_commands.link_heart_rate_to_visit,
        help="Link heart rate data to a visit",
        args={
            "heart_rate_id": ArgumentConfig(
                type=int,
                required=True,
                help="Heart rate record ID",
                positional=True,
            ),
            "visit_id_link": ArgumentConfig(
                type=int,
                required=True,
                help="Visit ID to link to",
                positional=True,
            ),
        },
    ),
    "heart-rate-unlink": CommandConfig(
        func=heart_rate_commands.unlink_heart_rate_from_visit,
        help="Unlink heart rate data from its visit",
        args={
            "heart_rate_id": ArgumentConfig(
                type=int,
                required=True,
                help="Heart rate record ID",
                positional=True,
            ),
        },
    ),
    "heart-rate-delete": CommandConfig(
        func=heart_rate_commands.delete_heart_rate_record,
        help="Delete a heart rate record",
        args={
            "heart_rate_id": ArgumentConfig(
                type=int,
                required=True,
                help="Heart rate record ID",
                positional=True,
            ),
            "force": ArgumentConfig(
                action="store_true", help="Force deletion without confirmation"
            ),
        },
    ),
    "heart-rate-batch-import": CommandConfig(
        func=heart_rate_commands.batch_import_heart_rate_data,
        help="Batch import heart rate data from a directory",
        args={
            "directory": ArgumentConfig(
                type=str,
                required=True,
                help="Directory containing heart rate data files",
                positional=True,
            ),
            "recursive": ArgumentConfig(
                action="store_true", help="Search subdirectories recursively"
            ),
            "format": ArgumentConfig(
                type=str,
                required=False,
                help="Force specific file format for all files",
            ),
            "notes": ArgumentConfig(
                type=str,
                required=False,
                help="Optional notes to add to all imported sessions",
            ),
            "dry_run": ArgumentConfig(
                action="store_true",
                help="Show what would be imported without storing data",
            ),
            "max_workers": ArgumentConfig(
                type=int, default=4, help="Maximum number of parallel workers"
            ),
        },
    ),
    # Analysis commands
    "analysis-run": CommandConfig(
        func=analysis_commands.run_analysis,
        help="Run a custom analysis",
        args={
            "analysis_type": ArgumentConfig(
                type=str,
                required=True,
                help="Type of analysis to perform",
                positional=True,
            ),
            "data_categories": ArgumentConfig(
                type=str,
                required=False,
                help="Comma-separated list of data categories",
            ),
            "metrics": ArgumentConfig(
                type=str,
                required=False,
                help="Comma-separated list of metrics to calculate",
            ),
            "visualizations": ArgumentConfig(
                type=str,
                required=False,
                help="Comma-separated list of visualizations to create",
            ),
            "models": ArgumentConfig(
                type=str,
                required=False,
                help="Comma-separated list of models to train",
            ),
            "filters": ArgumentConfig(
                type=str,
                required=False,
                help="JSON string of filters to apply",
            ),
            "grouping": ArgumentConfig(
                type=str,
                required=False,
                help="Comma-separated list of columns to group by",
            ),
            "time_range": ArgumentConfig(
                type=str,
                required=False,
                help="Time range in format 'start,end' (YYYY-MM-DD HH:MM)",
            ),
            "spatial_bounds": ArgumentConfig(
                type=str,
                required=False,
                help="Spatial bounds in format 'min_lat,max_lat,min_lon,max_lon'",
            ),
            "custom_metrics": ArgumentConfig(
                type=str,
                required=False,
                help="JSON string of custom metrics",
            ),
            "output_format": ArgumentConfig(
                type=str,
                required=False,
                default="html",
                help="Output format for reports",
            ),
            "include_raw_data": ArgumentConfig(
                action="store_true",
                help="Include raw data in results",
            ),
            "include_statistical_tests": ArgumentConfig(
                action="store_true",
                default=True,
                help="Include statistical tests",
            ),
            "confidence_level": ArgumentConfig(
                type=float,
                required=False,
                default=0.95,
                help="Confidence level for statistical tests",
            ),
            "output_dir": ArgumentConfig(
                type=str,
                required=False,
                help="Output directory for analysis results",
            ),
            "export": ArgumentConfig(
                type=str,
                required=False,
                help="Export format (json, csv)",
            ),
        },
    ),
    "analysis-scenario": CommandConfig(
        func=analysis_commands.run_scenario_analysis,
        help="Run a predefined analysis scenario",
        args={
            "scenario": ArgumentConfig(
                type=str,
                required=True,
                help="Analysis scenario to run",
                positional=True,
            ),
            "custom_config": ArgumentConfig(
                type=str,
                required=False,
                help="JSON string of custom configuration overrides",
            ),
            "output_dir": ArgumentConfig(
                type=str,
                required=False,
                help="Output directory for analysis results",
            ),
            "export": ArgumentConfig(
                type=str,
                required=False,
                help="Export format (json, csv)",
            ),
        },
    ),
    "analysis-list-scenarios": CommandConfig(
        func=analysis_commands.list_scenarios,
        help="List available analysis scenarios",
        args={},
    ),
    "analysis-list-options": CommandConfig(
        func=analysis_commands.list_analysis_options,
        help="List available analysis options",
        args={},
    ),
    "analysis-summary": CommandConfig(
        func=analysis_commands.show_analysis_summary,
        help="Show summary of all analyses performed",
        args={
            "output_dir": ArgumentConfig(
                type=str,
                required=False,
                help="Output directory for analysis results",
            ),
        },
    ),
    "analysis-clear-cache": CommandConfig(
        func=analysis_commands.clear_analysis_cache,
        help="Clear the analysis cache",
        args={
            "output_dir": ArgumentConfig(
                type=str,
                required=False,
                help="Output directory for analysis results",
            ),
        },
    ),
    "analysis-export": CommandConfig(
        func=analysis_commands.export_analysis_results,
        help="Export analysis results",
        args={
            "analysis_key": ArgumentConfig(
                type=str,
                required=False,
                help="Analysis key to export",
            ),
            "format": ArgumentConfig(
                type=str,
                required=False,
                default="json",
                help="Export format (json, csv)",
            ),
            "output_dir": ArgumentConfig(
                type=str,
                required=False,
                help="Output directory for analysis results",
            ),
        },
    ),
    "analysis-sample": CommandConfig(
        func=analysis_commands.create_sample_analysis,
        help="Create a sample analysis to demonstrate the system",
        args={
            "output_dir": ArgumentConfig(
                type=str,
                required=False,
                help="Output directory for analysis results",
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
