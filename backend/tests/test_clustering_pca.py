"""Clustering and PCA API tests."""

from fastapi.testclient import TestClient

from app.services.clustering_service import clustering_service
from app.services.pca_service import pca_service


def _analyst_token(client: TestClient) -> str:
    email = "unsupervised-analyst@example.com"
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


def test_clustering_output_shape_and_elbow(client: TestClient) -> None:
    """Clustering returns assignments and elbow inertia values."""
    clustering_service.clear_results()
    token = _analyst_token(client)
    content = (
        b"x,y,group\n"
        b"1,1,A\n"
        b"1.1,0.9,A\n"
        b"5,5,B\n"
        b"5.2,4.8,B\n"
        b"9,1,C\n"
        b"9.2,1.1,C\n"
        b"1.2,1.1,A\n"
        b"5.1,5.2,B\n"
    )
    file_id = _upload(client, token, "clusters.csv", content)

    response = client.post(
        f"/api/v1/models/{file_id}/clustering",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "algorithm": "kmeans",
            "feature_columns": ["x", "y"],
            "n_clusters": 3,
            "max_k": 5,
            "random_state": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_type"] == "clustering"
    assert len(body["assignments"]) == 8
    assert all(0 <= item["cluster"] < 3 for item in body["assignments"])
    assert len(body["elbow"]) == 5
    assert body["elbow"][0]["k"] == 1
    assert body["elbow"][-1]["k"] == 5
    assert body["silhouette"] is not None


def test_pca_variance_and_projections(client: TestClient) -> None:
    """PCA returns explained variance and projected coordinates."""
    pca_service.clear_results()
    token = _analyst_token(client)
    content = (
        b"a,b,c\n"
        b"1,2,3\n"
        b"2,4,6\n"
        b"3,6,9\n"
        b"4,8,12\n"
        b"5,10,15\n"
    )
    file_id = _upload(client, token, "pca-data.csv", content)

    response = client.post(
        f"/api/v1/models/{file_id}/pca",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "feature_columns": ["a", "b", "c"],
            "n_components": 2,
            "random_state": 1,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_type"] == "pca"
    assert body["n_components"] == 2
    assert len(body["components"]) == 2
    assert body["total_explained_variance"] > 0.9
    assert len(body["projections"]) == 5
    assert len(body["projections"][0]) == 2
