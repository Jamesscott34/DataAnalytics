"""Background job API schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

JobStatusValue = Literal["queued", "running", "complete", "failed", "cancelled"]
JobType = Literal["demo", "quick_scan", "fail", "eda"]


class JobCreateRequest(BaseModel):
    """Request to enqueue a background job."""

    job_type: JobType = "demo"
    payload: dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    """Background job status response."""

    id: str
    job_type: str
    status: JobStatusValue
    progress: int
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    result_id: str | None = None
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobListResponse(BaseModel):
    """List of recent jobs."""

    items: list[JobResponse]
    total: int
