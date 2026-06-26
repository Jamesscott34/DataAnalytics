"""Dataset versioning tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings


def _analyst_token(client: TestClient) -> str:
    """Register an analyst and return an access token."""
    email = "version-analyst@example.com"
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


def _upload(
    client: TestClient,
    token: str,
    filename: str,
    content: bytes,
    duplicate_action: str | None = None,
):
    """Upload bytes as a multipart CSV file."""
    data = {}
    if duplicate_action is not None:
        data["duplicate_action"] = duplicate_action
    return client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        data=data,
        files={"file": (filename, content, "text/csv")},
    )


def test_initial_upload_records_version_one(client: TestClient) -> None:
    """First upload creates version 1 in history."""
    token = _analyst_token(client)
    response = _upload(client, token, "v1.csv", b"name,value\nalpha,1\n")
    assert response.status_code == 201
    body = response.json()
    assert body["version_number"] == 1

    history = client.get(
        f"/api/v1/uploads/{body['file_id']}/versions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert history.status_code == 200
    assert len(history.json()["versions"]) == 1
    assert history.json()["versions"][0]["upload_event"] == "initial_upload"


def test_duplicate_use_existing_increments_version(client: TestClient) -> None:
    """Acknowledging a duplicate records a new version without a new file row."""
    token = _analyst_token(client)
    content = b"name,value\nbeta,2\n"
    first = _upload(client, token, "first-version.csv", content)
    second = _upload(
        client,
        token,
        "second-version.csv",
        content,
        duplicate_action="use_existing",
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["version_number"] == 2
    assert second.json()["file_id"] == first.json()["file_id"]

    history = client.get(
        f"/api/v1/uploads/{first.json()['file_id']}/versions",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert len(history["versions"]) == 2
    assert history["versions"][1]["upload_event"] == "re_upload"


def test_duplicate_does_not_create_second_disk_copy(
    client: TestClient,
    monkeypatch,
) -> None:
    """Duplicate uploads reuse the existing hash-based file on disk."""
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))

    token = _analyst_token(client)
    content = b"name,value\ngamma,3\n"
    first = _upload(client, token, "disk-a.csv", content)
    stored_name = f"{first.json()['file_hash']}.csv"
    stored_path = upload_dir / stored_name
    assert stored_path.exists()
    mtime = stored_path.stat().st_mtime

    second = _upload(
        client,
        token,
        "disk-b.csv",
        content,
        duplicate_action="use_existing",
    )
    assert second.status_code == 201
    assert stored_path.stat().st_mtime == mtime


def test_compare_versions_endpoint(client: TestClient) -> None:
    """Version compare endpoint returns metadata differences."""
    token = _analyst_token(client)
    content = b"name,value\ndelta,4\n"
    first = _upload(client, token, "compare-a.csv", content)
    _upload(
        client,
        token,
        "compare-b.csv",
        content,
        duplicate_action="use_existing",
    )
    file_id = first.json()["file_id"]

    response = client.get(
        f"/api/v1/uploads/{file_id}/versions/compare",
        headers={"Authorization": f"Bearer {token}"},
        params={"version_a": 1, "version_b": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content_identical"] is True
    assert "upload_event" in body["differences"][0]
