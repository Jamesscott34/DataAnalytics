"""Analytics plugin API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.plugins import PluginListResponse, PluginRunRequest, PluginRunResponse
from app.services.analytics_plugins import PluginError, list_plugins, run_plugin

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("", response_model=PluginListResponse, summary="List analytics plugins")
def get_plugins(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_viewer)],
    file_id: int | None = Query(default=None),
) -> PluginListResponse:
    """Return registered plugins, marking applicability for a file when provided."""
    return PluginListResponse(plugins=list_plugins(db, file_id=file_id))


@router.post(
    "/{plugin_name}/run",
    response_model=PluginRunResponse,
    summary="Run an analytics plugin",
)
def execute_plugin(
    plugin_name: str,
    request: PluginRunRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> PluginRunResponse:
    """Execute a plugin against an uploaded dataset."""
    try:
        return run_plugin(
            db,
            plugin_name=plugin_name,
            file_id=request.file_id,
            params=request.params,
        )
    except PluginError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
