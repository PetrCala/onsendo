from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session


def is_valid_db_url(url: str) -> bool:
    """
    Check if the URL is a valid SQLite database URL.
    """
    return isinstance(url, str) and url.startswith("sqlite:///")


def get_db(url: str) -> Generator[Session, None, None]:
    """
    A function to yield a SQLAlchemy session.

    Args:
    - url: The URL of the database to connect to.

    Returns:
    - A generator that yields a SQLAlchemy session.

    Usage:
    ```python
    from src.db.conn import get_db

    with get_db(url=CONST.DATABASE_URL) as db:
        # Use the db object here
    ```
    """
    assert url is not None, "url must be provided"
    assert is_valid_db_url(url), "url must be a valid SQLite database URL"

    engine = create_engine(url, echo=False)  # echo=True for SQL logging
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
