"""Dataset group tests."""

import uuid

from fastapi.testclient import TestClient


def _analyst_token(client: TestClient) -> str:
    email = f"group-analyst-{uuid.uuid4().hex[:8]}@example.com"
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


def test_create_group_and_import_headers(client: TestClient) -> None:
    """Users can group CSV files and import column headers for SQL."""
    token = _analyst_token(client)
    customers = _upload(
        client,
        token,
        "customers.csv",
        b"customer_id,name\n1,Alice\n2,Bob\n",
    )
    prices = _upload(
        client,
        token,
        "prices.csv",
        b"customer_id,price\n1,9.99\n2,4.50\n",
    )

    create = client.post(
        "/api/v1/groups",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Shop data",
            "members": [
                {"file_id": customers},
                {"file_id": prices},
            ],
        },
    )
    assert create.status_code == 201
    group_id = create.json()["id"]
    assert len(create.json()["members"]) == 2

    imported = client.post(
        f"/api/v1/sql/groups/{group_id}/import",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert imported.status_code == 200
    body = imported.json()
    assert body["group_name"] == "Shop data"
    assert len(body["tables"]) == 2
    assert body["tables"][0]["columns"]

    presets = client.get(
        f"/api/v1/sql/groups/{group_id}/presets",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert presets.status_code == 200
    assert any("JOIN" in preset["name"] for preset in presets.json()["presets"])
