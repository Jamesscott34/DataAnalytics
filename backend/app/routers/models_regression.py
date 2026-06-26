"""Regression and classification model API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.models import (
    ClassificationRequest,
    ClassificationResult,
    ModelRegistryResponse,
    RegressionRequest,
    RegressionResult,
)
from app.services.classification_service import (
    ClassificationError,
    classification_service,
)
from app.services.plugin_registry import model_registry_response
from app.services.regression_service import RegressionError, regression_service

router = APIRouter(prefix="/models", tags=["models"])


@router.get(
    "/registry",
    response_model=ModelRegistryResponse,
    summary="List available model algorithms",
)
def list_model_algorithms(
    _: Annotated[User, Depends(require_viewer)],
) -> ModelRegistryResponse:
    """Return built-in regression algorithms registered in the plugin registry."""
    return model_registry_response()


@router.post(
    "/{file_id}/regression",
    response_model=RegressionResult,
    summary="Train a regression model",
)
def train_regression(
    file_id: int,
    request: RegressionRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> RegressionResult:
    """Train a regression model on an uploaded CSV file."""
    try:
        return regression_service.run_regression(db, file_id=file_id, request=request)
    except RegressionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{file_id}/classification",
    response_model=ClassificationResult,
    summary="Train a classification model",
)
def train_classification(
    file_id: int,
    request: ClassificationRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> ClassificationResult:
    """Train a classification model on an uploaded CSV file."""
    try:
        return classification_service.run_classification(
            db,
            file_id=file_id,
            request=request,
        )
    except ClassificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/results/{result_id}",
    response_model=RegressionResult | ClassificationResult,
    summary="Get a stored model result",
)
def get_model_result(
    result_id: str,
    _: Annotated[User, Depends(require_viewer)],
) -> RegressionResult | ClassificationResult:
    """Return a previously trained regression or classification result."""
    try:
        return regression_service.get_result(result_id)
    except RegressionError:
        pass
    try:
        return classification_service.get_result(result_id)
    except ClassificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
