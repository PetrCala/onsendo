import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src import PATHS


def get_mock_db_url(filename: Optional[str] = None) -> str:
    """
    Get a database URL for a mock database.

    Args:
        filename (str, optional): The name of the database file.

    Returns:
        str: A database URL for a mock database.
    """
    filename = filename if filename is not None else "test.db"

    assert isinstance(filename, str), "filename must be a string"
    assert filename.endswith(".db"), "filename must end with .db"

    return f"sqlite:///{os.path.join(PATHS.TMP_DATA_DIR, filename)}"


def get_mock_engine(filename: Optional[str] = None):
    """Get a SQLAlchemy engine for the mock database."""
    url = get_mock_db_url(filename)
    return create_engine(url)


def get_mock_session(filename: Optional[str] = None) -> Session:
    """Get a SQLAlchemy session for the mock database."""
    engine = get_mock_engine(filename)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
