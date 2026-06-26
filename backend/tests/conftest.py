"""Pytest fixtures for API tests."""

from collections.abc import Generator

import pytest
from app.database import Base, SessionLocal, engine, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session


@pytest.fixture(scope="session", autouse=True)
def create_tables() -> Generator[None, None, None]:
    """Create database tables once per test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a database session cleared after each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(delete(table))
        session.commit()
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI test client with database dependency override."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
