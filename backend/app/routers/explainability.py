"""Explainability API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import require_analyst, require_viewer
from app.models.user import User
from app.schemas.explainability import ExplainabilityResponse, ShapResponse
from app.services.explainability_service import (
    ExplainabilityError,
    explainability_service,
)

router = APIRouter(prefix="/explainability", tags=["explainability"])


@router.get(
    "/{result_id}",
    response_model=ExplainabilityResponse,
    summary="Get explainability data for a model result",
)
def explain_result(
    result_id: str,
    _: Annotated[User, Depends(require_viewer)],
) -> ExplainabilityResponse:
    """Return feature importance, confidence, and summary text."""
    try:
        return explainability_service.explain_result(result_id)
    except ExplainabilityError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{result_id}/shap",
    response_model=ShapResponse,
    summary="Calculate or describe SHAP values for a model result",
)
def shap_values(
    result_id: str,
    _: Annotated[User, Depends(require_analyst)],
) -> ShapResponse:
    """Return SHAP values when available, or a documented fallback."""
    try:
        return explainability_service.shap_values(result_id)
    except ExplainabilityError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
