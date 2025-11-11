"""
cli_commands.py

Defines CLI commands using dataclasses for better structure and type safety.
"""

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from typing import Any, Optional


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
    nargs: Optional[str] = None
    dest: Optional[str] = None
    metavar: Optional[str] = None


@dataclass
class CommandConfig:
    """Configuration for a CLI command."""

    func: Callable[[argparse.Namespace], None]
    help: str
    args: dict[str, ArgumentConfig]


# Lazy loading helpers -----------------------------------------------------


def _load_command_callable(module_path: str, func_name: str) -> Callable[[argparse.Namespace], None]:
    """Import ``module_path`` and return ``func_name`` from it."""

    module = import_module(module_path)
    function = getattr(module, func_name)
    if not callable(function):  # pragma: no cover - defensive programming
        raise TypeError(f"{module_path}.{func_name} is not callable")
    return function


def lazy_command(module_path: str, func_name: str) -> Callable[[argparse.Namespace], None]:
    """Create a lazily imported CLI command handler."""

    @lru_cache(maxsize=None)
    def _load() -> Callable[[argparse.Namespace], None]:
        return _load_command_callable(module_path, func_name)

    def _command(args: argparse.Namespace) -> None:
        return _load()(args)

    _command.__name__ = func_name
    _command.__qualname__ = func_name
    _command.__doc__ = f"Lazy loader for {module_path}.{func_name}"
    return _command


