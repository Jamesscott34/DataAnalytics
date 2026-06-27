"""CSV upload service.

Validates uploaded CSV files, computes SHA-256 hashes, stores accepted files,
and persists metadata. Does not perform security scanning, EDA, or ML analysis.
"""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import FileSource, UploadedFile
from app.models.user import User, UserRole
from app.schemas.upload import ScanResult, UploadMetadata, UploadResponse
from app.services.audit_service import audit_service
from app.services.dataset_version_service import dataset_version_service
from app.services.security_scan_service import security_scan_service
from app.utils.csv_parse_utils import CSVParseError, parse_csv_rows
from app.utils.encoding_utils import EncodingValidationError, decode_csv_bytes
from app.utils.file_utils import (
    FileValidationError,
    ensure_within_directory,
    sanitize_filename,
)
from app.utils.hash_utils import sha256_bytes
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class CSVUploadError(ValueError):
    """Raised when a CSV upload fails validation or parsing."""


class DuplicateUploadError(Exception):
    """Raised when an upload matches an existing file and needs user action."""

    def __init__(
        self,
        *,
        existing_file: UploadMetadata,
        scan_result: ScanResult,
        file_hash: str,
    ) -> None:
        self.existing_file = existing_file
        self.scan_result = scan_result
        self.file_hash = file_hash
        super().__init__("Duplicate file detected")


@dataclass(frozen=True)
class CSVSummary:
    """Basic parsed CSV dimensions."""

    row_count: int
    column_count: int


