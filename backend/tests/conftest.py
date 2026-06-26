"""Pytest fixtures for API tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI test client for the application.

    Returns:
        Configured TestClient instance.
    """
    return TestClient(app)
