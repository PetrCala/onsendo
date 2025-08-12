"""
create_sample_analysis.py

Create a sample analysis to demonstrate the system.
"""

import argparse
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
)

logger = logging.getLogger(__name__)


def create_sample_analysis(args: argparse.Namespace) -> None:
    """Create a sample analysis to demonstrate the system."""
    try:
        with get_db(url=CONST.DATABASE_URL) as session:
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
