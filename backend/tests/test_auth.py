"""Authentication and RBAC tests."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from jose import jwt

from app.config import get_settings


def _register(
    client: TestClient,
    email: str,
    password: str = "password123",
    **kwargs: object,
) -> dict:
    """Helper to register a user and return the JSON body."""
    payload = {"email": email, "password": password, **kwargs}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


def _login(client: TestClient, email: str, password: str = "password123") -> dict:
    """Helper to login and return token payload."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def _auth_header(access_token: str) -> dict[str, str]:
    """Build Authorization header dict."""
    return {"Authorization": f"Bearer {access_token}"}


def test_register_and_login_succeed(client: TestClient) -> None:
    """User registration and login return valid tokens."""
    _register(client, "analyst@example.com", role="analyst")
    tokens = _login(client, "analyst@example.com")
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]


def test_invalid_credentials_rejected(client: TestClient) -> None:
    """Login with wrong password returns 401."""
    _register(client, "user@example.com")
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401


def test_me_requires_valid_token(client: TestClient) -> None:
    """Authenticated /me returns user profile."""
    _register(client, "viewer@example.com", role="viewer")
    tokens = _login(client, "viewer@example.com")
    response = client.get(
        "/api/v1/auth/me",
        headers=_auth_header(tokens["access_token"]),
    )
    assert response.status_code == 200
    assert response.json()["email"] == "viewer@example.com"


def test_expired_token_rejected(client: TestClient) -> None:
    """Expired access token is rejected."""
    user = _register(client, "expired@example.com")
    settings = get_settings()
    expired = jwt.encode(
        {
            "sub": str(user["id"]),
            "role": "viewer",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    response = client.get("/api/v1/auth/me", headers=_auth_header(expired))
    assert response.status_code == 401


def test_refresh_token_rotation(client: TestClient) -> None:
    """Refresh endpoint returns a new token pair and revokes the old refresh token."""
    _register(client, "refresh@example.com")
    tokens = _login(client, "refresh@example.com")
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    reuse = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert reuse.status_code == 401


def test_viewer_cannot_upload(client: TestClient) -> None:
    """Viewer role is blocked from analyst upload guard endpoint."""
    _register(client, "viewer2@example.com", role="viewer")
    tokens = _login(client, "viewer2@example.com")
    response = client.post(
        "/api/v1/uploads/guard",
        headers=_auth_header(tokens["access_token"]),
    )
    assert response.status_code == 403


def test_analyst_can_upload_guard(client: TestClient) -> None:
    """Analyst role passes upload permission guard."""
    _register(client, "analyst2@example.com", role="analyst")
    tokens = _login(client, "analyst2@example.com")
    response = client.post(
        "/api/v1/uploads/guard",
        headers=_auth_header(tokens["access_token"]),
    )
    assert response.status_code == 200


def test_analyst_cannot_delete_users(client: TestClient) -> None:
    """Analyst cannot delete user accounts (admin only)."""
    analyst = _register(client, "analyst3@example.com", role="analyst")
    victim = _register(client, "victim@example.com", role="viewer")
    tokens = _login(client, "analyst3@example.com")
    response = client.delete(
        f"/api/v1/users/{victim['id']}",
        headers=_auth_header(tokens["access_token"]),
    )
    assert response.status_code == 403
    assert analyst["id"] != victim["id"]


def test_admin_can_delete_user(client: TestClient) -> None:
    """Admin can delete another user account."""
    admin = _register(client, "admin@example.com", role="admin")
    victim = _register(client, "delete-me@example.com", role="viewer")
    tokens = _login(client, "admin@example.com")
    response = client.delete(
        f"/api/v1/users/{victim['id']}",
        headers=_auth_header(tokens["access_token"]),
    )
    assert response.status_code == 200
    assert admin["role"] == "admin"
