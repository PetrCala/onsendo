#!/usr/bin/env python3
"""
Database initialization script.
Creates the database file and tables if they don't exist.
"""

import os
from sqlalchemy import create_engine
from src.db.models import Base
from src.const import CONST


def init_database():
    """Initialize the database and create tables."""
    data_dir = os.path.dirname(CONST.DATABASE_URL.replace("sqlite:///", ""))
    os.makedirs(data_dir, exist_ok=True)

    # Create engine and tables
    engine = create_engine(CONST.DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    print(f"Database initialized at: {CONST.DATABASE_URL}")
    print("Tables created successfully!")


if __name__ == "__main__":
    init_database()
