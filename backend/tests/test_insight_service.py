"""Generated insights API tests."""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.services import insight_service as insight_module
from app.services.regression_service import regression_service


def _analyst_token(client: TestClient) -> str:
    email = "insight-analyst@example.com"
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


def _regression_result_id(client: TestClient, token: str) -> str:
    regression_service.clear_results()
    file_id = _upload(
        client,
        token,
        "insight-regression.csv",
        b"x,y,target\n1,2,4\n2,3,7\n3,4,10\n4,5,13\n5,6,16\n6,7,19\n",
    )
    response = client.post(
        f"/api/v1/models/{file_id}/regression",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "algorithm": "linear",
            "target_column": "target",
            "feature_columns": ["x", "y"],
            "test_size": 0.33,
        },
    )
    assert response.status_code == 200
    return response.json()["result_id"]


def test_insight_generate_fallback_and_fetch(client: TestClient) -> None:
    """No LLM config stores a fallback insight."""
    token = _analyst_token(client)
    result_id = _regression_result_id(client, token)

    response = client.post(
        "/api/v1/insights/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "result_id": result_id,
            "analysis_type": "regression",
            "job_id": "job-1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "fallback"
    assert "Key metrics" in body["summary"]

    fetched = client.get(
        f"/api/v1/insights/{body['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert fetched.status_code == 200
    assert fetched.json()["summary"] == body["summary"]

    by_job = client.get(
        "/api/v1/insights/by-job/job-1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert by_job.status_code == 200
    assert by_job.json()["id"] == body["id"]


def test_insight_generate_llm_path_mocked(client: TestClient, monkeypatch) -> None:
    """LLM path is used when config is present and can be mocked."""
    token = _analyst_token(client)
    result_id = _regression_result_id(client, token)
    monkeypatch.setattr(
        insight_module,
        "get_settings",
        lambda: SimpleNamespace(
            llm_api_key="key",
            llm_api_base_url="https://example.invalid/v1/chat/completions",
            llm_model="mock-model",
        ),
    )
    monkeypatch.setattr(
        insight_module.insight_service,
        "_call_llm",
        lambda context: f"Mock LLM summary for {context['model_type']}",
    )

    response = client.post(
        "/api/v1/insights/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"result_id": result_id, "analysis_type": "regression"},
    )

    assert response.status_code == 200
    assert response.json()["source"] == "llm"
    assert response.json()["summary"] == "Mock LLM summary for regression"