class CSVService:
    """Service for validating and storing uploaded CSV files."""

    def upload_csv(
        self,
        db: Session,
        *,
        filename: str,
        content: bytes,
        owner_id: int,
        mime_type: str | None,
        client_sha256: str | None = None,
        duplicate_action: str | None = None,
        source: FileSource = FileSource.UPLOAD,
        ip_address: str | None = None,
    ) -> UploadResponse:
        """Validate, store, and persist metadata for an uploaded CSV.

        Args:
            db: Active database session.
            filename: Client-provided filename.
            content: Uploaded file bytes.
            owner_id: Authenticated user ID.
            mime_type: Browser-supplied MIME type when available.
            client_sha256: Optional browser-computed SHA-256 for confirmation.
            duplicate_action: ``use_existing`` or ``replace`` when hash matches.
            source: Origin of the dataset file record.

        Returns:
            UploadResponse describing the stored or duplicate file.

        Raises:
            CSVUploadError: If validation, parsing, or storage fails.
        """
        settings = get_settings()
        self._validate_size(content, settings.max_upload_size_bytes)
        safe_filename = self._sanitize(filename)
        text = self._decode(content)
        summary = self._summarize_csv(text)
        file_hash = sha256_bytes(content)
        client_hash_match = self._validate_client_hash(client_sha256, file_hash)
        scan_result = security_scan_service.scan_bytes(
            filename=safe_filename,
            content=content,
        )
        if scan_result.status == "blocked":
            audit_service.record(
                db,
                event_type="upload",
                action="store",
                result="blocked",
                user_id=owner_id,
                file_hash=file_hash,
                filename=safe_filename,
                ip_address=ip_address,
                metadata={"scan_status": scan_result.status},
            )
            raise CSVUploadError(
                "Upload blocked by security scan. " f"{scan_result.recommended_action}"
            )

        existing = (
            db.query(UploadedFile).filter(UploadedFile.file_hash == file_hash).first()
        )
        if existing is not None:
            existing_metadata = self._metadata_from_file(existing)
            security_scan_service.persist_scan(
                db,
                file_id=existing.id,
                result=scan_result,
                user_id=owner_id,
                filename=safe_filename,
                ip_address=ip_address,
            )
            if duplicate_action is None:
                audit_service.record(
                    db,
                    event_type="upload",
                    action="duplicate_detected",
                    result="pending",
                    user_id=owner_id,
                    file_id=existing.id,
                    file_hash=file_hash,
                    filename=safe_filename,
                    ip_address=ip_address,
                )
                raise DuplicateUploadError(
                    existing_file=existing_metadata,
                    scan_result=scan_result,
                    file_hash=file_hash,
                )
            if duplicate_action == "use_existing":
                logger.info("duplicate_csv_upload", extra={"file_id": existing.id})
                audit_service.record(
                    db,
                    event_type="upload",
                    action="use_existing",
                    result="success",
                    user_id=owner_id,
                    file_id=existing.id,
                    file_hash=file_hash,
                    filename=safe_filename,
                    ip_address=ip_address,
                    metadata={"is_duplicate": True},
                )
                version_number = dataset_version_service.record_version(
                    db,
                    file_id=existing.id,
                    uploaded_by=owner_id,
                    upload_event="re_upload",
                    notes=f"Duplicate acknowledged for {safe_filename}",
                )
                return self._to_response(
                    existing,
                    is_duplicate=True,
                    scan_result=scan_result,
                    client_hash_match=client_hash_match,
                    version_number=version_number,
                )
            if duplicate_action == "replace":
                self._delete_record(db, existing)
            else:
                raise CSVUploadError("Invalid duplicate_action value")

        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_path = self._store_file(upload_dir, file_hash, safe_filename, content)

        upload_event = (
            "replace"
            if duplicate_action == "replace"
            else "asset_select" if source == FileSource.TEMP_ASSET else "initial_upload"
        )

        record = UploadedFile(
            owner_id=owner_id,
            original_filename=safe_filename,
            stored_path=str(stored_path.relative_to(upload_dir.resolve())),
            file_hash=file_hash,
            mime_type=mime_type,
            size_bytes=len(content),
            row_count=summary.row_count,
            column_count=summary.column_count,
            source=source,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(
            "csv_uploaded",
            extra={"file_id": record.id, "file_hash": file_hash},
        )
        security_scan_service.persist_scan(
            db,
            file_id=record.id,
            result=scan_result,
            user_id=owner_id,
            filename=safe_filename,
            ip_address=ip_address,
        )
        audit_service.record(
            db,
            event_type="upload",
            action="replace" if duplicate_action == "replace" else "store",
            result="success",
            user_id=owner_id,
            file_id=record.id,
            file_hash=file_hash,
            filename=safe_filename,
            ip_address=ip_address,
            metadata={"source": source.value, "is_duplicate": False},
        )
        version_number = dataset_version_service.record_version(
            db,
            file_id=record.id,
            uploaded_by=owner_id,
            upload_event=upload_event,
            notes=safe_filename,
        )
        return self._to_response(
            record,
            is_duplicate=False,
            scan_result=scan_result,
            client_hash_match=client_hash_match,
            version_number=version_number,
        )

    def delete_upload(
        self,
        db: Session,
        *,
        file_id: int,
        user: User,
        ip_address: str | None = None,
    ) -> None:
        """Delete an uploaded file record and its stored bytes (admin only)."""
        if user.role != UserRole.ADMIN:
            raise CSVUploadError("Only administrators may delete uploaded files")
        record = db.get(UploadedFile, file_id)
        if record is None:
            raise CSVUploadError("Uploaded file not found")
        audit_service.record(
            db,
            event_type="upload",
            action="delete",
            result="success",
            user_id=user.id,
            file_id=record.id,
            file_hash=record.file_hash,
            filename=record.original_filename,
            ip_address=ip_address,
        )
        self._delete_record(db, record)

    def list_uploads(
        self,
        db: Session,
        *,
        user: User,
        limit: int = 20,
    ) -> list[UploadMetadata]:
        """Return recent uploads visible to the current user."""
        query = db.query(UploadedFile).filter(UploadedFile.is_active.is_(True))
        if user.role != UserRole.ADMIN:
            query = query.filter(UploadedFile.owner_id == user.id)
        records = query.order_by(UploadedFile.created_at.desc()).limit(limit).all()
        return [self._metadata_from_file(record) for record in records]

    def _metadata_from_file(self, file: UploadedFile) -> UploadMetadata:
        """Build upload metadata without relying on a live ORM session."""
        return UploadMetadata(
            id=file.id,
            original_filename=file.original_filename,
            file_hash=file.file_hash,
            size_bytes=file.size_bytes,
            row_count=file.row_count,
            column_count=file.column_count,
            source=file.source.value,
            created_at=file.created_at,
        )

    def _delete_record(self, db: Session, record: UploadedFile) -> None:
        """Remove a file record and its stored bytes."""
        settings = get_settings()
        upload_dir = Path(settings.upload_dir)
        stored_path = upload_dir / record.stored_path
        if stored_path.exists():
            stored_path.unlink()
        db.delete(record)
        db.commit()

    def _validate_size(self, content: bytes, max_size_bytes: int) -> None:
        """Validate upload size constraints."""
        if not content:
            raise CSVUploadError("Uploaded file is empty")
        if len(content) > max_size_bytes:
            raise CSVUploadError("Uploaded file exceeds the configured size limit")

    def _sanitize(self, filename: str) -> str:
        """Sanitise filename and map utility validation errors."""
        try:
            return sanitize_filename(filename)
        except FileValidationError as exc:
            raise CSVUploadError(str(exc)) from exc

    def _validate_client_hash(
        self,
        client_sha256: str | None,
        file_hash: str,
    ) -> bool | None:
        """Compare browser-provided and backend-computed SHA-256 hashes."""
        if client_sha256 is None:
            return None
        normalized = client_sha256.strip().lower()
        if len(normalized) != 64:
            raise CSVUploadError("Client SHA-256 hash must be 64 hex characters")
        if normalized != file_hash:
            raise CSVUploadError("Client SHA-256 hash does not match uploaded file")
        return True

    def _decode(self, content: bytes) -> str:
        """Decode content and map encoding errors."""
        try:
            return decode_csv_bytes(content)
        except EncodingValidationError as exc:
            raise CSVUploadError(str(exc)) from exc

    def _summarize_csv(self, text: str) -> CSVSummary:
        """Parse CSV text and return row/column counts."""
        try:
            headers, data_rows, _ = parse_csv_rows(text)
        except CSVParseError as exc:
            raise CSVUploadError(str(exc)) from exc
        return CSVSummary(row_count=len(data_rows), column_count=len(headers))

    def _store_file(
        self,
        upload_dir: Path,
        file_hash: str,
        safe_filename: str,
        content: bytes,
    ) -> Path:
        """Store bytes under a hash-based filename inside upload_dir."""
        suffix = Path(safe_filename).suffix.lower()
        target = upload_dir / f"{file_hash}{suffix}"
        resolved_target = ensure_within_directory(upload_dir, target)
        if not resolved_target.exists():
            resolved_target.write_bytes(content)
        return resolved_target

    def _to_response(
        self,
        file: UploadedFile,
        *,
        is_duplicate: bool,
        scan_result: ScanResult,
        client_hash_match: bool | None,
        version_number: int = 1,
    ) -> UploadResponse:
        """Convert an UploadedFile ORM object into an UploadResponse."""
        return UploadResponse(
            file_id=file.id,
            filename=file.original_filename,
            file_hash=file.file_hash,
            size_bytes=file.size_bytes,
            row_count=file.row_count or 0,
            column_count=file.column_count or 0,
            is_duplicate=is_duplicate,
            version_number=version_number,
            scan_result=scan_result,
            client_hash_match=client_hash_match,
        )


csv_service = CSVService()
