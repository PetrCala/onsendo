from src import CONST
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from src.db.models import Base


def get_mock_engine() -> Engine:
    """Get a SQLAlchemy engine for the mock database."""
    return create_engine(url=CONST.MOCK_DATABASE_URL)


def get_mock_db() -> Session:
    """Get a SQLAlchemy session for the mock database."""
    engine = get_mock_engine()

    # Create all tables from the Base metadata
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
