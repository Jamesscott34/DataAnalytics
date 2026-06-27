"""Monitoring metrics and health schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class DatabaseStatus(BaseModel):
    """Database connectivity status."""

    connected: bool
    latency_ms: float | None = None


class MonitoringHealthResponse(BaseModel):
    """Detailed health check with dependency status."""

    status: str
    database: DatabaseStatus
    checked_at: datetime


class RequestMetrics(BaseModel):
    """Aggregated HTTP request counters."""

    total_requests: int
    by_status: dict[str, int] = Field(default_factory=dict)
    by_path: dict[str, int] = Field(default_factory=dict)
    slow_requests: int = 0
