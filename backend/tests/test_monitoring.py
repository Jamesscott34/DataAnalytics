"""Monitoring endpoint tests."""

from fastapi.testclient import TestClient

from app.services.monitoring_service import monitoring_service


def _viewer_token(client: TestClient) -> str:
    email = "monitor-viewer@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "viewer"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_monitoring_health_reports_database(client: TestClient) -> None:
    """Detailed health includes database connectivity."""
    token = _viewer_token(client)
    response = client.get(
        "/api/v1/monitoring/health",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"]["connected"] is True


def test_monitoring_metrics_counts_requests(client: TestClient) -> None:
    """Metrics endpoint returns request counters after traffic."""
    token = _viewer_token(client)
    client.get("/api/v1/health")
    client.get(
        "/api/v1/monitoring/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/api/v1/monitoring/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_requests"] >= monitoring_service.metrics().total_requests - 5
    assert body["total_requests"] > 0
