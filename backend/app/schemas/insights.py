"""Generated insight API schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class InsightRequest(BaseModel):
    """Request to generate an insight for an analysis result."""

    result_id: str
    analysis_type: str
    job_id: str | None = None


InsightSource = Literal["llm", "fallback"]


class InsightResponse(BaseModel):
    """Stored generated insight."""

    id: int
    result_id: str
    job_id: str | None = None
    analysis_type: str
    summary: str
    source: InsightSource
    generated_at: datetime
