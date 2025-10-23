from collections.abc import Generator
from contextlib import contextmanager
from typing import Optional
import argparse

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import get_database_config


def is_valid_url(url: str) -> bool:
    """Check if the URL is valid."""
    return isinstance(url, str) and url.startswith("sqlite://")


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
    def get_session(self, url: str) -> Generator[Session]:
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


@contextmanager
def get_db(url: str) -> Generator[Session]:
    """
    A function to yield a SQLAlchemy session.

    Args:
        url: The URL of the database to connect to.

    Yields:
        A SQLAlchemy session.

    Usage:
    ```python
    from src.db.conn import get_db
    from src.config import get_database_config

    config = get_database_config(
        env_override=getattr(args, 'env', None),
        path_override=getattr(args, 'database', None)
    )
    with get_db(url=config.url) as db:
        # Use the db object here
    ```
    """
    assert is_valid_url(url), "url must be provided and a valid SQLite URL"
    with db_manager.get_session(url) as session:
        yield session


@contextmanager
def get_db_from_args(args: Optional[argparse.Namespace] = None) -> Generator[Session]:
    """
    Convenience function to get a database session from CLI args.

    This is a DRY wrapper around get_db() that handles the common pattern
    of extracting database configuration from argparse args.

    Args:
        args: Argparse namespace with optional 'env' and 'database' attributes.
              If None, uses default database configuration.

    Yields:
        A SQLAlchemy session.

    Usage:
    ```python
    from src.db.conn import get_db_from_args

    def cmd_example(args):
        with get_db_from_args(args) as db:
            # Use the db object here
            results = db.query(SomeModel).all()
    ```
    """
    config = get_database_config(
        env_override=getattr(args, 'env', None) if args else None,
        path_override=getattr(args, 'database', None) if args else None
    )
    with get_db(url=config.url) as session:
        yield session
