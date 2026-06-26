"""Dataset version history service.

Records upload events against a file without creating duplicate on-disk copies
when the SHA-256 hash is unchanged.
"""

from sqlalchemy.orm import Session

from app.models.file_version import FileVersion
from app.models.uploaded_file import UploadedFile
from app.models.user import User, UserRole
from app.schemas.version import (
    FileVersionEntry,
    FileVersionListResponse,
    VersionCompareResponse,
)


class DatasetVersionError(ValueError):
    """Raised when version operations fail."""


class DatasetVersionService:
    """Manage dataset version history."""

    def record_version(
        self,
        db: Session,
        *,
        file_id: int,
        uploaded_by: int | None,
        upload_event: str,
        notes: str | None = None,
        commit: bool = True,
    ) -> int:
        """Append a version entry and return its version number."""
        latest = (
            db.query(FileVersion)
            .filter(FileVersion.file_id == file_id)
            .order_by(FileVersion.version_number.desc())
            .first()
        )
        version_number = (latest.version_number + 1) if latest else 1
        entry = FileVersion(
            file_id=file_id,
            uploaded_by=uploaded_by,
            version_number=version_number,
            upload_event=upload_event,
            notes=notes,
        )
        db.add(entry)
        if commit:
            db.commit()
            db.refresh(entry)
        return version_number

    def list_versions(self, db: Session, *, file_id: int) -> FileVersionListResponse:
        """Return ordered version history for a file."""
        file = db.get(UploadedFile, file_id)
        if file is None:
            raise DatasetVersionError("File not found")

        versions = (
            db.query(FileVersion)
            .filter(FileVersion.file_id == file_id)
            .order_by(FileVersion.version_number.asc())
            .all()
        )
        return FileVersionListResponse(
            file_id=file_id,
            file_hash=file.file_hash,
            versions=[FileVersionEntry.model_validate(item) for item in versions],
        )

    def compare_versions(
        self,
        db: Session,
        *,
        file_id: int,
        version_a: int,
        version_b: int,
    ) -> VersionCompareResponse:
        """Compare two version entries for the same file."""
        file = db.get(UploadedFile, file_id)
        if file is None:
            raise DatasetVersionError("File not found")

        entry_a = self._get_version(db, file_id=file_id, version_number=version_a)
        entry_b = self._get_version(db, file_id=file_id, version_number=version_b)
        schema_a = FileVersionEntry.model_validate(entry_a)
        schema_b = FileVersionEntry.model_validate(entry_b)

        differences: list[str] = []
        if schema_a.upload_event != schema_b.upload_event:
            differences.append(
                f"upload_event: {schema_a.upload_event} vs {schema_b.upload_event}"
            )
        if schema_a.uploaded_by != schema_b.uploaded_by:
            differences.append(
                f"uploaded_by: {schema_a.uploaded_by} vs {schema_b.uploaded_by}"
            )
        if schema_a.notes != schema_b.notes:
            differences.append("notes differ")

        return VersionCompareResponse(
            file_id=file_id,
            file_hash=file.file_hash,
            version_a=schema_a,
            version_b=schema_b,
            content_identical=True,
            differences=differences,
        )

    def latest_version_number(self, db: Session, *, file_id: int) -> int:
        """Return the latest version number for a file."""
        latest = (
            db.query(FileVersion)
            .filter(FileVersion.file_id == file_id)
            .order_by(FileVersion.version_number.desc())
            .first()
        )
        return latest.version_number if latest else 0

    def ensure_access(self, db: Session, *, file_id: int, user: User) -> UploadedFile:
        """Verify the caller may view version history for a file."""
        file = db.get(UploadedFile, file_id)
        if file is None:
            raise DatasetVersionError("File not found")
        if user.role != UserRole.ADMIN and file.owner_id != user.id:
            raise DatasetVersionError("Insufficient permissions")
        return file

    def _get_version(
        self,
        db: Session,
        *,
        file_id: int,
        version_number: int,
    ) -> FileVersion:
        """Load a version entry or raise."""
        entry = (
            db.query(FileVersion)
            .filter(
                FileVersion.file_id == file_id,
                FileVersion.version_number == version_number,
            )
            .first()
        )
        if entry is None:
            raise DatasetVersionError("Version not found")
        return entry


dataset_version_service = DatasetVersionService()
