"""CSV upload service.

Validates uploaded CSV files, computes SHA-256 hashes, stores accepted files,
and persists metadata. Does not perform security scanning, EDA, or ML analysis.
"""

import csv
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import FileSource, UploadedFile
from app.schemas.upload import ScanResult, UploadResponse
from app.services.security_scan_service import security_scan_service
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
    ) -> UploadResponse:
        """Validate, store, and persist metadata for an uploaded CSV.

        Args:
            db: Active database session.
            filename: Client-provided filename.
            content: Uploaded file bytes.
            owner_id: Authenticated user ID.
            mime_type: Browser-supplied MIME type when available.

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
        scan_result = security_scan_service.scan_bytes(
            filename=safe_filename,
            content=content,
        )

        existing = (
            db.query(UploadedFile).filter(UploadedFile.file_hash == file_hash).first()
        )
        if existing is not None:
            security_scan_service.persist_scan(
                db,
                file_id=existing.id,
                result=scan_result,
            )
            logger.info("duplicate_csv_upload", extra={"file_id": existing.id})
            return self._to_response(
                existing,
                is_duplicate=True,
                scan_result=scan_result,
            )

        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_path = self._store_file(upload_dir, file_hash, safe_filename, content)

        record = UploadedFile(
            owner_id=owner_id,
            original_filename=safe_filename,
            stored_path=str(stored_path.relative_to(upload_dir.resolve())),
            file_hash=file_hash,
            mime_type=mime_type,
            size_bytes=len(content),
            row_count=summary.row_count,
            column_count=summary.column_count,
            source=FileSource.UPLOAD,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(
            "csv_uploaded",
            extra={"file_id": record.id, "file_hash": file_hash},
        )
        security_scan_service.persist_scan(db, file_id=record.id, result=scan_result)
        return self._to_response(
            record,
            is_duplicate=False,
            scan_result=scan_result,
        )

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

    def _decode(self, content: bytes) -> str:
        """Decode content and map encoding errors."""
        try:
            return decode_csv_bytes(content)
        except EncodingValidationError as exc:
            raise CSVUploadError(str(exc)) from exc

    def _summarize_csv(self, text: str) -> CSVSummary:
        """Parse CSV text and return row/column counts."""
        reader = csv.reader(StringIO(text))
        rows = list(reader)
        if not rows or not rows[0]:
            raise CSVUploadError("CSV must contain a header row")
        header_width = len(rows[0])
        data_rows = rows[1:]
        if any(len(row) > 0 and len(row) != header_width for row in data_rows):
            raise CSVUploadError("CSV rows must have a consistent number of columns")
        return CSVSummary(row_count=len(data_rows), column_count=header_width)

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
        resolved_target.write_bytes(content)
        return resolved_target

    def _to_response(
        self,
        file: UploadedFile,
        *,
        is_duplicate: bool,
        scan_result: ScanResult,
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
            version_number=1,
            scan_result=scan_result,
        )


csv_service = CSVService()
