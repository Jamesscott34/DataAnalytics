"""Tests for model_results SQL persistence."""

from fastapi.testclient import TestClient

from app.models.model_result import ModelResult
from app.services.business_analytics_service import business_analytics_service
from app.services.regression_service import regression_service


def _analyst_token(client: TestClient) -> str:
    email = "persist-analyst@example.com"
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


def test_regression_result_persisted_to_sql(client: TestClient, db_session) -> None:
    """Regression results are stored in model_results and reloadable."""
    regression_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(
        client,
        token,
        "persist-regression.csv",
        b"x,y\n1,2\n2,4\n3,6\n4,8\n",
    )
    response = client.post(
        f"/api/v1/models/{file_id}/regression",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "algorithm": "linear",
            "target_column": "y",
            "feature_columns": ["x"],
        },
    )
    assert response.status_code == 200
    result_id = response.json()["result_id"]
    count = (
        db_session.query(ModelResult).filter(ModelResult.result_id == result_id).count()
    )
    assert count == 1

    regression_service.clear_results()
    restored = client.get(
        f"/api/v1/models/results/{result_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert restored.status_code == 200
    assert restored.json()["result_id"] == result_id


def test_eda_result_persisted_to_sql(client: TestClient, db_session) -> None:
    """EDA responses are stored in model_results."""
    token = _analyst_token(client)
    file_id = _upload(client, token, "persist-eda.csv", b"a,b\n1,2\n3,4\n")
    response = client.post(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"force_refresh": True},
    )
    assert response.status_code == 200
    result_id = response.json()["result_id"]
    record = (
        db_session.query(ModelResult)
        .filter(ModelResult.result_type == "eda", ModelResult.file_id == file_id)
        .first()
    )
    assert record is not None
    assert record.result_id == result_id


def test_business_result_persisted_to_sql(client: TestClient, db_session) -> None:
    """Business KPI reports are stored in model_results."""
    business_analytics_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(
        client,
        token,
        "persist-business.csv",
        b"job_date,technician,pest_type,customer_region,revenue,cost\n"
        b"2024-01-03,North,Rodent,Avery,240,95\n"
        b"2024-02-02,West,Rodent,Avery,260,105\n",
    )
    response = client.post(
        f"/api/v1/business/{file_id}/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert response.status_code == 200
    result_id = response.json()["result_id"]
    assert (
        db_session.query(ModelResult).filter(ModelResult.result_id == result_id).count()
        == 1
    )
