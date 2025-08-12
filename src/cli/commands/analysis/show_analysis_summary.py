"""
show_analysis_summary.py

Show summary of all analyses performed.
"""

import argparse
import logging

from src.const import CONST
from src.db.conn import get_db
from src.analysis.engine import AnalysisEngine


logger = logging.getLogger(__name__)


def show_analysis_summary(args: argparse.Namespace) -> None:
    """Show summary of all analyses performed."""
    try:
        with get_db(url=CONST.DATABASE_URL) as session:
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
