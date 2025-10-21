import sys
from typing import Optional

from loguru import logger

from src.db.conn import db_manager
from src.db.models import Base
from src.const import CONST


def main(action: Optional[str] = "create"):
    """
    Main entry point.
    - action='create': creates the database/tables from scratch
    - action='drop': drops the database
    - action='recreate': drops + then creates
    """

    logger.info(f"Deploy script called with action={action}")

    if action == "drop":
        drop_all()
    elif action == "create":
        create_all()
    elif action == "recreate":
        drop_all()
        create_all()
    else:
        logger.error(f"Unknown action: {action}")
        sys.exit(1)


def drop_all(database_url: Optional[str] = None):
    """
    Drop all tables in the database.

    Args:
        database_url: Optional database URL. If not provided, uses CONST.DATABASE_URL.
    """
    url = database_url or CONST.DATABASE_URL
    logger.warning(f"Dropping all tables in the database: {url}")
    # Get the engine from db_manager
    engine = db_manager.engines.get(url)
    if engine is None:
        db_manager.add_connection(url)
        engine = db_manager.engines[url]
    Base.metadata.drop_all(bind=engine)


def create_all(database_url: Optional[str] = None):
    """
    Create all tables in the database.

    Args:
        database_url: Optional database URL. If not provided, uses CONST.DATABASE_URL.
    """
    url = database_url or CONST.DATABASE_URL
    logger.info(f"Creating all tables in the database: {url}")
    # Get the engine from db_manager
    engine = db_manager.engines.get(url)
    if engine is None:
        db_manager.add_connection(url)
        engine = db_manager.engines[url]
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    # e.g. python deploy_db.py create
    action_arg = None
    if len(sys.argv) > 1:
        action_arg = sys.argv[1]
    main(action_arg)
