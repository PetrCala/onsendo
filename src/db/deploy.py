import sys
from typing import Optional
from loguru import logger
from sqlalchemy_utils import database_exists, create_database, drop_database
from src.db.conn import engine
from src.db.models import Base

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

def drop_all():
    logger.warning("Dropping all tables in the database.")
    Base.metadata.drop_all(bind=engine)

def create_all():
    logger.info("Creating all tables in the database.")
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # e.g. python deploy_db.py create
    action_arg = None
    if len(sys.argv) > 1:
        action_arg = sys.argv[1]
    main(action_arg)
