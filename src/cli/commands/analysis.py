"""
CLI commands for onsen analysis.
"""

import argparse
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import logging

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
    try:
        with get_db() as session:
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
                filters=args.filters,
                grouping=args.grouping.split(",") if args.grouping else None,
                time_range=args.time_range,
                spatial_bounds=args.spatial_bounds,
                custom_metrics=args.custom_metrics,
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


def run_scenario_analysis(args: argparse.Namespace) -> None:
    """Run a predefined analysis scenario."""
    try:
        with get_db() as session:
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


def list_scenarios(args: argparse.Namespace) -> None:
    """List available analysis scenarios."""
    print("Available Analysis Scenarios:")
    print("=" * 50)

    for scenario in AnalysisScenario:
        if scenario in ANALYSIS_SCENARIOS:
            config = ANALYSIS_SCENARIOS[scenario]
            print(f"\n{scenario.value.upper()}")
            print(f"  Description: {config.description}")
            print(
                f"  Analysis Types: {', '.join([t.value for t in config.analysis_types])}"
            )
            print(
                f"  Data Categories: {', '.join([c.value for c in config.data_categories])}"
            )
            print(f"  Metrics: {', '.join([m.value for m in config.metrics])}")
            print(
                f"  Visualizations: {', '.join([v.value for v in config.visualizations])}"
            )
            if config.models:
                print(f"  Models: {', '.join([m.value for m in config.models])}")
            print(f"  Focus Areas: {', '.join(config.insights_focus)}")


def list_analysis_options(args: argparse.Namespace) -> None:
    """List available analysis options."""
    print("Available Analysis Options:")
    print("=" * 50)

    print("\nAnalysis Types:")
    for analysis_type in AnalysisType:
        print(f"  - {analysis_type.value}")

    print("\nData Categories:")
    for category in DataCategory:
        print(f"  - {category.value}")

    print("\nMetrics:")
    for metric in MetricType:
        print(f"  - {metric.value}")

    print("\nVisualizations:")
    for viz in VisualizationType:
        print(f"  - {viz.value}")

    print("\nModels:")
    for model in ModelType:
        print(f"  - {model.value}")


def show_analysis_summary(args: argparse.Namespace) -> None:
    """Show summary of all analyses performed."""
    try:
        with get_db() as session:
            engine = AnalysisEngine(session, args.output_dir)
            summary = engine.get_analysis_summary()

            print("Analysis Summary:")
            print("=" * 50)
            print(f"Total Analyses: {summary['total_analyses']}")
            print(f"Output Directory: {summary['output_directory']}")
            print(f"Cache Size: {summary['cache_size']}")

            if summary["analyses"]:
                print("\nRecent Analyses:")
                for analysis in summary["analyses"][-5:]:  # Show last 5
                    print(f"\n  {analysis['cache_key']}")
                    print(f"    Type: {analysis['analysis_type']}")
                    print(f"    Data Shape: {analysis['data_shape']}")
                    print(f"    Execution Time: {analysis['execution_time']:.2f}s")
                    print(f"    Insights: {analysis['insights_count']}")
                    print(f"    Visualizations: {analysis['visualizations_count']}")
                    print(f"    Models: {analysis['models_count']}")

                    if analysis["errors"]:
                        print(f"    Errors: {len(analysis['errors'])}")
                    if analysis["warnings"]:
                        print(f"    Warnings: {len(analysis['warnings'])}")
            else:
                print("\nNo analyses performed yet.")

    except Exception as e:
        logger.error(f"Failed to get analysis summary: {e}")
        raise


def clear_analysis_cache(args: argparse.Namespace) -> None:
    """Clear the analysis cache."""
    try:
        with get_db() as session:
            engine = AnalysisEngine(session, args.output_dir)
            engine.clear_cache()
            print("Analysis cache cleared successfully.")

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise


def export_analysis_results(args: argparse.Namespace) -> None:
    """Export analysis results."""
    try:
        with get_db() as session:
            engine = AnalysisEngine(session, args.output_dir)

            # Get analysis summary to find available analyses
            summary = engine.get_analysis_summary()

            if not summary["analyses"]:
                print("No analyses available for export.")
                return

            # If no specific analysis specified, show available ones
            if not args.analysis_key:
                print("Available analyses for export:")
                for i, analysis in enumerate(summary["analyses"]):
                    print(f"{i+1}. {analysis['cache_key']}")

                print("\nUse --analysis_key to specify which analysis to export.")
                return

            # Find the specified analysis
            target_analysis = None
            for analysis in summary["analyses"]:
                if analysis["cache_key"] == args.analysis_key:
                    target_analysis = analysis
                    break

            if not target_analysis:
                print(f"Analysis '{args.analysis_key}' not found.")
                return

            # Get the cached result
            cache_key = target_analysis["cache_key"]
            if cache_key in engine._analysis_cache:
                result = engine._analysis_cache[cache_key]

                # Export
                export_path = engine.export_results(result, args.format)
                if export_path:
                    print(f"Results exported to: {export_path}")
                else:
                    print("Export failed.")
            else:
                print(f"Analysis '{args.analysis_key}' not found in cache.")

    except Exception as e:
        logger.error(f"Failed to export analysis results: {e}")
        raise


def create_sample_analysis(args: argparse.Namespace) -> None:
    """Create a sample analysis to demonstrate the system."""
    try:
        with get_db() as session:
            # Initialize analysis engine
            engine = AnalysisEngine(session, args.output_dir)

            # Create a sample analysis request
            request = AnalysisRequest(
                analysis_type=AnalysisType.DESCRIPTIVE,
                data_categories=[
                    DataCategory.ONSEN_BASIC,
                    DataCategory.VISIT_BASIC,
                    DataCategory.VISIT_RATINGS,
                ],
                metrics=[
                    MetricType.MEAN,
                    MetricType.MEDIAN,
                    MetricType.STD,
                    MetricType.COUNT,
                ],
                visualizations=[
                    VisualizationType.BAR,
                    VisualizationType.HISTOGRAM,
                    VisualizationType.CORRELATION_MATRIX,
                ],
                models=[ModelType.LINEAR_REGRESSION],
                include_statistical_tests=True,
            )

            # Run analysis
            logger.info("Running sample analysis...")
            result = engine.run_analysis(request)

            if result.errors:
                logger.error("Sample analysis completed with errors:")
                for error in result.errors:
                    logger.error(f"  - {error}")
            else:
                logger.info("Sample analysis completed successfully!")
                print("\n=== Sample Analysis Results ===")
                print(f"Data Shape: {result.data.shape}")
                print(f"Visualizations: {len(result.visualizations)}")
                print(f"Insights: {len(result.insights)}")
                print(f"Models: {len(result.models) if result.models else 0}")

                # Print insights
                if result.insights:
                    print("\n=== Insights ===")
                    for i, insight in enumerate(result.insights, 1):
                        print(f"{i}. {insight}")

                # Export results
                export_path = engine.export_results(result, "json")
                if export_path:
                    print(f"\nResults exported to: {export_path}")

    except Exception as e:
        logger.error(f"Sample analysis failed: {e}")
        raise
