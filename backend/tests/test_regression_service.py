"""Regression service and API tests."""

from fastapi.testclient import TestClient

from app.services.regression_service import regression_service


def _analyst_token(client: TestClient) -> str:
    email = "regression-analyst@example.com"
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


def test_regression_linear_metrics(client: TestClient) -> None:
    """Linear regression returns MAE, RMSE, and R2 on a simple dataset."""
    regression_service.clear_results()
    token = _analyst_token(client)
    content = b"x,y\n" b"1,2\n" b"2,4\n" b"3,6\n" b"4,8\n" b"5,10\n" b"6,12\n"
    file_id = _upload(client, token, "linear.csv", content)

    response = client.post(
        f"/api/v1/models/{file_id}/regression",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "algorithm": "linear",
            "target_column": "y",
            "feature_columns": ["x"],
            "test_size": 0.34,
            "random_state": 42,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["mae"] == 0.0
    assert body["metrics"]["rmse"] == 0.0
    assert body["metrics"]["r2"] == 1.0
    assert len(body["actual_vs_predicted"]) >= 1
    assert len(body["residuals"]) == len(body["actual_vs_predicted"])

    stored = client.get(
        f"/api/v1/models/results/{body['result_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stored.status_code == 200
    assert stored.json()["result_id"] == body["result_id"]


def test_regression_random_forest_feature_importance(client: TestClient) -> None:
    """Random forest returns non-empty feature importance."""
    regression_service.clear_results()
    token = _analyst_token(client)
    content = (
        b"region,units,revenue\n"
        b"North,10,100\n"
        b"North,12,120\n"
        b"South,8,70\n"
        b"South,9,80\n"
        b"East,15,150\n"
        b"East,14,140\n"
        b"West,11,110\n"
    )
    file_id = _upload(client, token, "sales.csv", content)

    response = client.post(
        f"/api/v1/models/{file_id}/regression",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "algorithm": "random_forest",
            "target_column": "revenue",
            "feature_columns": ["units", "region"],
            "test_size": 0.25,
            "random_state": 7,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == "random_forest"
    assert len(body["feature_importance"]) >= 1
    assert any(item["importance"] > 0 for item in body["feature_importance"])


def test_regression_all_algorithms_supported(client: TestClient) -> None:
    """Registry exposes all four regression algorithms."""
    regression_service.clear_results()
    token = _analyst_token(client)
    content = b"a,b\n1,2\n2,4\n3,5\n4,9\n5,10\n6,12\n"
    file_id = _upload(client, token, "all-algos.csv", content)

    registry = client.get(
        "/api/v1/models/registry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert registry.status_code == 200
    algorithm_ids = {item["id"] for item in registry.json()["regression"]}
    assert algorithm_ids == {
        "linear",
        "polynomial",
        "decision_tree",
        "random_forest",
    }

    for algorithm in algorithm_ids:
        response = client.post(
            f"/api/v1/models/{file_id}/regression",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "algorithm": algorithm,
                "target_column": "b",
                "feature_columns": ["a"],
                "test_size": 0.34,
                "random_state": 1,
            },
        )
        assert response.status_code == 200, algorithm
        assert response.json()["algorithm"] == algorithm
