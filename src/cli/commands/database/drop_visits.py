"""
drop_visits.py

Mass drop all onsen visits from the database.
"""

import argparse
from loguru import logger
from src.db.conn import get_db
from src.db.models import OnsenVisit
from src.const import CONST


def drop_all_visits(args: argparse.Namespace) -> None:
    """
    Drop all onsen visits from the database.
    """
    with get_db(url=CONST.DATABASE_URL) as db:
        # Count existing visits
        visit_count = db.query(OnsenVisit).count()

        if visit_count == 0:
            logger.info("No visits found in database. Nothing to drop.")
            return

        # Confirm deletion unless --force is used
        if not args.force:
            if args.no_interactive:
                logger.error(
                    "Cannot drop visits without confirmation in non-interactive mode. Use --force to skip confirmation."
                )
                return

            confirm = input(
                f"Are you sure you want to delete ALL {visit_count} visits? This cannot be undone! (yes/no): "
            )
            if confirm.lower() not in ["yes", "y"]:
                logger.info("Operation cancelled.")
                return

        # Delete all visits
        deleted_count = db.query(OnsenVisit).delete()
        db.commit()

        logger.info(f"Successfully deleted {deleted_count} visits from database")

        # Verify deletion
        remaining_count = db.query(OnsenVisit).count()
        if remaining_count == 0:
            logger.info("All visits have been removed from the database.")
        else:
            logger.warning(
                f"Warning: {remaining_count} visits still remain in the database."
            )


def drop_visits_by_criteria(args: argparse.Namespace) -> None:
    """
    Drop visits based on specific criteria.
    """
    with get_db(url=CONST.DATABASE_URL) as db:
        query = db.query(OnsenVisit)

        # Apply filters
        if args.onsen_id:
            query = query.filter(OnsenVisit.onsen_id == args.onsen_id)
            logger.info(f"Filtering visits for onsen ID: {args.onsen_id}")

        if args.before_date:
            from datetime import datetime

            try:
                before_date = datetime.strptime(args.before_date, "%Y-%m-%d")
                query = query.filter(OnsenVisit.visit_time < before_date)
                logger.info(f"Filtering visits before: {args.before_date}")
            except ValueError:
                logger.error(
                    f"Invalid before_date format: {args.before_date}. Use YYYY-MM-DD format."
                )
                return

        if args.after_date:
            from datetime import datetime

            try:
                after_date = datetime.strptime(args.after_date, "%Y-%m-%d")
                query = query.filter(OnsenVisit.visit_time > after_date)
                logger.info(f"Filtering visits after: {args.after_date}")
            except ValueError:
                logger.error(
                    f"Invalid after_date format: {args.after_date}. Use YYYY-MM-DD format."
                )
                return

        if args.rating_below:
            query = query.filter(OnsenVisit.personal_rating < args.rating_below)
            logger.info(f"Filtering visits with rating below: {args.rating_below}")

        if args.rating_above:
            query = query.filter(OnsenVisit.personal_rating > args.rating_above)
            logger.info(f"Filtering visits with rating above: {args.rating_above}")

        # Count matching visits
        matching_count = query.count()

        if matching_count == 0:
            logger.info("No visits match the specified criteria.")
            return

        # Confirm deletion unless --force is used
        if not args.force:
            if args.no_interactive:
                logger.error(
                    "Cannot drop visits without confirmation in non-interactive mode. Use --force to skip confirmation."
                )
                return

            confirm = input(
                f"Are you sure you want to delete {matching_count} visits matching the criteria? This cannot be undone! (yes/no): "
            )
            if confirm.lower() not in ["yes", "y"]:
                logger.info("Operation cancelled.")
                return

        # Delete matching visits
        deleted_count = query.delete(synchronize_session=False)
        db.commit()

        logger.info(
            f"Successfully deleted {deleted_count} visits matching the criteria"
        )

        # Show remaining count
        remaining_count = db.query(OnsenVisit).count()
        logger.info(f"Remaining visits in database: {remaining_count}")
