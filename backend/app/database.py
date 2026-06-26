"""SQLAlchemy database engine and session configuration.

Configures the engine, session factory, and declarative base only.
ORM models live in ``app.models``; this module does not define tables.
"""

from collections.abc import AsyncIterator, Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _create_engine() -> Engine:
    """Create SQLAlchemy engine from current settings."""
    settings = get_settings()
    connect_args: dict[str, object] = {}
    if settings.database_url.startswith("sqlite"):
        # SQLite requires single-thread check disabled for FastAPI TestClient.
        connect_args["check_same_thread"] = False
    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
