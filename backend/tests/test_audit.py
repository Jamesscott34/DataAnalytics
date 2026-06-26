"""Audit logging tests."""

from fastapi.testclient import TestClient

from app.services.audit_service import audit_service


def _analyst_token(client: TestClient) -> str:
    """Register an analyst and return an access token."""
    email = "audit-analyst@example.com"
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


def _admin_token(client: TestClient) -> str:
    """Register an admin and return an access token."""
    email = "audit-admin@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "role": "admin"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _upload(client: TestClient, token: str, filename: str, content: bytes):
    """Upload bytes as a multipart CSV file."""
    return client.post(
        "/api/v1/uploads",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, content, "text/csv")},
    )


def test_upload_creates_upload_and_scan_audit_entries(
    client: TestClient,
    db_session,
) -> None:
    """Successful uploads persist upload and scan audit events."""
    token = _analyst_token(client)
    response = _upload(client, token, "audit.csv", b"name,value\nalpha,1\n")
    assert response.status_code == 201

    upload_count = audit_service.count_for_event(
        db_session,
        event_type="upload",
        action="store",
    )
    scan_count = audit_service.count_for_event(
        db_session,
        event_type="scan",
        action="persist",
    )
    assert upload_count == 1
    assert scan_count == 1


def test_admin_can_list_audit_logs(client: TestClient, db_session) -> None:
    """Admins can list persisted audit entries."""
    analyst_token = _analyst_token(client)
    admin_token = _admin_token(client)
    _upload(client, analyst_token, "audit-list.csv", b"name,value\nbeta,2\n")

    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    assert any(item["event_type"] == "upload" for item in body["items"])


def test_analyst_cannot_list_all_audit_logs(client: TestClient) -> None:
    """Non-admin users cannot access the global audit list."""
    token = _analyst_token(client)
    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_file_owner_can_list_file_audit_logs(client: TestClient) -> None:
    """File owners can view audit entries for their uploads."""
    token = _analyst_token(client)
    uploaded = _upload(client, token, "audit-owner.csv", b"name,value\ngamma,3\n")
    file_id = uploaded.json()["file_id"]

    response = client.get(
        f"/api/v1/audit/{file_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1
