"""Ragged CSV parsing tests."""

from fastapi.testclient import TestClient

from app.utils.csv_parse_utils import parse_csv_rows


def test_parse_csv_rows_pads_ragged_market_basket_rows() -> None:
    """Market-basket style rows are padded instead of rejected."""
    text = "items\nbread,milk\nbread,butter,eggs\n"
    headers, rows, warnings = parse_csv_rows(text)
    assert headers == ["items", "item_1", "item_2"]
    assert len(rows) == 2
    assert rows[1][2] == "eggs"
    assert warnings


def test_upload_accepts_ragged_csv(client: TestClient) -> None:
    """Upload accepts variable-width market basket CSV files."""
    email = "ragged-uploader@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "analyst"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login.json()["access_token"]
    content = b"items\nbread,milk\nbread,butter,eggs\n"
    response = client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("market_basket.csv", content, "text/csv")},
    )
    assert response.status_code == 201
    assert response.json()["column_count"] == 3


def test_eda_handles_ragged_csv_consistently(client: TestClient) -> None:
    """EDA reports padded columns and ragged-row warnings for market basket CSV."""
    email = "ragged-eda@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "analyst"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login.json()["access_token"]
    content = b"items\nbread,milk\nbread,butter,eggs\n"
    upload_response = client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("market_basket.csv", content, "text/csv")},
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["file_id"]

    eda_response = client.post(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"force_refresh": True},
    )
    assert eda_response.status_code == 200
    body = eda_response.json()

    assert any("ragged" in warning.lower() for warning in body["quality_warnings"])
    assert body["summary"]["column_count"] == 3
    column_names = [column["name"] for column in body["columns"]]
    assert column_names == ["items", "item_1", "item_2"]
