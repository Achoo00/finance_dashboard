"""Database session management."""
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields db sessions.

    Yields:
        Session: A database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Yields:
        Session: A database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_db_connection() -> None:
    """
    Get a raw database connection.
    """
    return engine.connect()


def init_db() -> None:
    """
    Initialize the database.

    This function should be called during application startup to ensure
    all models are properly registered and the database is created.
    """
    from app.database.models.base import Base  # noqa

    # Import models to ensure they are registered with SQLAlchemy
    import app.database.models.portfolio  # noqa
    import app.database.models.market_data  # noqa

    # Create all tables
    Base.metadata.create_all(bind=engine)
