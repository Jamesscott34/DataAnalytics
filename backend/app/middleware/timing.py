"""Request timing middleware and slow-request logging."""

import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings
from app.services.monitoring_service import monitoring_service
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Log requests that exceed the configured duration threshold."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Time the request and log if it exceeds the slow threshold.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            Response from the downstream handler.
        """
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        threshold = get_settings().slow_request_threshold_ms

        if duration_ms >= threshold:
            logger.warning(
                "slow_request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "status_code": response.status_code,
                },
            )

        monitoring_service.record_request(
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        response.headers["X-Process-Time-Ms"] = str(round(duration_ms, 2))
        return response
