"""Generate interactive statistics maps from visit data.

This command creates interactive HTML maps showing visited onsens with
colored circles representing statistics from visits. Users can select
which statistic to display via a dropdown in the browser.
"""

import argparse
import webbrowser
from pathlib import Path

from loguru import logger

from src.config import get_database_config
from src.db.conn import get_db
from src.lib.statistics_map_generator import StatisticsMapGenerator
from src.lib.statistics_registry import StatisticsRegistry


def generate_statistics_map(args: argparse.Namespace) -> int:
    """Generate statistics map from visit data.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Get database configuration
    db_config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    # Get visit selection strategy
    visit_selection = getattr(args, "visit_selection", "latest")
    if visit_selection not in ["latest", "first"] and not visit_selection.startswith("nth:"):
        logger.error(
            f"Invalid visit selection: {visit_selection}. "
            "Must be 'latest', 'first', or 'nth:N' (e.g., 'nth:2')"
        )
        return 1

    # Validate nth: format if used
    if visit_selection.startswith("nth:"):
        try:
            n = int(visit_selection.split(":")[1])
            if n < 1:
                logger.error("nth value must be >= 1")
                return 1
        except (ValueError, IndexError):
            logger.error(f"Invalid nth format: {visit_selection}. Use 'nth:N' where N is a number")
            return 1

    show_locations = not getattr(args, "no_show_locations", False)
    output_filename = getattr(args, "output", None)

    logger.info(f"Generating statistics map (visit selection: {visit_selection})...")

    try:
        with get_db(url=db_config.url) as session:
            generator = StatisticsMapGenerator()
            output_path = generator.generate_map(
                session=session,
                visit_selection=visit_selection,
                show_locations=show_locations,
                output_filename=output_filename,
            )

            if output_path:
                logger.success("Statistics map generation complete!")
                logger.info(f"Map saved to: {output_path}")

                # Open in browser unless --no-open is specified
                if not getattr(args, "no_open", False):
                    try:
                        webbrowser.open(f"file://{output_path.absolute()}")
                        logger.info("Opened map in browser")
                    except Exception as e:
                        logger.warning(f"Failed to open browser: {e}")

                return 0
            else:
                logger.error("Statistics map generation failed")
                return 1

    except Exception as e:
        logger.error(f"Error generating statistics map: {e}", exc_info=True)
        return 1


def list_statistics(args: argparse.Namespace) -> int:  # pylint: disable=unused-argument
    """List all available statistics that can be mapped.

    Args:
        args: Command-line arguments (unused)

    Returns:
        Exit code (always 0)
    """
    registry = StatisticsRegistry()
    statistics = registry.get_all_statistics()

    logger.info("Available statistics for mapping:")
    logger.info("")

    # Group by type
    by_type = {}
    for stat in statistics:
        stat_type = stat["type"]
        if stat_type not in by_type:
            by_type[stat_type] = []
        by_type[stat_type].append(stat)

    for stat_type in ["rating", "duration", "numeric"]:
        if stat_type in by_type:
            logger.info(f"{stat_type.title()} Statistics:")
            for stat in by_type[stat_type]:
                logger.info(
                    f"  • {stat['display_name']:30s} ({stat['field_name']:35s}) - {stat['description']}"
                )
            logger.info("")

    logger.info(f"\nTotal: {len(statistics)} statistics available")
    logger.info("\nAll statistics are automatically included in the map.")
    logger.info("Use the dropdown in the browser to select which statistic to display.")

    return 0

