"""EDA service and API tests."""

from fastapi.testclient import TestClient

from app.services.eda_service import eda_service


def _analyst_token(client: TestClient) -> str:
    email = "eda-analyst@example.com"
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


def _upload(client: TestClient, token: str, filename: str, content: bytes) -> int:
    response = client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, content, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["file_id"]


def test_eda_summary_includes_types_missing_and_stats(client: TestClient) -> None:
    """EDA returns column types, missing values, and numeric/categorical stats."""
    eda_service.clear_cache()
    token = _analyst_token(client)
    content = (
        b"region,pest_type,incidents,month,notes\n"
        b"North,rodent,12,January,\n"
        b"South,insect,8,January,NA\n"
        b"East,rodent,5,February,\n"
    )
    file_id = _upload(client, token, "pest.csv", content)

    response = client.post(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"force_refresh": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["row_count"] == 3
    assert body["summary"]["column_count"] == 5
    assert body["cached"] is False

    columns = {column["name"]: column for column in body["columns"]}
    assert columns["incidents"]["inferred_type"] == "integer"
    assert columns["incidents"]["numeric_stats"]["mean"] == 8.3333
    assert columns["pest_type"]["inferred_type"] == "categorical"
    assert columns["pest_type"]["categorical_stats"]["unique_count"] == 2
    assert columns["notes"]["missing_count"] == 3
    assert any("missing" in warning.lower() for warning in body["quality_warnings"])
    assert "incidents" in body["chart_data"]


def test_eda_cache_by_hash(client: TestClient) -> None:
    """Second request returns cached EDA for the same file hash."""
    eda_service.clear_cache()
    token = _analyst_token(client)
    content = b"name,value\nalpha,1\n"
    file_id = _upload(client, token, "cache-a.csv", content)

    first = client.post(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert first.status_code == 200
    assert first.json()["cached"] is False

    second = client.post(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert second.status_code == 200
    assert second.json()["cached"] is True

    cached_get = client.get(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cached_get.status_code == 200
    assert cached_get.json()["cached"] is True


def test_eda_column_detail_and_suggestions(client: TestClient) -> None:
    """Column detail and suggestions endpoints return structured data."""
    eda_service.clear_cache()
    token = _analyst_token(client)
    content = (
        b"date,amount,category\n"
        b"2024-01-01,10.5,A\n"
        b"2024-02-01,20.0,B\n"
        b"2024-03-01,30.0,A\n"
    )
    file_id = _upload(client, token, "biz.csv", content)
    client.post(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    column = client.get(
        f"/api/v1/eda/{file_id}/columns/amount",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert column.status_code == 200
    assert column.json()["inferred_type"] == "float"

    suggestions = client.get(
        f"/api/v1/eda/{file_id}/suggestions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert suggestions.status_code == 200
    body = suggestions.json()
    assert "date" in body["date_columns"]
    assert "amount" in body["feature_columns"]
    assert "time_series" in body["suggested_analyses"]
