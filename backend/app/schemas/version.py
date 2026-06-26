"""Dataset version API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class FileVersionEntry(BaseModel):
    """Single file version history entry."""

    id: int
    file_id: int
    uploaded_by: int | None
    version_number: int
    upload_event: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FileVersionListResponse(BaseModel):
    """Version history for an uploaded file."""

    file_id: int
    file_hash: str
    versions: list[FileVersionEntry]


class VersionCompareResponse(BaseModel):
    """Comparison between two version entries for the same file."""

    file_id: int
    file_hash: str
    version_a: FileVersionEntry
    version_b: FileVersionEntry
    content_identical: bool
    differences: list[str] = Field(default_factory=list)
