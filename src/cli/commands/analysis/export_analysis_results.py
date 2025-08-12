"""
export_analysis_results.py

Export analysis results.
"""

import argparse
import logging

from src.db.conn import get_db
from src.analysis.engine import AnalysisEngine


logger = logging.getLogger(__name__)


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
