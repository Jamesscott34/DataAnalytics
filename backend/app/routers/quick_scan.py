"""Quick scan API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.quick_scan import QuickScanReport
from app.services.quick_scan_service import QuickScanError, quick_scan_service

router = APIRouter(prefix="/files", tags=["quick-scan"])


@router.post(
    "/{file_id}/quick-scan",
    response_model=QuickScanReport,
    summary="Run full analysis quick scan",
)
def run_quick_scan(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> QuickScanReport:
    """Run EDA, SQL import, regression, and classification where possible."""
    try:
        return quick_scan_service.run_quick_scan(db, file_id=file_id)
    except QuickScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{file_id}/quick-scan",
    response_model=QuickScanReport,
    summary="Get latest quick scan report",
    responses={204: {"description": "No quick scan report exists for this file yet"}},
)
def get_latest_quick_scan(
    file_id: int,
    _: Annotated[User, Depends(require_viewer)],
) -> QuickScanReport | Response:
    """Return the most recent quick-scan report for a file."""
    try:
        return quick_scan_service.get_latest_for_file(file_id)
    except QuickScanError as exc:
        if "no quick scan report" in str(exc).lower():
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/quick-scan/{report_id}",
    response_model=QuickScanReport,
    summary="Get quick scan report by ID",
)
def get_quick_scan_report(
    report_id: str,
    _: Annotated[User, Depends(require_viewer)],
) -> QuickScanReport:
    """Return a stored quick-scan report."""
    try:
        return quick_scan_service.get_report(report_id)
    except QuickScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
