"""Health check API router.

Exposes a minimal liveness endpoint for development and orchestration.
Full monitoring (database, disk) is added in the monitoring feature task.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Liveness health check",
    response_description="Application is running",
)
def health_check() -> dict[str, str]:
    """Return a simple ok status for load balancers and smoke tests.

    Returns:
        Dict with status key set to ``ok``.
    """
    return {"status": "ok"}
