"""Export request and response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ExportReportRequest(BaseModel):
    """Export a stored quick-scan report."""

    report_id: str = Field(min_length=1)


class SavedScanResult(BaseModel):
    """Metadata for a file saved under scan_results/."""

    filename: str
    format: Literal["markdown", "pdf"]
    size_bytes: int
    saved_at: datetime
    view_url: str
    download_url: str


class ScanResultListResponse(BaseModel):
    """List of saved scan result exports."""

    items: list[SavedScanResult]
    total: int


class ExportSavedResponse(BaseModel):
    """Response after saving an export to scan_results."""

    saved: SavedScanResult
    download_filename: str
