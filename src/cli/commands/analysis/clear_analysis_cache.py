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
    """Clear the analysis cache."""
    try:
        with get_db(url=CONST.DATABASE_URL) as session:
            engine = AnalysisEngine(session, args.output_dir)
            engine.clear_cache()
            print("Analysis cache cleared successfully.")

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise
