"""
run_scenario_analysis.py

Run a predefined analysis scenario.
"""

import argparse
import logging
import json

from src.const import CONST
from src.db.conn import get_db
from src.analysis.engine import AnalysisEngine
from src.types.analysis import AnalysisScenario

logger = logging.getLogger(__name__)


def run_scenario_analysis(args: argparse.Namespace) -> None:
    """Run a predefined analysis scenario."""
    try:
        with get_db(url=CONST.DATABASE_URL) as session:
            # Initialize analysis engine
            engine = AnalysisEngine(session, args.output_dir)

            # Parse scenario
            try:
                scenario = AnalysisScenario(args.scenario)
            except ValueError:
                logger.error(f"Unknown scenario: {args.scenario}")
                print(
                    f"Available scenarios: {', '.join([s.value for s in AnalysisScenario])}"
                )
                return

            # Parse custom configuration
            custom_config = None
            if args.custom_config:
                try:
                    custom_config = json.loads(args.custom_config)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in custom_config")
                    return

            # Run scenario analysis
            logger.info(f"Running scenario: {scenario.value}")
            result = engine.run_scenario_analysis(scenario, custom_config)

            if result.errors:
                logger.error("Scenario analysis completed with errors:")
                for error in result.errors:
                    logger.error(f"  - {error}")
            else:
                logger.info("Scenario analysis completed successfully!")
                logger.info(f"Generated {len(result.visualizations)} visualizations")
                logger.info(f"Generated {len(result.insights)} insights")
                if result.models:
                    logger.info(f"Trained {len(result.models)} models")

                # Print insights
                if result.insights:
                    print("\n=== Analysis Insights ===")
                    for i, insight in enumerate(result.insights, 1):
                        print(f"{i}. {insight}")

                # Export results if requested
                if args.export:
                    export_path = engine.export_results(result, args.export)
                    if export_path:
                        print(f"\nResults exported to: {export_path}")

    except Exception as e:
        logger.error(f"Scenario analysis failed: {e}")
        raise
