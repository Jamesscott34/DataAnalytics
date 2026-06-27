"""Secure CSV upload endpoint tests."""

from fastapi.testclient import TestClient

from app.config import get_settings
from app.utils.hash_utils import sha256_bytes


def _analyst_token(client: TestClient) -> str:
    """Register an analyst and return an access token."""
    email = "upload-analyst@example.com"
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


def _headers(token: str) -> dict[str, str]:
    """Build auth headers for upload requests."""
    return {"Authorization": f"Bearer {token}"}


def _upload(
    client: TestClient,
    token: str,
    filename: str,
    content: bytes,
    client_sha256: str | None = None,
    duplicate_action: str | None = None,
):
    """Upload bytes as a multipart CSV file."""
    data = {}
    if client_sha256 is not None:
        data["client_sha256"] = client_sha256
    if duplicate_action is not None:
        data["duplicate_action"] = duplicate_action
    return client.post(
        "/api/v1/uploads",
        headers=_headers(token),
        data=data,
        files={"file": (filename, content, "text/csv")},
    )


def test_safe_csv_upload_accepted(client: TestClient) -> None:
    """Safe CSV upload is accepted and returns metadata."""
    token = _analyst_token(client)
    content = b"name,value\nalpha,1\nbeta,2\n"
    response = _upload(client, token, "safe.csv", content)
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "safe.csv"
    assert body["file_hash"] == sha256_bytes(content)
    assert body["row_count"] == 2
    assert body["column_count"] == 2
    assert body["is_duplicate"] is False


def test_non_csv_extension_blocked(client: TestClient) -> None:
    """Files without final .csv extension are rejected."""
    token = _analyst_token(client)
    response = _upload(client, token, "data.txt", b"a,b\n1,2\n")
    assert response.status_code == 400


def test_executable_extension_blocked(client: TestClient) -> None:
    """Executable extensions are rejected."""
    token = _analyst_token(client)
    response = _upload(client, token, "malware.exe", b"a,b\n1,2\n")
    assert response.status_code == 400


def test_double_extension_blocked(client: TestClient) -> None:
    """Double extension ending in an executable suffix is rejected."""
    token = _analyst_token(client)
    response = _upload(client, token, "report.csv.exe", b"a,b\n1,2\n")
    assert response.status_code == 400


def test_path_traversal_blocked(client: TestClient) -> None:
    """Filenames attempting directory traversal are rejected."""
    token = _analyst_token(client)
    response = _upload(client, token, "../evil.csv", b"a,b\n1,2\n")
    assert response.status_code == 400


def test_null_byte_detection(client: TestClient) -> None:
    """Uploaded CSV content containing null bytes is rejected."""
    token = _analyst_token(client)
    response = _upload(client, token, "nulls.csv", b"a,b\n1,\x002\n")
    assert response.status_code == 400


def test_oversized_file_blocked(client: TestClient, monkeypatch) -> None:
    """Files over the configured size limit are rejected."""
    settings = get_settings()
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)
    token = _analyst_token(client)
    response = _upload(client, token, "large.csv", b"a,b\n1,2\n")
    assert response.status_code == 400


def test_invalid_csv_format_returns_400(client: TestClient) -> None:
    """CSV files without a header row are rejected."""
    token = _analyst_token(client)
    response = _upload(client, token, "no-header.csv", b"\n")
    assert response.status_code == 400
    assert response.json()["message"]


def test_duplicate_upload_returns_409_not_500(client: TestClient) -> None:
    """Duplicate uploads return structured 409 responses after audit commits."""
    token = _analyst_token(client)
    content = b"name,value\nalpha,1\n"
    first = _upload(client, token, "dup409-a.csv", content)
    second = _upload(client, token, "dup409-b.csv", content)
    assert first.status_code == 201
    assert second.status_code == 409
    body = second.json()
    assert body["error"] == "duplicate_upload"
    assert body["existing_file"]["original_filename"] == "dup409-a.csv"


def test_duplicate_use_existing_action(client: TestClient) -> None:
    """Users can continue with the existing duplicate file."""
    token = _analyst_token(client)
    content = b"name,value\nbeta,2\n"
    first = _upload(client, token, "keep.csv", content)
    second = _upload(
        client,
        token,
        "keep-copy.csv",
        content,
        duplicate_action="use_existing",
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["is_duplicate"] is True
    assert second.json()["file_id"] == first.json()["file_id"]


def test_duplicate_replace_action(client: TestClient) -> None:
    """Users can replace an existing duplicate with a new upload record."""
    token = _analyst_token(client)
    content = b"name,value\ngamma,3\n"
    first = _upload(client, token, "replace-me.csv", content)
    second = _upload(
        client,
        token,
        "replace-me-new.csv",
        content,
        duplicate_action="replace",
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["is_duplicate"] is False
    assert second.json()["filename"] == "replace-me-new.csv"


def test_delete_upload_requires_admin(client: TestClient) -> None:
    """Only administrators may delete uploaded files."""
    analyst_token = _analyst_token(client)
    content = b"name,value\ndelta,4\n"
    uploaded = _upload(client, analyst_token, "delete-me.csv", content)
    file_id = uploaded.json()["file_id"]
    denied = client.delete(
        f"/api/v1/uploads/{file_id}",
        headers=_headers(analyst_token),
    )
    assert denied.status_code == 403

    admin_email = "upload-admin@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": "password123", "role": "admin"},
    )
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "password123"},
    )
    admin_token = admin_login.json()["access_token"]
    allowed = client.delete(
        f"/api/v1/uploads/{file_id}",
        headers=_headers(admin_token),
    )
    assert allowed.status_code == 200
    assert allowed.json()["message"] == "Uploaded file deleted"


def test_client_hash_match_recorded(client: TestClient) -> None:
    """Browser-provided SHA-256 is compared with backend hash."""
    token = _analyst_token(client)
    content = b"name,value\nalpha,1\n"
    response = _upload(
        client,
        token,
        "hash.csv",
        content,
        client_sha256=sha256_bytes(content),
    )
    assert response.status_code == 201
    assert response.json()["client_hash_match"] is True


def test_client_hash_mismatch_rejected(client: TestClient) -> None:
    """Mismatched browser-provided SHA-256 rejects the upload."""
    token = _analyst_token(client)
    content = b"name,value\nalpha,1\n"
    response = _upload(
        client,
        token,
        "hash-mismatch.csv",
        content,
        client_sha256="0" * 64,
    )
    assert response.status_code == 400
    assert "does not match" in response.json()["message"]
