"""Background EDA job tests."""

from fastapi.testclient import TestClient

from app.models.uploaded_file import FileSource, UploadedFile
from app.services.eda_service import eda_service


def _analyst_token(client: TestClient) -> str:
    email = "eda-bg@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "analyst"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


def test_large_file_eda_queues_background_job(client: TestClient, db_session) -> None:
    """Files above the large-file threshold return 202 and complete via jobs API."""
    eda_service.clear_cache()
    token = _analyst_token(client)
    file = UploadedFile(
        owner_id=1,
        original_filename="large.csv",
        stored_path="large.csv",
        file_hash="c" * 64,
        mime_type="text/csv",
        size_bytes=60 * 1024 * 1024,
        row_count=10,
        column_count=2,
        source=FileSource.UPLOAD,
        is_active=True,
    )
    db_session.add(file)
    db_session.commit()
    db_session.refresh(file)

    response = client.post(
        f"/api/v1/eda/{file.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"force_refresh": True},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["async_job"] is True
    assert body["job_id"]

    job = client.get(
        f"/api/v1/jobs/{body['job_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert job.status_code == 200
    assert job.json()["job_type"] == "eda"


def test_force_background_flag_queues_eda(client: TestClient) -> None:
    """Analysts can force background EDA even for small files."""
    eda_service.clear_cache()
    token = _analyst_token(client)
    upload = client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("small.csv", b"x,y\n1,2\n", "text/csv")},
    )
    file_id = upload.json()["file_id"]
    response = client.post(
        f"/api/v1/eda/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"force_background": True},
    )
    assert response.status_code == 202
    assert response.json()["async_job"] is True