# Define all CLI commands with new grouped structure
CLI_COMMANDS = {
    # Location commands
    "location-add": CommandConfig(
        func=lazy_command("src.cli.commands.location.add", "add_location"),
        help="Add a new location for distance calculations.",
        args={
            "no-interactive": ArgumentConfig(
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
        func=lazy_command("src.cli.commands.location.list", "list_locations"),
        help="List all locations in the database.",
        args={
            "limit": ArgumentConfig(
                type=int,
                required=False,
                help="Limit number of results",
            ),
        },
    ),
    "location-delete": CommandConfig(
        func=lazy_command("src.cli.commands.location.delete", "delete_location"),
        help="Delete a location from the database.",
        args={
            "no-interactive": ArgumentConfig(
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
        func=lazy_command("src.cli.commands.location.modify", "modify_location"),
        help="Modify an existing location.",
        args={
            "no-interactive": ArgumentConfig(
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
        func=lazy_command("src.cli.commands.visit.add", "add_visit"),
        help="Add a new onsen visit.",
        args={
            "no-interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "onsen-id": ArgumentConfig(type=int, required=False),
            "entry-fee-yen": ArgumentConfig(type=int, default=0),
            "stay-length-minutes": ArgumentConfig(type=int, default=0),
            "travel-time-minutes": ArgumentConfig(type=int, default=0),
            "accessibility-rating": ArgumentConfig(type=int, default=0),
            "exercise-length-minutes": ArgumentConfig(type=int, default=0),
            "cleanliness-rating": ArgumentConfig(type=int, default=0),
            "navigability-rating": ArgumentConfig(type=int, default=0),
            "view-rating": ArgumentConfig(type=int, default=0),
            "main-bath-temperature": ArgumentConfig(type=float, default=0),
            "smell-intensity-rating": ArgumentConfig(type=int, default=0),
            "changing-room-cleanliness-rating": ArgumentConfig(type=int, default=0),
            "locker-availability-rating": ArgumentConfig(type=int, default=0),
            "rest-area-rating": ArgumentConfig(type=int, default=0),
            "food-quality-rating": ArgumentConfig(type=int, default=0),
            "sauna-temperature": ArgumentConfig(type=float, default=0),
            "sauna-duration-minutes": ArgumentConfig(type=int, default=0),
            "sauna-rating": ArgumentConfig(type=int, default=0),
            "outdoor-bath-temperature": ArgumentConfig(type=float, default=0),
            "outdoor-bath-rating": ArgumentConfig(type=int, default=0),
            "energy-level-change": ArgumentConfig(type=int, default=0),
            "hydration-level": ArgumentConfig(type=int, default=0),
            "previous-location": ArgumentConfig(type=int, default=0),
            "next-location": ArgumentConfig(type=int, default=0),
            "visit-order": ArgumentConfig(type=int, default=0),
            "atmosphere-rating": ArgumentConfig(type=int, default=0),
            "personal-rating": ArgumentConfig(type=int, default=0),
            "temperature-outside-celsius": ArgumentConfig(type=float, default=0),
            "payment-method": ArgumentConfig(type=str, default=""),
            "weather": ArgumentConfig(type=str, default=""),
            "time-of-day": ArgumentConfig(type=str, default=""),
            "visited-with": ArgumentConfig(type=str, default=""),
            "travel-mode": ArgumentConfig(type=str, default=""),
            "exercise-type": ArgumentConfig(type=str, default=""),
            "crowd-level": ArgumentConfig(type=str, default=""),
            "main-bath-type": ArgumentConfig(type=str, default=""),
            "main-bath-water-type": ArgumentConfig(type=str, default=""),
            "water-color": ArgumentConfig(type=str, default=""),
            "pre-visit-mood": ArgumentConfig(type=str, default=""),
            "post-visit-mood": ArgumentConfig(type=str, default=""),
            "visit-time": ArgumentConfig(help="YYYY-MM-DD HH:MM", default=None),
            "notes": ArgumentConfig(type=str, default="", help="Optional notes about the visit"),
            "exercise-before-onsen": ArgumentConfig(action="store_true"),
            "had-soap": ArgumentConfig(action="store_true"),
            "had-sauna": ArgumentConfig(action="store_true"),
            "had-outdoor-bath": ArgumentConfig(action="store_true"),
            "had-rest-area": ArgumentConfig(action="store_true"),
            "had-food-service": ArgumentConfig(action="store_true"),
            "massage-chair-available": ArgumentConfig(action="store_true"),
            "sauna-visited": ArgumentConfig(action="store_true"),
            "sauna-steam": ArgumentConfig(action="store_true"),
            "outdoor-bath-visited": ArgumentConfig(action="store_true"),
            "multi-onsen-day": ArgumentConfig(action="store_true"),
        },
    ),
    "visit-list": CommandConfig(
        func=lazy_command("src.cli.commands.visit.list", "list_visits"),
        help="List all visits in the database.",
        args={
            "limit": ArgumentConfig(
                type=int,
                required=False,
                help="Limit number of results",
            ),
        },
    ),
    "visit-delete": CommandConfig(
        func=lazy_command("src.cli.commands.visit.delete", "delete_visit"),
        help="Delete a visit from the database.",
        args={
            "no-interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "visit-id": ArgumentConfig(type=int, required=False, help="Visit ID"),
            "force": ArgumentConfig(
                action="store_true", help="Skip confirmation prompt"
            ),
        },
    ),
    "visit-modify": CommandConfig(
        func=lazy_command("src.cli.commands.visit.modify", "modify_visit"),
        help="Modify an existing visit.",
        args={
            "no-interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "visit-id": ArgumentConfig(type=int, required=False, help="Visit ID"),
            "entry-fee-yen": ArgumentConfig(
                type=int, required=False, help="New entry fee"
            ),
            "stay-length-minutes": ArgumentConfig(
                type=int, required=False, help="New stay length"
            ),
            "personal-rating": ArgumentConfig(
                type=int, required=False, help="New personal rating (1-10)"
            ),
            "weather": ArgumentConfig(type=str, required=False, help="New weather"),
            "travel-mode": ArgumentConfig(
                type=str, required=False, help="New travel mode"
            ),
        },
    ),
    # Onsen commands
    "onsen-add": CommandConfig(
        func=lazy_command("src.cli.commands.onsen.add", "add_onsen"),
        help="Add a new onsen.",
        args={
            "ban-number": ArgumentConfig(type=str, required=True),
            "name": ArgumentConfig(type=str, required=True),
            "address": ArgumentConfig(type=str, default=""),
        },
    ),
    "onsen-print-summary": CommandConfig(
        func=lazy_command("src.cli.commands.onsen.print_summary", "print_summary"),
        help="Print a summary for an onsen by ID or ban number.",
        args={
            "onsen-id": ArgumentConfig(type=int, required=False, help="Onsen ID"),
            "ban-number": ArgumentConfig(
                type=str, required=False, help="Onsen BAN number"
            ),
            "name": ArgumentConfig(
                type=str, required=False, help="Onsen name (exact match)"
            ),
        },
    ),
    "onsen-map": CommandConfig(
        func=lazy_command("src.cli.commands.onsen.map", "map_onsens"),
        help="Generate interactive map of all onsens in the database.",
        args={
            "filter": ArgumentConfig(
                action="append",
                help="Filter onsens by keyword (can be used multiple times for OR logic). Example: --filter '足湯'",
            ),
            "field": ArgumentConfig(
                action="append",
                help="Field(s) to search in: name, description, business_form, remarks, address, region, or 'all' (default: name)",
            ),
            "list-matches": ArgumentConfig(
                action="store_true",
                help="Display table of matching onsens before generating map (only with --filter)",
            ),
            "no-open-map": ArgumentConfig(
                action="store_true",
                help="Do not automatically open map in browser (default: auto-open)",
            ),
            "no-show-locations": ArgumentConfig(
                action="store_true",
                help="Do not show user location markers on map (default: show locations)",
            ),
        },
    ),
    "onsen-recommend": CommandConfig(
        func=lazy_command("src.cli.commands.onsen.recommend", "recommend_onsen"),
        help="Get onsen recommendations based on location and criteria.",
        args={
            "no-interactive": ArgumentConfig(
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
                help="Distance category (very_close, close, medium, far, any)",
            ),
            "exclude-closed": ArgumentConfig(
                action="store_true", default=True, help="Exclude closed onsens"
            ),
            "exclude-visited": ArgumentConfig(
                action="store_true", default=True, help="Exclude visited onsens"
            ),
            "min-hours-after": ArgumentConfig(
                type=int,
                required=False,
                default=2,
                help="Minimum hours onsen should be open after target time (0 to disable)",
            ),
            "limit": ArgumentConfig(
                type=int, required=False, help="Maximum number of recommendations"
            ),
            "stay-restriction-filter": ArgumentConfig(
                type=str,
                required=False,
                default="non_stay_restricted",
                help="Stay restriction filter (non_stay_restricted, all)",
            ),
            "no-generate-map": ArgumentConfig(
                action="store_true",
                help="Disable interactive map generation",
            ),
            "open-map": ArgumentConfig(
                action="store_true",
                help="Automatically open map in browser after generation",
            ),
            "no-show-locations": ArgumentConfig(
                action="store_true",
                help="Do not show user location markers on map (default: show locations)",
            ),
        },
    ),
    "onsen-scrape-data": CommandConfig(
        func=lazy_command("src.cli.commands.onsen.scrape_data", "scrape_onsen_data"),
        help="Scrape onsen data from the web.",
        args={
            "fetch-mapping-only": ArgumentConfig(
                action="store_true",
                help="Only fetch the onsen mapping (list of all onsens), skip individual scraping",
            ),
            "scrape-individual-only": ArgumentConfig(
                action="store_true",
                help="Only scrape individual onsen pages, skip fetching the mapping (requires existing mapping file)",
            ),
        },
    ),
    "onsen-identify": CommandConfig(
        func=lazy_command("src.cli.commands.onsen.identify", "identify"),
        help="Identify an onsen based on name, location, address, or region.",
        args={
            "name": ArgumentConfig(
                type=str,
                required=False,
                help="Onsen name (supports fuzzy matching)",
            ),
            "latitude": ArgumentConfig(
                type=float,
                required=False,
                help="Latitude in decimal degrees (requires --longitude)",
            ),
            "longitude": ArgumentConfig(
                type=float,
                required=False,
                help="Longitude in decimal degrees (requires --latitude)",
            ),
            "address": ArgumentConfig(
                type=str,
                required=False,
                help="Address (supports fuzzy matching)",
            ),
            "region": ArgumentConfig(
                type=str,
                required=False,
                help="Region name (supports fuzzy matching)",
            ),
            "max-distance": ArgumentConfig(
                type=float,
                required=False,
                help="Maximum distance in kilometers (for location-based search)",
            ),
            "limit": ArgumentConfig(
                type=int,
                default=5,
                help="Maximum number of results to return (default: 5)",
            ),
            "auto-print": ArgumentConfig(
                action="store_true",
                help="Automatically print summary of best match without prompting",
            ),
            "name-threshold": ArgumentConfig(
                type=float,
                default=0.6,
                help="Minimum similarity threshold for name matching (0.0-1.0, default: 0.6)",
            ),
            "address-threshold": ArgumentConfig(
                type=float,
                default=0.5,
                help="Minimum similarity threshold for address matching (0.0-1.0, default: 0.5)",
            ),
            "region-threshold": ArgumentConfig(
                type=float,
                default=0.6,
                help="Minimum similarity threshold for region matching (0.0-1.0, default: 0.6)",
            ),
        },
    ),
    # Database commands
    "database-init": CommandConfig(
        func=lazy_command("src.cli.commands.database.init_db", "init_db"),
        help="Initialize the database.",
        args={
            "force": ArgumentConfig(action="store_true"),
        },
    ),
    "database-migrate-to-envs": CommandConfig(
        func=lazy_command("src.cli.commands.database.migrate_to_envs", "migrate_to_environments"),
        help="Migrate from single database to multi-environment setup (one-time migration).",
        args={
            "force": ArgumentConfig(
                action="store_true",
                help="Overwrite existing environment databases if they exist"
            ),
            "yes": ArgumentConfig(
                short="y",
                action="store_true",
                help="Skip confirmation prompt"
            ),
        },
    ),
    "database-fill": CommandConfig(
        func=lazy_command("src.cli.commands.database.fill_db", "fill_db"),
        help="Fill the database with onsen data. In interactive mode, will search for scraped data files.",
        args={
            "no-interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "json-path": ArgumentConfig(
                type=str,
                required=False,
                help="Path to JSON file with onsen data (optional in interactive mode)",
            ),
        },
    ),
    "database-backup": CommandConfig(
        func=lazy_command("src.cli.commands.database.backup", "backup_db"),
        help="Backup the current database to a specified folder. In interactive mode, type 'browse' to open folder selection dialog, or type 'artifact' to backup to latest artifact.",
        args={
            "no-interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "backup-folder": ArgumentConfig(
                type=str,
                required=False,
                help="Folder path where the backup should be stored (optional in interactive mode)",
            ),
            "to-latest-artifact": ArgumentConfig(
                action="store_true",
                short="a",
                help="Backup directly to the latest artifact path (artifacts/db/onsen_latest.db)",
            ),
        },
    ),
    "database-insert-mock-visits": CommandConfig(
        func=lazy_command("src.cli.commands.database.mock_data", "insert_mock_visits"),
        help="[DEPRECATED] Insert simple mock data for testing. Use 'database generate-realistic-data' for analysis-ready data.",
        args={
            "scenario": ArgumentConfig(
                type=str,
                default="random",
                help="Mock data scenario (random, weekend_warrior, daily_visitor, seasonal_explorer, multi_onsen_enthusiast, custom, seasonal)",
            ),
            "num-days": ArgumentConfig(
                type=int,
                default=44,
                help="Number of days for custom scenario (default: 44)",
            ),
            "visits-per-day": ArgumentConfig(
                type=int,
                default=2,
                help="Visits per day for custom scenario (default: 2)",
            ),
            "num-visits": ArgumentConfig(
                type=int,
                default=10,
                help="Number of visits for seasonal scenario (default: 10)",
            ),
            "season": ArgumentConfig(
                type=str,
                default="summer",
                help="Season for seasonal scenario (spring, summer, autumn, winter)",
            ),
            "start-date": ArgumentConfig(
                type=str,
                help="Start date for custom scenario (YYYY-MM-DD)",
            ),
        },
    ),
    "database-drop-visits": CommandConfig(
        func=lazy_command("src.cli.commands.database.drop_visits", "drop_all_visits"),
        help="Drop all onsen visits from the database.",
        args={
            "force": ArgumentConfig(
                action="store_true",
                help="Skip confirmation prompt",
            ),
            "no-interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
        },
    ),
    "database-drop-visits-by-criteria": CommandConfig(
        func=lazy_command("src.cli.commands.database.drop_visits", "drop_visits_by_criteria"),
        help="Drop visits from the database based on specific criteria.",
        args={
            "onsen-id": ArgumentConfig(
                type=int,
                help="Filter visits by specific onsen ID",
            ),
            "before-date": ArgumentConfig(
                type=str,
                help="Filter visits before this date (YYYY-MM-DD)",
            ),
            "after-date": ArgumentConfig(
                type=str,
                help="Filter visits after this date (YYYY-MM-DD)",
            ),
            "rating-below": ArgumentConfig(
                type=int,
                help="Filter visits with rating below this value (1-10)",
            ),
            "rating-above": ArgumentConfig(
                type=int,
                help="Filter visits with rating above this value (1-10)",
            ),
            "force": ArgumentConfig(
                action="store_true",
                help="Skip confirmation prompt",
            ),
            "no-interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
        },
    ),
    "database-generate-realistic-data": CommandConfig(
        func=lazy_command("src.cli.commands.database.generate_realistic_data", "generate_realistic_data"),
        help="Generate comprehensive realistic mock data with user profiles and correlations.",
        args={
            "scenario": ArgumentConfig(
                type=str,
                default="comprehensive",
                help="Data scenario (comprehensive, econometric, heart_rate, pricing, spatial, temporal, tourist, local_regular, integrated)",
            ),
            "num-visits": ArgumentConfig(
                type=int,
                help="Number of visits to generate (default varies by scenario)",
            ),
            "days": ArgumentConfig(
                type=int,
                help="Number of days to span (for comprehensive, integrated scenarios)",
            ),
            "months": ArgumentConfig(
                type=int,
                help="Number of months (for temporal, local_regular scenarios)",
            ),
            "trip-days": ArgumentConfig(
                type=int,
                help="Trip duration in days (for tourist scenario)",
            ),
            "visits-per-day": ArgumentConfig(
                type=int,
                help="Visits per day (for tourist scenario)",
            ),
            "hr-coverage": ArgumentConfig(
                type=float,
                help="Heart rate coverage 0.0-1.0 (for integrated scenario)",
            ),
            "quiet": ArgumentConfig(
                action="store_true",
                help="Suppress detailed output",
            ),
        },
    ),
    "database-list-profiles": CommandConfig(
        func=lazy_command("src.cli.commands.database.generate_realistic_data", "list_user_profiles"),
        help="List available user profiles for mock data generation.",
        args={},
    ),
    "database-scenario-info": CommandConfig(
        func=lazy_command("src.cli.commands.database.generate_realistic_data", "show_scenario_info"),
        help="Show detailed information about a data generation scenario.",
        args={
            "scenario": ArgumentConfig(
                type=str,
                required=True,
                positional=True,
                help="Scenario name to show info for",
            ),
        },
    ),
    "database-migrate-upgrade": CommandConfig(
        func=lazy_command("src.cli.commands.database.migrate", "migrate_upgrade"),
        help="Run database migrations to upgrade to the latest version.",
        args={
            "revision": ArgumentConfig(
                type=str,
                required=False,
                default="head",
                help="Revision to upgrade to (default: head)",
            ),
        },
    ),
    "database-migrate-downgrade": CommandConfig(
        func=lazy_command("src.cli.commands.database.migrate", "migrate_downgrade"),
        help="Downgrade database to a previous migration.",
        args={
            "revision": ArgumentConfig(
                type=str,
                required=True,
                help="Revision to downgrade to (use '-1' for previous)",
            ),
            "force": ArgumentConfig(
                action="store_true",
                help="Skip confirmation prompt",
            ),
        },
    ),
    "database-migrate-current": CommandConfig(
        func=lazy_command("src.cli.commands.database.migrate", "migrate_current"),
        help="Show current database migration revision.",
        args={},
    ),
    "database-migrate-history": CommandConfig(
        func=lazy_command("src.cli.commands.database.migrate", "migrate_history"),
        help="Show migration history.",
        args={
            "verbose": ArgumentConfig(
                action="store_true",
                help="Show detailed information",
            ),
        },
    ),
    "database-migrate-generate": CommandConfig(
        func=lazy_command("src.cli.commands.database.migrate", "migrate_generate"),
        help="Generate a new migration based on model changes.",
        args={
            "message": ArgumentConfig(
                type=str,
                required=True,
                help="Migration message",
            ),
        },
    ),
    "database-migrate-stamp": CommandConfig(
        func=lazy_command("src.cli.commands.database.migrate", "migrate_stamp"),
        help="Stamp the database with a specific revision without running migrations.",
        args={
            "revision": ArgumentConfig(
                type=str,
                required=True,
                help="Revision to stamp (use 'head' for latest)",
            ),
        },
    ),
    "calculate-milestones": CommandConfig(
        func=lazy_command("src.cli.commands.system.calculate_milestones", "calculate_milestones"),
        help="Calculate distance milestones for a location based on onsen distribution.",
        args={
            "location-identifier": ArgumentConfig(
                type=str, required=True, help="Location ID or name", positional=True
            ),
            "update-engine": ArgumentConfig(
                action="store_true",
                help="Update the recommendation engine with calculated milestones",
            ),
            "show-recommendations": ArgumentConfig(
                action="store_true",
                help="Show sample recommendations using the new milestones",
            ),
        },
    ),
    "system-clear-cache": CommandConfig(
        func=lazy_command("src.cli.commands.system.clear_cache", "clear_cache"),
        help="Clear cached recommendation data.",
        args={
            "namespace": ArgumentConfig(
                type=str,
                required=False,
                help="Cache namespace to clear (distance, milestones, or all).",
            ),
        },
    ),
    "update-artifacts": CommandConfig(
        func=lazy_command("src.cli.commands.system.update_artifacts", "update_artifacts"),
        help="Update database artifacts in the artifacts/db folder for presentation purposes.",
        args={},
    ),
    # Weight commands
    "weight-import": CommandConfig(
        func=lazy_command("src.cli.commands.weight.import_", "import_weight_data"),
        help="Import weight data from a file",
        args={
            "file-path": ArgumentConfig(
                type=str,
                required=True,
                help="Path to weight data file",
                positional=True,
            ),
            "format": ArgumentConfig(
                type=str,
                required=False,
                help="Force specific file format (csv, json, apple_health)",
            ),
            "notes": ArgumentConfig(
                type=str,
                required=False,
                help="Optional notes about the measurement(s)",
            ),
            "validate-only": ArgumentConfig(
                action="store_true", help="Only validate data without importing"
            ),
        },
    ),
    "weight-add": CommandConfig(
        func=lazy_command("src.cli.commands.weight.add", "add_weight_measurement"),
        help="Manually add a weight measurement",
        args={
            "weight": ArgumentConfig(
                type=float,
                required=False,
                help="Weight in kilograms",
            ),
            "time": ArgumentConfig(
                type=str,
                required=False,
                help="Measurement time (YYYY-MM-DD HH:MM:SS, defaults to now)",
            ),
            "conditions": ArgumentConfig(
                type=str,
                required=False,
                help="Measurement conditions (fasted, after_meal, post_workout, etc.)",
            ),
            "time-of-day": ArgumentConfig(
                type=str,
                required=False,
                help="Time of day (morning, afternoon, evening, night)",
            ),
            "notes": ArgumentConfig(
                type=str,
                required=False,
                help="Optional notes",
            ),
        },
    ),
    "weight-list": CommandConfig(
        func=lazy_command("src.cli.commands.weight.list", "list_weight_measurements"),
        help="List weight measurements",
        args={
            "date-range": ArgumentConfig(
                type=str,
                required=False,
                help="Date range in format 'YYYY-MM-DD,YYYY-MM-DD'",
            ),
            "limit": ArgumentConfig(
                type=int,
                required=False,
                help="Limit number of results",
            ),
            "format": ArgumentConfig(
                type=str,
                required=False,
                help="Output format (table, json)",
            ),
        },
    ),
    "weight-delete": CommandConfig(
        func=lazy_command("src.cli.commands.weight.delete", "delete_weight_measurement"),
        help="Delete a weight measurement",
        args={
            "id": ArgumentConfig(
                type=int,
                required=False,
                help="Measurement ID to delete (if not provided, interactive selection)",
            ),
        },
    ),
    "weight-stats": CommandConfig(
        func=lazy_command("src.cli.commands.weight.stats", "show_weight_stats"),
        help="Show weight statistics and trends",
        args={
            "week": ArgumentConfig(
                type=str,
                required=False,
                help="Week start date (YYYY-MM-DD) for weekly summary",
            ),
            "month": ArgumentConfig(
                type=int,
                required=False,
                help="Month number (1-12) for monthly summary",
            ),
            "year": ArgumentConfig(
                type=int,
                required=False,
                help="Year for monthly summary (defaults to current year)",
            ),
            "all-time": ArgumentConfig(
                action="store_true",
                help="Show all-time statistics",
            ),
        },
    ),
    "weight-export": CommandConfig(
        func=lazy_command("src.cli.commands.weight.export", "export_weight_data"),
        help="Export weight measurements to file",
        args={
            "format": ArgumentConfig(
                type=str,
                required=False,
                default="csv",
                help="Export format (csv, json)",
            ),
            "output": ArgumentConfig(
                type=str,
                required=False,
                help="Output file path",
            ),
            "date-range": ArgumentConfig(
                type=str,
                required=False,
                help="Date range to export 'YYYY-MM-DD,YYYY-MM-DD'",
            ),
        },
    ),
    # Analysis commands
    "analysis-run": CommandConfig(
        func=lazy_command("src.cli.commands.analysis.run_analysis", "run_analysis"),
        help="Run a custom analysis",
        args={
            "no-interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "analysis-type": ArgumentConfig(
                type=str,
                required=False,
                help="Type of analysis to perform",
                positional=True,
                nargs="?",
            ),
            "data-categories": ArgumentConfig(
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
            "time-range": ArgumentConfig(
                type=str,
                required=False,
                help="Time range in format 'start,end' (YYYY-MM-DD HH:MM)",
            ),
            "spatial-bounds": ArgumentConfig(
                type=str,
                required=False,
                help="Spatial bounds in format 'min_lat,max_lat,min_lon,max_lon'",
            ),
            "custom-metrics": ArgumentConfig(
                type=str,
                required=False,
                help="JSON string of custom metrics",
            ),
            "output-format": ArgumentConfig(
                type=str,
                required=False,
                default="html",
                help="Output format for reports",
            ),
            "include-raw-data": ArgumentConfig(
                action="store_true",
                help="Include raw data in results",
            ),
            "include-statistical-tests": ArgumentConfig(
                action="store_true",
                default=True,
                help="Include statistical tests",
            ),
            "confidence-level": ArgumentConfig(
                type=float,
                required=False,
                default=0.95,
                help="Confidence level for statistical tests",
            ),
            "output-dir": ArgumentConfig(
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
        func=lazy_command("src.cli.commands.analysis.run_scenario_analysis", "run_scenario_analysis"),
        help="Run a predefined analysis scenario",
        args={
            "no-interactive": ArgumentConfig(
                action="store_true",
                short="ni",
                help="Run in non-interactive mode (default: False)",
            ),
            "scenario": ArgumentConfig(
                type=str,
                required=False,
                help="Analysis scenario to run",
                positional=True,
                nargs="?",
            ),
            "custom-config": ArgumentConfig(
                type=str,
                required=False,
                help="JSON string of custom configuration overrides",
            ),
            "output-dir": ArgumentConfig(
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
        func=lazy_command("src.cli.commands.analysis.list_scenarios", "list_scenarios"),
        help="List available analysis scenarios",
        args={},
    ),
    "analysis-list-options": CommandConfig(
        func=lazy_command("src.cli.commands.analysis.list_analysis_options", "list_analysis_options"),
        help="List available analysis options",
        args={},
    ),
    "analysis-summary": CommandConfig(
        func=lazy_command("src.cli.commands.analysis.show_analysis_summary", "show_analysis_summary"),
        help="Show summary of all analyses performed",
        args={
            "output-dir": ArgumentConfig(
                type=str,
                required=False,
                help="Output directory for analysis results",
            ),
        },
    ),
    "analysis-clear-cache": CommandConfig(
        func=lazy_command("src.cli.commands.analysis.clear_analysis_cache", "clear_analysis_cache"),
        help="Clear the analysis cache and optionally clean up old directories",
        args={
            "output-dir": ArgumentConfig(
                type=str,
                required=False,
                help="Output directory for analysis results",
            ),
            "cleanup-old-analyses": ArgumentConfig(
                action="store_true",
                help="Clean up old analysis directories, keeping only recent ones",
            ),
            "keep-recent": ArgumentConfig(
                type=int,
                required=False,
                default=5,
                help="Number of recent analysis directories to keep (default: 5)",
            ),
            "cleanup-shared-dirs": ArgumentConfig(
                action="store_true",
                help="Clean up old shared directories (models, visualizations)",
            ),
        },
    ),
    "analysis-export": CommandConfig(
        func=lazy_command("src.cli.commands.analysis.export_analysis_results", "export_analysis_results"),
        help="Export analysis results",
        args={
            "analysis-key": ArgumentConfig(
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
            "output-dir": ArgumentConfig(
                type=str,
                required=False,
                help="Output directory for analysis results",
            ),
        },
    ),
    # Rules commands
    "rules-print": CommandConfig(
        func=lazy_command("src.cli.commands.rules.print", "print_rules"),
        help="Print the current Onsendo rules, formatted.",
        args={
            "section": ArgumentConfig(
                type=str,
                required=False,
                help="Specific section number to print (default: all)",
            ),
            "raw": ArgumentConfig(
                action="store_true",
                help="Output raw markdown (default: formatted)",
            ),
            "version": ArgumentConfig(
                type=int,
                required=False,
                help="Print rules at specific revision version",
            ),
        },
    ),
    "rules-revision-create": CommandConfig(
        func=lazy_command("src.cli.commands.rules.revision_create", "create_revision"),
        help="Create a new rule revision with interactive workflow (Rule Review Sunday).",
        args={
            "auto-fetch": ArgumentConfig(
                action="store_true",
                help="Automatically fetch weekly statistics from database (onsen visits, exercise data)",
            ),
        },
    ),
    "rules-revision-list": CommandConfig(
        func=lazy_command("src.cli.commands.rules.revision_list", "list_revisions"),
        help="List all rule revisions.",
        args={
            "verbose": ArgumentConfig(
                action="store_true",
                help="Include full adjustment descriptions",
            ),
            "limit": ArgumentConfig(
                type=int,
                required=False,
                help="Maximum number of revisions to show",
            ),
            "section": ArgumentConfig(
                type=str,
                required=False,
                help="Filter by specific section number",
            ),
        },
    ),
    "rules-revision-show": CommandConfig(
        func=lazy_command("src.cli.commands.rules.revision_show", "show_revision"),
        help="Show detailed information about a specific rule revision.",
        args={
            "version": ArgumentConfig(
                type=int,
                required=False,
                help="Version number to show",
            ),
            "date": ArgumentConfig(
                type=str,
                required=False,
                help="Date filter (YYYY-MM-DD)",
            ),
            "format": ArgumentConfig(
                type=str,
                required=False,
                help="Output format (text, json, markdown)",
            ),
            "open-file": ArgumentConfig(
                action="store_true",
                help="Open the revision markdown file in default editor",
            ),
        },
    ),
    "rules-revision-modify": CommandConfig(
        func=lazy_command("src.cli.commands.rules.revision_modify", "modify_revision"),
        help="Modify an existing rule revision's metadata (not the rules themselves).",
        args={
            "version": ArgumentConfig(
                type=int,
                required=False,
                help="Version number to modify",
            ),
        },
    ),
    "rules-revision-compare": CommandConfig(
        func=lazy_command("src.cli.commands.rules.revision_compare", "compare_revisions"),
        help="Compare two rule revisions.",
        args={
            "version-a": ArgumentConfig(
                type=int,
                required=False,
                help="First version number",
            ),
            "version-b": ArgumentConfig(
                type=int,
                required=False,
                help="Second version number",
            ),
            "section": ArgumentConfig(
                type=str,
                required=False,
                help="Limit comparison to specific section",
            ),
            "metrics-only": ArgumentConfig(
                action="store_true",
                help="Only show metrics comparison",
            ),
            "rules-only": ArgumentConfig(
                action="store_true",
                help="Only show rules comparison",
            ),
        },
    ),
    "rules-revision-export": CommandConfig(
        func=lazy_command("src.cli.commands.rules.revision_export", "export_revisions"),
        help="Export rule revision data.",
        args={
            "version": ArgumentConfig(
                type=int,
                required=False,
                help="Specific version to export (default: all)",
            ),
            "format": ArgumentConfig(
                type=str,
                required=False,
                default="json",
                help="Export format (json, csv, markdown)",
            ),
            "output": ArgumentConfig(
                type=str,
                required=False,
                help="Output file path",
            ),
            "include-weekly-reviews": ArgumentConfig(
                action="store_true",
                help="Include full weekly review data",
            ),
        },
    ),
    "rules-history": CommandConfig(
        func=lazy_command("src.cli.commands.rules.history", "show_history"),
        help="Show chronological history of all rule changes.",
        args={
            "section": ArgumentConfig(
                type=str,
                required=False,
                help="Filter to specific section number",
            ),
            "date-range": ArgumentConfig(
                type=str,
                required=False,
                help="Filter by date range 'YYYY-MM-DD,YYYY-MM-DD'",
            ),
            "visual": ArgumentConfig(
                action="store_true",
                help="Generate visual timeline chart",
            ),
        },
    ),
    # Strava commands
    "strava-auth": CommandConfig(
        func=lazy_command("src.cli.commands.strava.auth", "cmd_strava_auth"),
        help="Authenticate with Strava API (OAuth2 flow).",
        args={
            "reauth": ArgumentConfig(
                action="store_true",
                help="Force re-authentication even if already authenticated",
            ),
        },
    ),
    "strava-status": CommandConfig(
        func=lazy_command("src.cli.commands.strava.status", "cmd_strava_status"),
        help="Check Strava API connection status and credentials.",
        args={
            "verbose": ArgumentConfig(
                action="store_true",
                short="v",
                help="Show detailed configuration and rate limit info",
            ),
        },
    ),
    "strava-download": CommandConfig(
        func=lazy_command("src.cli.commands.strava.download", "cmd_strava_download"),
        help="Download specific Strava activity by ID.",
        args={
            "activity-id": ArgumentConfig(
                type=int,
                required=True,
                help="Strava activity ID to download",
                positional=True,
            ),
            "format": ArgumentConfig(
                type=str,
                required=False,
                help="Output format: gpx, json, hr_csv, all (default: all)",
            ),
        },
    ),
    "strava-sync": CommandConfig(
        func=lazy_command("src.cli.commands.strava.sync", "cmd_strava_sync"),
        help="Batch sync recent Strava activities.",
        args={
            "days": ArgumentConfig(
                type=int,
                required=False,
                help="Sync activities from last N days (default: 7)",
            ),
            "type": ArgumentConfig(
                type=str,
                required=False,
                help="Only sync specific activity type (Run, Ride, Hike, etc.)",
            ),
            "interactive": ArgumentConfig(
                action="store_true",
                help="Enable post-sync review of auto-detected onsen monitoring activities",
            ),
            "auto-link": ArgumentConfig(
                action="store_true",
                help="Enable visit linking during interactive review",
            ),
            "no-auto-pair": ArgumentConfig(
                action="store_true",
                help="Disable automatic activity-visit pairing (enabled by default)",
            ),
            "pairing-threshold": ArgumentConfig(
                type=float,
                required=False,
                help="Confidence threshold for auto-pairing (default: 0.8 = 80%%)",
            ),
            "dry-run": ArgumentConfig(
                action="store_true",
                help="Show what would be synced without importing",
            ),
            "skip-existing": ArgumentConfig(
                action="store_true",
                help="Skip activities that already exist in database",
            ),
        },
    ),
    "strava-pair-activities": CommandConfig(
        func=lazy_command("src.cli.commands.strava.pair", "cmd_strava_pair_activities"),
        help="Pair onsen monitoring activities to visits based on name and time.",
        args={
            "since": ArgumentConfig(
                type=str,
                required=False,
                help="Only pair activities after this date (YYYY-MM-DD)",
            ),
            "dry-run": ArgumentConfig(
                action="store_true",
                help="Preview pairings without saving to database",
            ),
            "auto-threshold": ArgumentConfig(
                type=float,
                required=False,
                help="Confidence threshold for auto-linking (default: 0.8 = 80%%)",
            ),
            "review-threshold": ArgumentConfig(
                type=float,
                required=False,
                help="Minimum confidence for review (default: 0.6 = 60%%)",
            ),
            "time-window": ArgumentConfig(
                type=int,
                required=False,
                help="Search window in hours for finding visits (default: 4)",
            ),
            "interactive": ArgumentConfig(
                action="store_true",
                help="Enable interactive review for medium-confidence matches",
            ),
        },
    ),
}


def get_argument_kwargs(arg_config: ArgumentConfig) -> dict[str, Any]:
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
    if arg_config.nargs is not None:
        kwargs["nargs"] = arg_config.nargs
    if arg_config.metavar is not None:
        kwargs["metavar"] = arg_config.metavar
    if arg_config.dest is not None and not arg_config.positional:
        kwargs["dest"] = arg_config.dest

    return kwargs
