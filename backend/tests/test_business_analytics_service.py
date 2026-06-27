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


def test_business_kpis_repeat_customers_and_growth(client: TestClient) -> None:
    """Business preset computes repeat customers, growth, forecast, and best service."""
    import pytest

    business_analytics_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(
        client,
        token,
        "business-kpis.csv",
        (
            b"order_date,customer_id,pest_type,revenue,cost\n"
            b"2024-01-05,CUST-1,Commercial Extermination,1000,400\n"
            b"2024-01-20,CUST-2,Residential Treatment,500,150\n"
            b"2024-02-03,CUST-1,Commercial Extermination,1500,600\n"
            b"2024-02-18,CUST-3,Residential Treatment,250,80\n"
            b"2024-03-02,CUST-1,Commercial Extermination,2000,800\n"
        ),
    )

    response = client.post(
        f"/api/v1/business/{file_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 200
    kpis = {item["label"]: item["value"] for item in response.json()["kpis"]}

    assert kpis["Repeat customers"] == 1
    assert kpis["Month-over-month growth"] == pytest.approx(14.29, rel=1e-2)
    assert kpis["Next month forecast"] == pytest.approx(2250.0, rel=1e-2)
    assert kpis["Best performing service"] == "Commercial Extermination (4500.0)"


def test_pest_control_kpis_include_operational_metrics(client: TestClient) -> None:
    """Pest control preset computes technician, pest, and forecast KPIs."""
    business_analytics_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(
        client,
        token,
        "pest-kpis.csv",
        (
            b"job_date,customer_region,pest_type,technician,revenue,cost\n"
            b"2024-01-03,North,Rodent,Avery,240,95\n"
            b"2024-01-08,South,Ants,Blake,180,70\n"
            b"2024-02-02,West,Rodent,Avery,260,105\n"
            b"2024-02-14,North,Wasps,Devon,310,120\n"
        ),
    )
    response = client.post(
        f"/api/v1/business/{file_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 200
    body = response.json()
    labels = {item["label"] for item in body["kpis"]}
    assert "Total jobs" in labels
    assert "January sales" in labels
    assert "Busiest month" in labels
    assert body["jobs_by_technician"]
    assert body["jobs_by_pest"]
    assert body["jobs_by_location"]
    assert body["yearly_revenue"]


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
