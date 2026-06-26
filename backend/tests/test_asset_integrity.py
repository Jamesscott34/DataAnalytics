"""Asset integrity manifest tests."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.services.asset_integrity_service import AssetIntegrityService
from app.utils.hash_utils import sha256_bytes
from app.utils.manifest_crypto import decrypt_manifest, encrypt_manifest


def _analyst_token(client: TestClient) -> str:
    """Register an analyst and return an access token."""
    email = "integrity-analyst@example.com"
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


@pytest.fixture
def integrity_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point integrity folders and manifest to a temp directory."""
    temp_assets = tmp_path / "temp_assets"
    assets = tmp_path / "assets"
    temp_assets.mkdir()
    assets.mkdir()
    manifest = tmp_path / "manifest.enc"

    settings = get_settings()
    monkeypatch.setattr(settings, "temp_assets_dir", str(temp_assets))
    monkeypatch.setattr(settings, "assets_dir", str(assets))
    monkeypatch.setattr(settings, "asset_manifest_path", str(manifest))

    service = AssetIntegrityService()
    monkeypatch.setattr(
        "app.services.asset_integrity_service.asset_integrity_service",
        service,
    )
    monkeypatch.setattr(
        "app.routers.asset_integrity.asset_integrity_service",
        service,
    )
    return service, temp_assets, assets, manifest


def test_encrypt_decrypt_manifest_round_trip() -> None:
    """Manifest encryption round-trips with the same password."""
    payload = {"version": 1, "entries": {"temp_assets/a.csv": {"sha256": "abc"}}}
    blob = encrypt_manifest("StrongPass123", payload)
    assert decrypt_manifest("StrongPass123", blob) == payload


def test_initialize_and_unlock_manifest(integrity_paths) -> None:
    """Initialize stores all scanned files and unlock reads them back."""
    service, temp_assets, _assets, manifest = integrity_paths
    (temp_assets / "sample.csv").write_text("a,b\n1,2\n", encoding="utf-8")

    service.refresh_disk_scan()
    service.initialize_manifest("StrongPass123", "StrongPass123")
    assert manifest.exists()

    service.lock_manifest()
    service.unlock_manifest("StrongPass123")
    status = service.get_status()
    assert status.unlocked is True
    assert status.unchanged_count == 1


def test_detect_modified_and_new_files(integrity_paths) -> None:
    """Changed and new files are reported after unlock."""
    service, temp_assets, assets, _manifest = integrity_paths
    sample = temp_assets / "sample.csv"
    sample.write_text("a,b\n1,2\n", encoding="utf-8")
    service.refresh_disk_scan()
    service.initialize_manifest("StrongPass123", "StrongPass123")

    sample.write_text("a,b\n1,3\n", encoding="utf-8")
    (assets / "new.csv").write_text("x,y\n9,9\n", encoding="utf-8")
    service.refresh_disk_scan()

    status = service.get_status()
    assert len(status.modified_files) == 1
    assert status.modified_files[0].path == "temp_assets/sample.csv"
    assert len(status.new_files) == 1
    assert status.new_files[0].path == "assets/new.csv"


def test_apply_changes_updates_manifest(integrity_paths) -> None:
    """Approved changes are written back to the encrypted manifest."""
    service, temp_assets, assets, _manifest = integrity_paths
    sample = temp_assets / "sample.csv"
    sample.write_text("a,b\n1,2\n", encoding="utf-8")
    service.refresh_disk_scan()
    service.initialize_manifest("StrongPass123", "StrongPass123")

    sample.write_text("a,b\n1,9\n", encoding="utf-8")
    (assets / "new.csv").write_text("x,y\n9,9\n", encoding="utf-8")
    service.refresh_disk_scan()
    service.apply_changes(
        add_or_update=["temp_assets/sample.csv", "assets/new.csv"],
        remove=[],
    )

    service.lock_manifest()
    service.unlock_manifest("StrongPass123")
    status = service.get_status()
    assert status.new_files == []
    assert status.modified_files == []
    assert status.unchanged_count == 2


def test_integrity_status_endpoint_requires_unlock(
    integrity_paths,
    db_session,
) -> None:
    """Status endpoint reports setup and pending changes through the API."""
    from app.database import get_db
    from app.main import app

    service, temp_assets, _assets, _manifest = integrity_paths
    (temp_assets / "sample.csv").write_bytes(b"a,b\n1,2\n")
    service.refresh_disk_scan()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            token = _analyst_token(client)
            first = client.get(
                "/api/v1/asset-integrity/status",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert first.status_code == 200
            assert first.json()["setup_required"] is True

            init = client.post(
                "/api/v1/asset-integrity/initialize",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "password": "StrongPass123",
                    "confirm_password": "StrongPass123",
                },
            )
            assert init.status_code == 200

            (temp_assets / "sample.csv").write_bytes(b"a,b\n9,9\n")
            service.refresh_disk_scan()
            status = client.get(
                "/api/v1/asset-integrity/status",
                headers={"Authorization": f"Bearer {token}"},
            ).json()
            assert len(status["modified_files"]) == 1
            assert status["modified_files"][0]["current_sha256"] == sha256_bytes(
                b"a,b\n9,9\n"
            )
    finally:
        app.dependency_overrides.clear()
