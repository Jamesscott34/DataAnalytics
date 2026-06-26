"""Asset folder integrity scanning and password-protected manifest management.

Scans ``temp_assets`` and ``assets`` on startup, compares file SHA-256 hashes
against an encrypted manifest, and exposes pending changes for user review.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.schemas.asset_integrity import (
    IntegrityActionResponse,
    IntegrityFileInfo,
    IntegrityStatusResponse,
    ModifiedIntegrityFile,
)
from app.utils.hash_utils import sha256_bytes
from app.utils.logging_utils import get_logger
from app.utils.manifest_crypto import (
    ManifestCryptoError,
    decrypt_manifest,
    encrypt_manifest,
)

logger = get_logger(__name__)

MANIFEST_VERSION = 1


class AssetIntegrityError(ValueError):
    """Raised when integrity operations fail."""


@dataclass(frozen=True)
class ScannedFile:
    """A file discovered during a folder scan."""

    path: str
    sha256: str
    size_bytes: int


class AssetIntegrityService:
    """Scan watched folders and manage the encrypted integrity manifest."""

    def __init__(self) -> None:
        self._manifest: dict[str, Any] | None = None
        self._unlock_password: str | None = None
        self._disk_scan: dict[str, ScannedFile] = {}

    def refresh_disk_scan(self) -> dict[str, ScannedFile]:
        """Scan watched folders and cache current file hashes."""
        scanned: dict[str, ScannedFile] = {}
        for label, folder in self._watched_folder_paths().items():
            folder.mkdir(parents=True, exist_ok=True)
            for path in sorted(folder.rglob("*")):
                if not path.is_file():
                    continue
                if path.name.startswith("."):
                    continue
                relative = f"{label}/{path.relative_to(folder).as_posix()}"
                content = path.read_bytes()
                scanned[relative] = ScannedFile(
                    path=relative,
                    sha256=sha256_bytes(content),
                    size_bytes=len(content),
                )
        self._disk_scan = scanned
        logger.info(
            "asset_integrity_scan_complete",
            extra={"file_count": len(scanned)},
        )
        return scanned

    def get_status(self) -> IntegrityStatusResponse:
        """Return manifest and pending change status."""
        manifest_exists = self._manifest_path().exists()
        setup_required = not manifest_exists
        unlocked = self._manifest is not None

        response = IntegrityStatusResponse(
            manifest_exists=manifest_exists,
            unlocked=unlocked,
            watched_folders=list(self._watched_folder_paths().keys()),
            discovered_file_count=len(self._disk_scan),
            setup_required=setup_required,
        )
        if not unlocked:
            return response

        new_files, modified_files, removed_files, unchanged_count = (
            self._diff_manifest()
        )
        response.new_files = new_files
        response.modified_files = modified_files
        response.removed_files = removed_files
        response.unchanged_count = unchanged_count
        return response

    def initialize_manifest(
        self,
        password: str,
        confirm_password: str,
    ) -> IntegrityActionResponse:
        """Create a password-protected manifest from the current disk scan."""
        if password != confirm_password:
            raise AssetIntegrityError("Passwords do not match")
        if len(password) < 8:
            raise AssetIntegrityError("Manifest password must be at least 8 characters")
        if self._manifest_path().exists():
            raise AssetIntegrityError("Manifest already exists")

        entries = self._build_entries_from_scan()
        manifest = {
            "version": MANIFEST_VERSION,
            "created_at": datetime.now(UTC).isoformat(),
            "entries": entries,
        }
        self._write_manifest_file(password, manifest)
        self._manifest = manifest
        self._unlock_password = password
        logger.info(
            "asset_integrity_manifest_initialized",
            extra={"entries": len(entries)},
        )
        return IntegrityActionResponse(
            message="Integrity manifest created",
            unlocked=True,
            setup_required=False,
        )

    def unlock_manifest(self, password: str) -> IntegrityActionResponse:
        """Unlock the encrypted manifest for this server session."""
        if not self._manifest_path().exists():
            raise AssetIntegrityError("Integrity manifest does not exist yet")
        manifest = self._read_manifest_file(password)
        self._manifest = manifest
        self._unlock_password = password
        logger.info("asset_integrity_manifest_unlocked")
        return IntegrityActionResponse(
            message="Integrity manifest unlocked",
            unlocked=True,
            setup_required=False,
        )

    def apply_changes(
        self,
        *,
        add_or_update: list[str],
        remove: list[str],
    ) -> IntegrityActionResponse:
        """Persist user-approved manifest updates."""
        if self._manifest is None or self._unlock_password is None:
            raise AssetIntegrityError("Unlock the integrity manifest first")

        entries: dict[str, dict[str, Any]] = dict(self._manifest.get("entries", {}))
        for path in add_or_update:
            scanned = self._disk_scan.get(path)
            if scanned is None:
                raise AssetIntegrityError(f"File not found on disk: {path}")
            entries[path] = {
                "sha256": scanned.sha256,
                "size_bytes": scanned.size_bytes,
                "updated_at": datetime.now(UTC).isoformat(),
            }
        for path in remove:
            entries.pop(path, None)

        manifest = {
            "version": MANIFEST_VERSION,
            "created_at": self._manifest.get("created_at"),
            "updated_at": datetime.now(UTC).isoformat(),
            "entries": entries,
        }
        self._write_manifest_file(self._unlock_password, manifest)
        self._manifest = manifest
        logger.info(
            "asset_integrity_manifest_updated",
            extra={"added_or_updated": len(add_or_update), "removed": len(remove)},
        )
        return IntegrityActionResponse(
            message="Integrity manifest updated",
            unlocked=True,
            setup_required=False,
        )

    def lock_manifest(self) -> None:
        """Clear unlocked manifest state from memory."""
        self._manifest = None
        self._unlock_password = None

    def _diff_manifest(
        self,
    ) -> tuple[list[IntegrityFileInfo], list[ModifiedIntegrityFile], list[str], int]:
        """Compare disk scan against the unlocked manifest."""
        if self._manifest is None:
            return [], [], [], 0

        entries: dict[str, dict[str, Any]] = self._manifest.get("entries", {})
        new_files: list[IntegrityFileInfo] = []
        modified_files: list[ModifiedIntegrityFile] = []
        removed_files: list[str] = []
        unchanged_count = 0

        for path, scanned in self._disk_scan.items():
            stored = entries.get(path)
            if stored is None:
                new_files.append(
                    IntegrityFileInfo(
                        path=path,
                        sha256=scanned.sha256,
                        size_bytes=scanned.size_bytes,
                    )
                )
                continue
            if stored.get("sha256") != scanned.sha256:
                modified_files.append(
                    ModifiedIntegrityFile(
                        path=path,
                        stored_sha256=str(stored.get("sha256")),
                        current_sha256=scanned.sha256,
                        size_bytes=scanned.size_bytes,
                    )
                )
            else:
                unchanged_count += 1

        for path in entries:
            if path not in self._disk_scan:
                removed_files.append(path)

        return new_files, modified_files, removed_files, unchanged_count

    def _build_entries_from_scan(self) -> dict[str, dict[str, Any]]:
        """Build manifest entries from the current disk scan."""
        now = datetime.now(UTC).isoformat()
        return {
            path: {
                "sha256": scanned.sha256,
                "size_bytes": scanned.size_bytes,
                "updated_at": now,
            }
            for path, scanned in self._disk_scan.items()
        }

    def _manifest_path(self) -> Path:
        """Return the encrypted manifest file path."""
        settings = get_settings()
        return Path(settings.asset_manifest_path)

    def _watched_folder_paths(self) -> dict[str, Path]:
        """Return watched folder labels and absolute paths."""
        settings = get_settings()
        return {
            "temp_assets": Path(settings.temp_assets_dir),
            "assets": Path(settings.assets_dir),
        }

    def _write_manifest_file(self, password: str, manifest: dict[str, Any]) -> None:
        """Encrypt and persist the manifest."""
        path = self._manifest_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            encrypted = encrypt_manifest(password, manifest)
        except ManifestCryptoError as exc:
            raise AssetIntegrityError(str(exc)) from exc
        path.write_bytes(encrypted)

    def _read_manifest_file(self, password: str) -> dict[str, Any]:
        """Load and decrypt the manifest from disk."""
        path = self._manifest_path()
        try:
            return decrypt_manifest(password, path.read_bytes())
        except ManifestCryptoError as exc:
            raise AssetIntegrityError(str(exc)) from exc


asset_integrity_service = AssetIntegrityService()
