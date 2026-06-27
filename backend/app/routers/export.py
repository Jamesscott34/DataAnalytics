"""Export API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.auth.dependencies import require_viewer
from app.models.user import User
from app.schemas.export import (
    ExportReportRequest,
    ExportSavedResponse,
    ScanResultListResponse,
)
from app.services.quick_scan_service import QuickScanError, quick_scan_service
from app.services.report_service import report_service
from app.services.scan_result_storage import ScanResultStorageError, scan_result_storage

router = APIRouter(prefix="/export", tags=["export"])


@router.get(
    "/scan-results",
    response_model=ScanResultListResponse,
    summary="List saved scan result files",
)
def list_scan_results(
    _: Annotated[User, Depends(require_viewer)],
) -> ScanResultListResponse:
    """List Markdown and PDF reports saved in scan_results/."""
    items = scan_result_storage.list_results()
    return ScanResultListResponse(items=items, total=len(items))


@router.get(
    "/scan-results/{filename}/download",
    summary="Download a saved scan result file",
)
def download_scan_result(
    filename: str,
    _: Annotated[User, Depends(require_viewer)],
) -> Response:
    """Serve a saved report as a file download."""
    try:
        if filename.lower().endswith(".pdf"):
            pdf_content = scan_result_storage.read_bytes(filename)
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        if filename.lower().endswith(".md"):
            md_content = scan_result_storage.read_text(filename)
            return Response(
                content=md_content,
                media_type="text/markdown; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        if filename.lower().endswith(".json"):
            json_content = scan_result_storage.read_text(filename)
            return Response(
                content=json_content,
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        if filename.lower().endswith(".csv"):
            csv_content = scan_result_storage.read_text(filename)
            return Response(
                content=csv_content,
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
    except ScanResultStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported file type",
    )


@router.get(
    "/scan-results/{filename}",
    summary="View a saved scan result in the browser",
)
def view_scan_result(
    filename: str,
    _: Annotated[User, Depends(require_viewer)],
) -> Response:
    """Serve a saved report for inline browser viewing."""
    try:
        if filename.lower().endswith(".pdf"):
            pdf_content = scan_result_storage.read_bytes(filename)
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={"Content-Disposition": f'inline; filename="{filename}"'},
            )
        if filename.lower().endswith(".md"):
            md_content = scan_result_storage.read_text(filename)
            return Response(
                content=md_content,
                media_type="text/markdown; charset=utf-8",
                headers={"Content-Disposition": f'inline; filename="{filename}"'},
            )
        if filename.lower().endswith(".json"):
            json_content = scan_result_storage.read_text(filename)
            return Response(
                content=json_content,
                media_type="application/json",
                headers={"Content-Disposition": f'inline; filename="{filename}"'},
            )
        if filename.lower().endswith(".csv"):
            csv_content = scan_result_storage.read_text(filename)
            return Response(
                content=csv_content,
                media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f'inline; filename="{filename}"'},
            )
    except ScanResultStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported file type",
    )


@router.post(
    "/markdown",
    response_model=ExportSavedResponse,
    summary="Export quick-scan report as Markdown",
)
def export_markdown(
    request: ExportReportRequest,
    _: Annotated[User, Depends(require_viewer)],
) -> ExportSavedResponse:
    """Generate, save, and return a Markdown analytics report."""
    try:
        report = quick_scan_service.get_report(request.report_id)
    except QuickScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    markdown = report_service.to_markdown(report)
    saved = scan_result_storage.save_text(
        content=markdown,
        original_filename=report.filename,
        extension="md",
    )
    return ExportSavedResponse(saved=saved, download_filename=saved.filename)


@router.post(
    "/json",
    response_model=ExportSavedResponse,
    summary="Export quick-scan report as JSON",
)
def export_json(
    request: ExportReportRequest,
    _: Annotated[User, Depends(require_viewer)],
) -> ExportSavedResponse:
    """Generate, save, and return a JSON analytics report."""
    try:
        report = quick_scan_service.get_report(request.report_id)
    except QuickScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    json_report = report_service.to_json(report)
    saved = scan_result_storage.save_text(
        content=json_report,
        original_filename=report.filename,
        extension="json",
    )
    return ExportSavedResponse(saved=saved, download_filename=saved.filename)


@router.post(
    "/csv",
    response_model=ExportSavedResponse,
    summary="Export quick-scan report as CSV",
)
def export_csv(
    request: ExportReportRequest,
    _: Annotated[User, Depends(require_viewer)],
) -> ExportSavedResponse:
    """Generate, save, and return a CSV analytics report."""
    try:
        report = quick_scan_service.get_report(request.report_id)
    except QuickScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    csv_report = report_service.to_csv(report)
    saved = scan_result_storage.save_text(
        content=csv_report,
        original_filename=report.filename,
        extension="csv",
    )
    return ExportSavedResponse(saved=saved, download_filename=saved.filename)


@router.post(
    "/pdf",
    response_model=ExportSavedResponse,
    summary="Export quick-scan report as PDF",
)
def export_pdf(
    request: ExportReportRequest,
    _: Annotated[User, Depends(require_viewer)],
) -> ExportSavedResponse:
    """Generate, save, and return a PDF analytics report."""
    try:
        report = quick_scan_service.get_report(request.report_id)
    except QuickScanError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    pdf_bytes = report_service.to_pdf(report)
    saved = scan_result_storage.save_bytes(
        content=pdf_bytes,
        original_filename=report.filename,
        extension="pdf",
    )
    return ExportSavedResponse(saved=saved, download_filename=saved.filename)
