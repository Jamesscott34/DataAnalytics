"""Classification service and API tests."""

from fastapi.testclient import TestClient

from app.services.classification_service import classification_service


def _analyst_token(client: TestClient) -> str:
    email = "classification-analyst@example.com"
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


def test_classification_metrics_and_confusion_matrix(client: TestClient) -> None:
    """Classification returns accuracy, F1, confusion matrix, and confidence."""
    classification_service.clear_results()
    token = _analyst_token(client)
    content = (
        b"color,size,label\n"
        b"red,small,A\n"
        b"red,large,A\n"
        b"blue,small,B\n"
        b"blue,large,B\n"
        b"red,small,A\n"
        b"blue,large,B\n"
        b"red,large,A\n"
        b"blue,small,B\n"
    )
    file_id = _upload(client, token, "shapes.csv", content)

    response = client.post(
        f"/api/v1/models/{file_id}/classification",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "algorithm": "logistic",
            "target_column": "label",
            "feature_columns": ["color", "size"],
            "test_size": 0.25,
            "random_state": 3,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_type"] == "classification"
    assert body["metrics"]["accuracy"] >= 0.5
    assert body["metrics"]["f1"] >= 0.0
    assert len(body["confusion_matrix"]["labels"]) == 2
    assert len(body["confusion_matrix"]["matrix"]) == 2
    assert len(body["predictions"]) >= 1
    assert any(item["confidence"] is not None for item in body["predictions"])

    stored = client.get(
        f"/api/v1/models/results/{body['result_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stored.status_code == 200
    assert stored.json()["model_type"] == "classification"


def test_classification_all_algorithms_supported(client: TestClient) -> None:
    """Registry exposes all six classification algorithms."""
    classification_service.clear_results()
    token = _analyst_token(client)
    content = (
        b"x1,x2,group\n"
        b"1,1,A\n"
        b"2,2,A\n"
        b"8,8,B\n"
        b"9,9,B\n"
        b"1,2,A\n"
        b"8,9,B\n"
        b"2,1,A\n"
    )
    file_id = _upload(client, token, "groups.csv", content)

    registry = client.get(
        "/api/v1/models/registry",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert registry.status_code == 200
    algorithm_ids = {item["id"] for item in registry.json()["classification"]}
    assert algorithm_ids == {
        "logistic",
        "decision_tree",
        "random_forest",
        "knn",
        "svm",
        "naive_bayes",
    }

    for algorithm in algorithm_ids:
        response = client.post(
            f"/api/v1/models/{file_id}/classification",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "algorithm": algorithm,
                "target_column": "group",
                "feature_columns": ["x1", "x2"],
                "test_size": 0.25,
                "random_state": 1,
            },
        )
        assert response.status_code == 200, algorithm
        assert response.json()["algorithm"] == algorithm
