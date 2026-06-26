"""SQL analysis service and API tests."""

from fastapi.testclient import TestClient


def _analyst_token(client: TestClient) -> str:
    import uuid

    email = f"sql-analyst-{uuid.uuid4().hex[:8]}@example.com"
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


def test_import_rows_creates_queryable_table(client: TestClient) -> None:
    """Import stores rows and exposes a SQLite table name."""
    token = _analyst_token(client)
    content = (
        b"region,pest_type,incidents\n"
        b"North,rodent,12\n"
        b"South,insect,8\n"
        b"East,rodent,5\n"
    )
    file_id = _upload(client, token, "sql-pest.csv", content)

    response = client.post(
        f"/api/v1/sql/{file_id}/import",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["imported_rows"] == 3
    assert body["table_name"] == f"csv_import_{file_id}"
    assert body["columns"] == ["region", "pest_type", "incidents"]


def test_group_by_preset_returns_counts(client: TestClient) -> None:
    """Group-by preset runs real SQL against imported rows."""
    token = _analyst_token(client)
    content = (
        b"region,pest_type,incidents\n"
        b"North,rodent,12\n"
        b"South,insect,8\n"
        b"East,rodent,5\n"
    )
    file_id = _upload(client, token, "sql-group.csv", content)
    client.post(
        f"/api/v1/sql/{file_id}/import",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    presets = client.get(
        f"/api/v1/sql/{file_id}/presets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert presets.status_code == 200
    preset_ids = {preset["id"] for preset in presets.json()["presets"]}
    assert "group_by_count" in preset_ids

    result = client.post(
        f"/api/v1/sql/{file_id}/presets/group_by_count/run",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert result.status_code == 200
    body = result.json()
    assert body["row_count"] >= 1
    assert "row_count" in body["columns"]


def test_destructive_sql_is_rejected(client: TestClient) -> None:
    """Write queries are blocked by the read-only validator."""
    token = _analyst_token(client)
    file_id = _upload(client, token, "sql-safe.csv", b"name,value\nalpha,1\n")
    import_response = client.post(
        f"/api/v1/sql/{file_id}/import",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    table_name = import_response.json()["table_name"]

    response = client.post(
        f"/api/v1/sql/{file_id}/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": f'DELETE FROM "{table_name}"'},
    )
    assert response.status_code == 400
    body = response.json()
    error_text = (body.get("detail") or body.get("message") or "").lower()
    assert "not allowed" in error_text
