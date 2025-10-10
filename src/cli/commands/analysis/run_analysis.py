"""
run_analysis.py

Run an analysis.
"""

import argparse
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import logging

from src.const import CONST
from src.db.conn import get_db
from src.analysis.engine import AnalysisEngine
from src.types.analysis import (
    AnalysisType,
    DataCategory,
    MetricType,
    VisualizationType,
    ModelType,
    AnalysisRequest,
    AnalysisScenario,
    ANALYSIS_SCENARIOS,
)

logger = logging.getLogger(__name__)


def run_analysis(args: argparse.Namespace) -> None:
    """Run a custom analysis."""
    # Check if we should run in interactive mode
    if not hasattr(args, "no_interactive") or not args.no_interactive:
        if not args.analysis_type:
            run_analysis_interactive(args)
            return

    # Validate required arguments in non-interactive mode
    if not args.analysis_type:
        logger.error("analysis_type is required in non-interactive mode")
        print("Error: analysis_type is required. Use --help for more information.")
        return

    try:
        with get_db(url=CONST.DATABASE_URL) as session:
            # Initialize analysis engine
            engine = AnalysisEngine(session, args.output_dir)

            # Parse data categories
            data_categories = []
            if args.data_categories:
                for cat_str in args.data_categories.split(","):
                    try:
                        data_categories.append(DataCategory(cat_str.strip()))
                    except ValueError:
                        logger.warning(f"Unknown data category: {cat_str}")
                        continue

            # Parse metrics
            metrics = []
            if args.metrics:
                for metric_str in args.metrics.split(","):
                    try:
                        metrics.append(MetricType(metric_str.strip()))
                    except ValueError:
                        logger.warning(f"Unknown metric: {metric_str}")
                        continue

            # Parse visualizations
            visualizations = []
            if args.visualizations:
                for viz_str in args.visualizations.split(","):
                    try:
                        visualizations.append(VisualizationType(viz_str.strip()))
                    except ValueError:
                        logger.warning(f"Unknown visualization: {viz_str}")
                        continue

            # Parse models
            models = None
            if args.models:
                models = []
                for model_str in args.models.split(","):
                    try:
                        models.append(ModelType(model_str.strip()))
                    except ValueError:
                        logger.warning(f"Unknown model: {model_str}")
                        continue

            # Parse filters
            filters = None
            if args.filters:
                try:
                    filters = json.loads(args.filters)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in filters")
                    return

            # Parse custom metrics
            custom_metrics = None
            if args.custom_metrics:
                try:
                    custom_metrics = json.loads(args.custom_metrics)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in custom_metrics")
                    return

            # Parse analysis type
            try:
                analysis_type = AnalysisType(args.analysis_type)
            except ValueError:
                logger.error(f"Unknown analysis type: {args.analysis_type}")
                return

            # Create analysis request
            request = AnalysisRequest(
                analysis_type=analysis_type,
                data_categories=data_categories
                or [DataCategory.ONSEN_BASIC, DataCategory.VISIT_BASIC],
                metrics=metrics or [MetricType.MEAN, MetricType.MEDIAN, MetricType.STD],
                visualizations=visualizations
                or [VisualizationType.BAR, VisualizationType.HISTOGRAM],
                models=models,
                filters=filters,
                grouping=args.grouping.split(",") if args.grouping else None,
                time_range=args.time_range,
                spatial_bounds=args.spatial_bounds,
                custom_metrics=custom_metrics,
                output_format=args.output_format,
                include_raw_data=args.include_raw_data,
                include_statistical_tests=args.include_statistical_tests,
                confidence_level=args.confidence_level,
            )

            # Run analysis
            logger.info("Starting analysis...")
            result = engine.run_analysis(request)

            if result.errors:
                logger.error("Analysis completed with errors:")
                for error in result.errors:
                    logger.error(f"  - {error}")
            else:
                logger.info("Analysis completed successfully!")
                logger.info(f"Generated {len(result.visualizations)} visualizations")
                logger.info(f"Generated {len(result.insights)} insights")
                if result.models:
                    logger.info(f"Trained {len(result.models)} models")

                # Print insights
                if result.insights:
                    print("\n=== Analysis Insights ===")
                    for i, insight in enumerate(result.insights, 1):
                        print(f"{i}. {insight}")

                # Print key metrics
                if result.metrics and "overall" in result.metrics:
                    print("\n=== Key Metrics ===")
                    overall = result.metrics["overall"]
                    for metric_type, values in overall.items():
                        if isinstance(values, dict):
                            print(f"\n{metric_type.title()}:")
                            for col, value in list(values.items())[:5]:  # Show first 5
                                if isinstance(value, (int, float)):
                                    print(f"  {col}: {value:.2f}")
                        else:
                            print(f"{metric_type}: {values}")

                # Export results if requested
                if args.export:
                    export_path = engine.export_results(result, args.export)
                    if export_path:
                        print(f"\nResults exported to: {export_path}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


def run_analysis_interactive(args: argparse.Namespace) -> None:
    """Run analysis with interactive prompts for missing parameters."""
    print("=== Run Custom Analysis ===\n")

    # Display available analysis types
    print("Available Analysis Types:")
    analysis_types = list(AnalysisType)
    for i, analysis_type in enumerate(analysis_types, 1):
        print(f"  {i}. {analysis_type.value}")

    # Prompt for analysis type
    while True:
        selection = input("\nSelect analysis type (number or name): ").strip()

        # Try to parse as number
        if selection.isdigit():
            idx = int(selection) - 1
            if 0 <= idx < len(analysis_types):
                selected_type = analysis_types[idx].value
                break
            else:
                print(f"Invalid selection. Please enter a number between 1 and {len(analysis_types)}.")
                continue

        # Try to match by name
        try:
            AnalysisType(selection)
            selected_type = selection
            break
        except ValueError:
            print(f"Invalid analysis type: {selection}")
            print("Please enter a valid analysis type name or number.")

    # Update args and call main function
    args.analysis_type = selected_type
    args.no_interactive = True

    print(f"\nRunning {selected_type} analysis...")
    run_analysis(args)
