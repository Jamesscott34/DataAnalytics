"""Similarity and recommendation API tests."""

from fastapi.testclient import TestClient

from app.services.recommendation_service import recommendation_service


def _analyst_token(client: TestClient) -> str:
    email = "similarity-analyst@example.com"
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


def test_similarity_row_mode_top_pairs(client: TestClient) -> None:
    """Row similarity returns top pairs and a preview matrix."""
    recommendation_service.clear_results()
    token = _analyst_token(client)
    content = b"name,views,purchases\n" b"A,10,2\n" b"B,11,2\n" b"C,1,10\n" b"D,2,9\n"
    file_id = _upload(client, token, "similarity.csv", content)

    response = client.post(
        f"/api/v1/models/{file_id}/similarity",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "mode": "row",
            "id_column": "name",
            "feature_columns": ["views", "purchases"],
            "top_n": 3,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model_type"] == "similarity"
    assert body["suitable"] is True
    assert body["similarity_matrix_preview"][0]["label"] == "A"
    assert body["top_pairs"][0]["left"] == "A"
    assert body["top_pairs"][0]["right"] == "B"
    assert body["top_pairs"][0]["score"] > 0.99


def test_similarity_unsuitable_dataset_message(client: TestClient) -> None:
    """Unsuitable data returns a clear note rather than a server error."""
    recommendation_service.clear_results()
    token = _analyst_token(client)
    file_id = _upload(client, token, "bad-similarity.csv", b"name,code\nA,x\nB,y\n")

    response = client.post(
        f"/api/v1/models/{file_id}/similarity",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "mode": "row",
            "id_column": "name",
            "feature_columns": ["code"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["suitable"] is False
    assert "numeric" in body["suitability_note"].lower()
    assert body["top_pairs"] == []
