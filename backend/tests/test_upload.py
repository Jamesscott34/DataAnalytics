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


def _upload(client: TestClient, token: str, filename: str, content: bytes):
    """Upload bytes as a multipart CSV file."""
    return client.post(
        "/api/v1/uploads",
        headers=_headers(token),
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
    """Malformed CSV parser errors are converted to client errors."""
    token = _analyst_token(client)
    response = _upload(client, token, "bad-newline.csv", b'a,b\n"broken\n1,2\n')
    assert response.status_code == 400
    assert response.json()["message"]


def test_duplicate_file_detection_returns_existing_hash(client: TestClient) -> None:
    """Uploading the same CSV twice returns duplicate metadata."""
    token = _analyst_token(client)
    content = b"name,value\nalpha,1\n"
    first = _upload(client, token, "first.csv", content)
    second = _upload(client, token, "second.csv", content)
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["is_duplicate"] is True
    assert second.json()["file_hash"] == first.json()["file_hash"]
    assert second.json()["file_id"] == first.json()["file_id"]
