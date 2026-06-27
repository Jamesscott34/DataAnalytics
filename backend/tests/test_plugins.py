"""Analytics plugin registry tests."""

from fastapi.testclient import TestClient

from app.services.analytics_plugins import ANALYTICS_PLUGINS, clear_plugin_results


def _analyst_token(client: TestClient) -> str:
    email = "plugin-analyst@example.com"
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


def _upload(client: TestClient, token: str) -> int:
    content = (
        b"date,revenue,cost,label\n"
        b"2024-01-01,100,40,A\n"
        b"2024-01-02,120,50,B\n"
        b"2024-01-03,90,35,A\n"
        b"2024-01-04,500,200,B\n"
        b"2024-01-05,110,45,A\n"
        b"2024-01-06,115,48,B\n"
    )
    response = client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("plugin-data.csv", content, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["file_id"]


def test_plugins_register_list_and_run(client: TestClient) -> None:
    """Built-in plugins are listed and anomaly detection runs."""
    clear_plugin_results()
    token = _analyst_token(client)
    file_id = _upload(client, token)

    list_response = client.get(
        "/api/v1/plugins",
        headers={"Authorization": f"Bearer {token}"},
        params={"file_id": file_id},
    )
    assert list_response.status_code == 200
    names = {item["name"] for item in list_response.json()["plugins"]}
    assert names == set(ANALYTICS_PLUGINS.keys())
    anomaly = next(
        item
        for item in list_response.json()["plugins"]
        if item["name"] == "anomaly_detection"
    )
    assert anomaly["applicable"] is True

    run_response = client.post(
        "/api/v1/plugins/anomaly_detection/run",
        headers={"Authorization": f"Bearer {token}"},
        json={"file_id": file_id, "params": {}},
    )
    assert run_response.status_code == 200
    body = run_response.json()
    assert body["plugin_name"] == "anomaly_detection"
    assert "anomalous rows" in body["summary"]


def test_plugins_hide_inapplicable_for_empty_numeric(client: TestClient) -> None:
    """Plugins mark inapplicable when dataset lacks required columns."""
    token = _analyst_token(client)
    response = client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("text-only.csv", b"name,notes\nfoo,bar\n", "text/csv")},
    )
    assert response.status_code == 201
    file_id = response.json()["file_id"]

    list_response = client.get(
        "/api/v1/plugins",
        headers={"Authorization": f"Bearer {token}"},
        params={"file_id": file_id},
    )
    anomaly = next(
        item
        for item in list_response.json()["plugins"]
        if item["name"] == "anomaly_detection"
    )
    assert anomaly["applicable"] is False
