"""Temp assets listing and selection tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings


def _analyst_token(client: TestClient) -> str:
    """Register an analyst and return an access token."""
    email = "assets-analyst@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "analyst"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_list_assets_returns_csv_files(client: TestClient) -> None:
    """Asset listing includes safe CSV files from temp_assets."""
    token = _analyst_token(client)
    response = client.get(
        "/api/v1/assets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["files"]}
    assert "pest_control_sample.csv" in names


def test_select_asset_imports_csv(client: TestClient, monkeypatch) -> None:
    """Selecting a temp asset imports it through the upload pipeline."""
    settings = get_settings()
    assets_dir = Path(settings.temp_assets_dir)
    monkeypatch.setattr(settings, "temp_assets_dir", str(assets_dir))

    token = _analyst_token(client)
    response = client.post(
        "/api/v1/assets/select",
        headers={"Authorization": f"Bearer {token}"},
        json={"filename": "pest_control_sample.csv"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "pest_control_sample.csv"
    assert body["row_count"] == 8
    assert body["column_count"] == 7
    assert body["scan_result"]["status"] in {"safe", "warning"}


def test_select_asset_rejects_path_traversal(client: TestClient) -> None:
    """Path traversal filenames are rejected."""
    token = _analyst_token(client)
    response = client.post(
        "/api/v1/assets/select",
        headers={"Authorization": f"Bearer {token}"},
        json={"filename": "../evil.csv"},
    )
    assert response.status_code == 400
