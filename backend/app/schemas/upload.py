"""Upload request and response schemas.

Defines serialisable API shapes for secure CSV uploads and metadata previews.
Does not contain ORM models or file-processing logic.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ScanResult(BaseModel):
    """Python-only security scanner result."""

    status: str
    issues: list[str]
    risk_score: int
    recommended_action: str
    scan_timestamp: datetime
    file_hash: str


class UploadResponse(BaseModel):
    """Response returned after a CSV upload is accepted."""

    file_id: int
    filename: str
    file_hash: str = Field(min_length=64, max_length=64)
    size_bytes: int
    row_count: int
    column_count: int
    is_duplicate: bool
    version_number: int = 1
    scan_result: ScanResult | None = None
    client_hash_match: bool | None = None


class UploadMetadata(BaseModel):
    """Uploaded file metadata returned by list/detail endpoints."""

    id: int
    original_filename: str
    file_hash: str
    size_bytes: int
    row_count: int | None
    column_count: int | None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadListResponse(BaseModel):
    """Paginated uploaded file metadata response."""

    items: list[UploadMetadata]
    total: int


class DuplicateUploadResponse(BaseModel):
    """Returned when an upload matches an existing file hash."""

    error: str = "duplicate_upload"
    message: str
    file_hash: str
    existing_file: UploadMetadata
    scan_result: ScanResult


class AssetFileInfo(BaseModel):
    """Metadata for a file available in temp_assets."""

    name: str
    size_bytes: int
    safe: bool = True
    file_type: str = "csv"


class AssetListResponse(BaseModel):
    """List of selectable temp asset files."""

    files: list[AssetFileInfo]
