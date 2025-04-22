from typing import Generator
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager


class DatabaseConnection:
    """Manages database connections and sessions."""

    def __init__(self):
        self.engines: dict[str, Engine] = {}
        self.session_factories: dict[str, sessionmaker] = {}

    def add_connection(self, url: str, echo: bool = False) -> None:
        """
        Add a new database connection.

        Args:
            url: Database connection URL
            echo: Whether to log SQL statements
        """
        if url in self.engines:
            return

        engine = create_engine(url, echo=echo)
        self.engines[url] = engine
        self.session_factories[url] = sessionmaker(
            bind=engine, autoflush=False, autocommit=False
        )

    def remove_connection(self, url: str) -> None:
        """Remove a database connection and dispose of its engine."""
        if url in self.engines:
            self.engines[url].dispose()
            del self.engines[url]
            del self.session_factories[url]

    @contextmanager
    def get_session(self, url: str) -> Generator[Session, None, None]:
        """
        Get a database session for the specified URL.

        Args:
            url: Database connection URL

        Yields:
            SQLAlchemy Session object

        Raises:
            SQLAlchemyError: If connection fails
        """
        if url not in self.session_factories:
            self.add_connection(url)

        session = self.session_factories[url]()
        try:
            yield session
        finally:
            session.close()


db_manager = DatabaseConnection()


def get_db(url: str) -> Generator[Session, None, None]:
    """
    A function to yield a SQLAlchemy session.

    Args:
        url: The URL of the database to connect to.

    Returns:
        A generator that yields a SQLAlchemy session.

    Usage:
    ```python
    from src.db.conn import get_db

    with get_db(url=CONST.DATABASE_URL) as db:
        # Use the db object here
    ```
    """
    assert url is not None, "url must be provided"
    yield from db_manager.get_session(url)
