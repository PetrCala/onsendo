from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

DATABASE_URL = "sqlite:///onsen.db"  # Or you can parametrize this

engine = create_engine(DATABASE_URL, echo=False)  # echo=True for SQL logging
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    """
    A function to yield a SQLAlchemy session.
    In a web framework, you'd typically use this in a request context.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
