"""Audit log API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    """Single persisted audit log entry."""

    id: int
    user_id: int | None
    file_id: int | None
    event_type: str
    action: str
    result: str
    file_hash: str | None
    filename: str | None
    ip_address: str | None
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="event_metadata",
    )
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class AuditLogListResponse(BaseModel):
    """Paginated audit log response."""

    items: list[AuditLogEntry]
    total: int
