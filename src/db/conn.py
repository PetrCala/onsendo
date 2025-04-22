from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from src import CONST

DATABASE_URL = CONST.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)  # echo=True for SQL logging
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """
    A function to yield a SQLAlchemy session.

    Usage:
    ```python
    from src.db.conn import get_db

    with get_db() as db:
        # Use the db object here
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
