"""Standard error response tests."""

from app.main import create_app
from app.utils.response_utils import build_error_response, build_validation_error
from fastapi import status
from fastapi.testclient import TestClient


def test_build_error_response_shape() -> None:
    """Error builder returns error, message, and status_code keys."""
    body = build_error_response("test_error", "Something failed", 400)
    assert body == {
        "error": "test_error",
        "message": "Something failed",
        "status_code": 400,
    }


def test_build_validation_error_status() -> None:
    """Validation helper uses 422 status code."""
    body = build_validation_error("Invalid field")
    assert body["status_code"] == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert body["error"] == "validation_error"


def test_security_headers_on_health(client: TestClient) -> None:
    """Security headers middleware attaches defensive headers."""
    response = client.get("/api/v1/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in response.headers


def test_not_found_returns_standard_error() -> None:
    """Unknown routes return the standard error JSON shape."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert "message" in body
    assert "status_code" in body
