"""Business analytics API tests."""

from fastapi.testclient import TestClient

from app.services.business_analytics_service import business_analytics_service


def _analyst_token(client: TestClient) -> str:
    email = "business-analyst@example.com"
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


def test_business_kpis_match_raw_calculations(client: TestClient) -> None:
    """Business KPI totals match raw CSV calculations."""
    business_analytics_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(
        client,
        token,
        "business.csv",
        b"date,revenue,cost\n2024-01-01,100,40\n2024-01-15,50,10\n2024-02-01,200,80\n",
    )

    response = client.post(
        f"/api/v1/business/{file_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "date_column": "date",
            "revenue_column": "revenue",
            "cost_column": "cost",
        },
    )

    assert response.status_code == 200
    body = response.json()
    kpis = {item["label"]: item["value"] for item in body["kpis"]}
    assert kpis["Total revenue"] == 350
    assert kpis["Total cost"] == 130
    assert kpis["Gross margin"] == 220
    assert kpis["Margin %"] == 62.86
    assert body["revenue_by_month"][0] == {"label": "2024-01", "value": 150}

    latest = client.get(
        f"/api/v1/business/{file_id}/kpis",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert latest.status_code == 200
    assert latest.json()["result_id"] == body["result_id"]


def test_business_unsuitable_dataset_message(client: TestClient) -> None:
    """Datasets without revenue-like columns return a helpful note."""
    business_analytics_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(client, token, "not-business.csv", b"name,category\nA,x\nB,y\n")

    response = client.post(
        f"/api/v1/business/{file_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 200
    assert response.json()["kpis"] == []
    assert "revenue" in response.json()["suitability_note"].lower()
