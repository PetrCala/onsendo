"""
run_analysis.py

Run an analysis.
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
