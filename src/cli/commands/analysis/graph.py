"""Generate interactive graph dashboards from visit data.

This command creates a comprehensive HTML dashboard with visualizations
of your onsen visit data.
"""

import argparse

from loguru import logger

from src.config import get_database_config
from src.db.conn import get_db
from src.lib.graphing.base import DashboardConfig, DataSource, GraphCategory
from src.lib.graphing.dashboard_builder import DashboardBuilder
from src.lib.graphing.visit_graphs import (
    get_all_graphs,
    get_graphs_for_category,
)


def generate_graphs(args: argparse.Namespace) -> int:
    """Generate graph dashboard from visit data.

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

    # Determine which graphs to generate
    category = getattr(args, "category", None)
    data_source_str = getattr(args, "data_source", "visit")

    try:
        data_source = DataSource(data_source_str)
    except ValueError:
        logger.error(f"Invalid data source: {data_source_str}")
        logger.info(f"Valid options: {', '.join([ds.value for ds in DataSource])}")
        return 1

    # Select graphs based on category
    if category:
        try:
            graph_category = GraphCategory(category)
            graph_definitions = get_graphs_for_category(graph_category)
            if not graph_definitions:
                logger.error(f"No graphs found for category: {category}")
                return 1
            dashboard_title = f"Onsen Visit Analytics - {graph_category.value.title()}"
        except ValueError:
            logger.error(f"Invalid category: {category}")
            logger.info(
                f"Valid options: {', '.join([gc.value for gc in GraphCategory])}"
            )
            return 1
    else:
        # Generate all graphs
        graph_definitions = get_all_graphs()
        dashboard_title = "Onsen Visit Analytics - Complete Dashboard"

    logger.info(f"Generating dashboard with {len(graph_definitions)} graphs...")

    # Create dashboard configuration
    dashboard_config = DashboardConfig(
        title=dashboard_title,
        data_source=data_source,
        graph_definitions=graph_definitions,
        columns=getattr(args, "columns", 2),
        show_summary=not getattr(args, "no_summary", False),
        output_filename=getattr(args, "output", None),
    )

    # Build dashboard
    try:
        with get_db(url=db_config.url) as session:
            builder = DashboardBuilder(session)
            output_path = builder.build(
                dashboard_config, auto_open=not getattr(args, "no_open", False)
            )

            if output_path:
                logger.success("Dashboard generation complete!")
                logger.info(f"Dashboard saved to: {output_path}")
                return 0
            else:
                logger.error("Dashboard generation failed")
                return 1

    except Exception as e:
        logger.error(f"Error generating dashboard: {e}", exc_info=True)
        return 1


def list_categories(args: argparse.Namespace) -> int:  # pylint: disable=unused-argument
    """List available graph categories.

    Args:
        args: Command-line arguments (unused)

    Returns:
        Exit code (always 0)
    """
    logger.info("Available graph categories:")
    for category in GraphCategory:
        graphs = get_graphs_for_category(category)
        logger.info(f"  {category.value}: {len(graphs)} graphs")

    logger.info("\nUse --category to generate graphs for a specific category")
    return 0


def list_graphs(args: argparse.Namespace) -> int:
    """List all available graphs.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (always 0)
    """
    category = getattr(args, "category", None)

    if category:
        try:
            graph_category = GraphCategory(category)
            graphs = get_graphs_for_category(graph_category)
            logger.info(f"Graphs in category '{category}':")
        except ValueError:
            logger.error(f"Invalid category: {category}")
            return 1
    else:
        graphs = get_all_graphs()
        logger.info("All available graphs:")

    for i, graph_def in enumerate(graphs, 1):
        logger.info(
            f"  {i}. {graph_def.title} ({graph_def.graph_type.value}) - {graph_def.notes}"
        )

    return 0
