"""Upload request and response schemas.

Defines serialisable API shapes for secure CSV uploads and metadata previews.
Does not contain ORM models or file-processing logic.
"""

from datetime import datetime

from pydantic import BaseModel, Field


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
