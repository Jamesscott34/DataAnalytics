"""Explainability API tests."""

from fastapi.testclient import TestClient

from app.services.classification_service import classification_service
from app.services.regression_service import regression_service


def _analyst_token(client: TestClient) -> str:
    email = "explainability-analyst@example.com"
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


def test_explainability_returns_regression_feature_importance(client: TestClient) -> None:
    """Regression explainability exposes fallback feature importance."""
    regression_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(
        client,
        token,
        "regression-explain.csv",
        b"x,y,target\n1,2,4\n2,3,7\n3,4,10\n4,5,13\n5,6,16\n6,7,19\n",
    )
    train_response = client.post(
        f"/api/v1/models/{file_id}/regression",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "algorithm": "linear",
            "target_column": "target",
            "feature_columns": ["x", "y"],
            "test_size": 0.33,
        },
    )
    assert train_response.status_code == 200
    result_id = train_response.json()["result_id"]

    response = client.get(
        f"/api/v1/explainability/{result_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_type"] == "regression"
    assert body["feature_importance"]
    assert "SHAP" in body["summary_text"]

    shap_response = client.post(
        f"/api/v1/explainability/{result_id}/shap",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert shap_response.status_code == 200
    assert shap_response.json()["supported"] is False


def test_explainability_returns_classification_confidence(client: TestClient) -> None:
    """Classification explainability summarizes confidence scores."""
    classification_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(
        client,
        token,
        "classification-explain.csv",
        b"x,y,label\n1,1,A\n1.1,1,A\n5,5,B\n5.1,5,B\n1.2,1,A\n5.2,5,B\n",
    )
    train_response = client.post(
        f"/api/v1/models/{file_id}/classification",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "algorithm": "logistic",
            "target_column": "label",
            "feature_columns": ["x", "y"],
            "test_size": 0.33,
        },
    )
    assert train_response.status_code == 200
    result_id = train_response.json()["result_id"]

    response = client.get(
        f"/api/v1/explainability/{result_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    confidence = response.json()["confidence_scores"]
    assert confidence["available"] is True
    assert confidence["average"] is not None
