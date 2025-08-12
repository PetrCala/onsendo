"""
clear_analysis_cache.py

Clear the analysis cache.
"""

import argparse
import logging

from src.const import CONST
from src.db.conn import get_db
from src.analysis.engine import AnalysisEngine


logger = logging.getLogger(__name__)


def clear_analysis_cache(args: argparse.Namespace) -> None:
    """Clear the analysis cache and optionally clean up old directories."""
    try:
        with get_db(url=CONST.DATABASE_URL) as session:
            engine = AnalysisEngine(session, args.output_dir)

            # Clear the in-memory cache
            engine.clear_cache()
            print("Analysis cache cleared successfully.")

            # Clean up old analysis directories if requested
            if args.cleanup_old_analyses:
                print("\nCleaning up old analysis directories...")
                engine.cleanup_old_analysis_directories(keep_recent=args.keep_recent)

            # Clean up shared directories if requested
            if args.cleanup_shared_dirs:
                print("\nCleaning up old shared directories...")
                engine.cleanup_shared_directories()

            print("Cleanup completed successfully.")

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise
