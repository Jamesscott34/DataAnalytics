"""EDA chart payload tests."""

from fastapi.testclient import TestClient

from app.services.eda_service import eda_service


def _analyst_token(client: TestClient) -> str:
    email = "eda-charts@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "analyst"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


def _upload(client: TestClient, token: str, filename: str, content: bytes) -> int:
    response = client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, content, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["file_id"]


def test_eda_includes_scatter_line_and_correlation_charts(client: TestClient) -> None:
    """EDA dataset_charts includes scatter, line, and correlation payloads."""
    eda_service.clear_cache()
    token = _analyst_token(client)
    content = (
        b"job_date,revenue,cost,incidents\n"
        b"2024-01-03,240,95,2\n"
        b"2024-02-02,260,105,3\n"
        b"2024-03-04,190,75,1\n"
    )
    file_id = _upload(client, token, "eda-charts.csv", content)
    response = client.post(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"force_refresh": True},
    )
    assert response.status_code == 200
    charts = response.json()["dataset_charts"]
    assert charts["correlation"]["type"] == "correlation"
    assert len(charts["correlation"]["labels"]) >= 2
    assert charts["scatter"]
    assert charts["line"]


def test_eda_omits_correlation_for_single_numeric_column(client: TestClient) -> None:
    """EDA skips correlation and scatter charts when fewer than two numeric columns."""
    eda_service.clear_cache()
    token = _analyst_token(client)
    file_id = _upload(
        client,
        token,
        "single-numeric.csv",
        b"name,score\nalice,10\nbob,20\n",
    )
    response = client.post(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"force_refresh": True},
    )
    assert response.status_code == 200
    charts = response.json()["dataset_charts"]
    assert "correlation" not in charts
    assert not charts.get("scatter")


def test_eda_samples_large_datasets(client: TestClient, monkeypatch) -> None:
    """EDA marks sampled=True and warns when row count exceeds the sample limit."""
    eda_service.clear_cache()
    monkeypatch.setenv("EDA_SAMPLE_MAX_ROWS", "2")
    from app.config import get_settings

    get_settings.cache_clear()

    token = _analyst_token(client)
    file_id = _upload(
        client,
        token,
        "large-sample.csv",
        b"x,y\n1,2\n2,3\n3,4\n4,5\n",
    )
    response = client.post(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"force_refresh": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sampled"] is True
    assert any("sampled" in warning.lower() for warning in body["quality_warnings"])

    get_settings.cache_clear()
