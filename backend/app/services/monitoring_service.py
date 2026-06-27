"""Application monitoring metrics and health checks."""

import threading
import time
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.schemas.monitoring import (
    DatabaseStatus,
    MonitoringHealthResponse,
    RequestMetrics,
)


class MonitoringService:
    """In-memory request metrics and dependency health probes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_requests = 0
        self._by_status: dict[str, int] = {}
        self._by_path: dict[str, int] = {}
        self._slow_requests = 0

    def record_request(
        self,
        *,
        path: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        """Increment request counters."""
        with self._lock:
            self._total_requests += 1
            status_key = str(status_code)
            self._by_status[status_key] = self._by_status.get(status_key, 0) + 1
            self._by_path[path] = self._by_path.get(path, 0) + 1
            if duration_ms >= get_settings().slow_request_threshold_ms:
                self._slow_requests += 1

    def metrics(self) -> RequestMetrics:
        """Return aggregated request metrics."""
        with self._lock:
            return RequestMetrics(
                total_requests=self._total_requests,
                by_status=dict(self._by_status),
                by_path=dict(self._by_path),
                slow_requests=self._slow_requests,
            )

    def health(self, db: Session) -> MonitoringHealthResponse:
        """Return detailed health including database connectivity."""
        database = self._database_status(db)
        status = "ok" if database.connected else "degraded"
        return MonitoringHealthResponse(
            status=status,
            database=database,
            checked_at=datetime.now(UTC),
        )

    def _database_status(self, db: Session) -> DatabaseStatus:
        start = time.perf_counter()
        try:
            db.execute(text("SELECT 1"))
            latency_ms = (time.perf_counter() - start) * 1000
            return DatabaseStatus(connected=True, latency_ms=round(latency_ms, 2))
        except Exception:  # noqa: BLE001 - health probe should not raise
            return DatabaseStatus(connected=False, latency_ms=None)


monitoring_service = MonitoringService()
