"""SQLAlchemy database engine and session configuration.

Configures the engine, session factory, and declarative base only.
ORM models live in ``app.models``; this module does not define tables.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Default SQLite URL for local development; overridden via config in later tasks.
DATABASE_URL = "sqlite:///./data/app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for FastAPI dependency injection.

    Yields:
        SQLAlchemy session closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
