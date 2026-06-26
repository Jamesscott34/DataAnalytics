"""Security scan API routes.

Exposes latest and historical Python-only scanner results for uploaded files.
Does not perform CSV parsing or model analysis.
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.config import get_settings
from app.database import get_db
from app.models.security_scan import SecurityScan
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.schemas.upload import ScanResult
from app.services.security_scan_service import security_scan_service

router = APIRouter(prefix="/scans", tags=["scans"])


def _get_file_or_404(db: Session, file_id: int) -> UploadedFile:
    """Load an uploaded file or raise HTTP 404."""
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
    return file


@router.get("/{file_id}", response_model=ScanResult, summary="Get latest scan")
def get_latest_scan(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_viewer)],
) -> ScanResult:
    """Return the latest scan result for an uploaded file."""
    _get_file_or_404(db, file_id)
    scan = security_scan_service.latest_for_file(db, file_id)
    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )
    return security_scan_service.to_schema(scan)


@router.get(
    "/{file_id}/history",
    response_model=list[ScanResult],
    summary="Get scan history",
)
def get_scan_history(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_viewer)],
) -> list[ScanResult]:
    """Return all scan results for an uploaded file."""
    _get_file_or_404(db, file_id)
    scans = (
        db.query(SecurityScan)
        .filter(SecurityScan.file_id == file_id)
        .order_by(SecurityScan.scanned_at.desc())
        .all()
    )
    return [security_scan_service.to_schema(scan) for scan in scans]


@router.post("/{file_id}", response_model=ScanResult, summary="Rescan uploaded file")
def rescan_file(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> ScanResult:
    """Rescan a stored uploaded file and persist the result."""
    file = _get_file_or_404(db, file_id)
    upload_dir = security_scan_service_upload_dir()
    path = upload_dir / file.stored_path
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored file not found",
        )
    result = security_scan_service.scan_bytes(
        filename=file.original_filename,
        content=path.read_bytes(),
    )
    security_scan_service.persist_scan(
        db,
        file_id=file.id,
        result=result,
        user_id=current_user.id,
        filename=file.original_filename,
    )
    return result


def security_scan_service_upload_dir() -> Path:
    """Return configured upload directory for rescan file lookup."""
    return Path(get_settings().upload_dir)
