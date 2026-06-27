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
    ClusteringRequest,
    ClusteringResult,
    ModelRegistryResponse,
    PCARequest,
    PCAResult,
    RegressionRequest,
    RegressionResult,
    SimilarityRequest,
    SimilarityResult,
    TimeseriesRequest,
    TimeseriesResult,
)
from app.services.classification_service import (
    ClassificationError,
    classification_service,
)
from app.services.clustering_service import ClusteringError, clustering_service
from app.services.pca_service import PCAError, pca_service
from app.services.plugin_registry import model_registry_response
from app.services.recommendation_service import (
    RecommendationError,
    recommendation_service,
)
from app.services.regression_service import RegressionError, regression_service
from app.services.timeseries_service import TimeseriesError, timeseries_service

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


@router.post(
    "/{file_id}/clustering",
    response_model=ClusteringResult,
    summary="Run clustering on an uploaded CSV file",
)
def run_clustering(
    file_id: int,
    request: ClusteringRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> ClusteringResult:
    """Cluster rows using k-means or hierarchical clustering."""
    try:
        return clustering_service.run_clustering(db, file_id=file_id, request=request)
    except ClusteringError as exc:
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
    "/{file_id}/pca",
    response_model=PCAResult,
    summary="Run PCA on an uploaded CSV file",
)
def run_pca(
    file_id: int,
    request: PCARequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> PCAResult:
    """Run principal component analysis on numeric feature columns."""
    try:
        return pca_service.run_pca(db, file_id=file_id, request=request)
    except PCAError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{file_id}/timeseries",
    response_model=TimeseriesResult,
    summary="Forecast a time series from an uploaded CSV file",
)
def run_timeseries_forecast(
    file_id: int,
    request: TimeseriesRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> TimeseriesResult:
    """Forecast using moving average, AR, ARIMA, or SARIMAX."""
    try:
        return timeseries_service.run_forecast(db, file_id=file_id, request=request)
    except TimeseriesError as exc:
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
    "/{file_id}/similarity",
    response_model=SimilarityResult,
    summary="Run row or item cosine similarity",
)
def run_similarity(
    file_id: int,
    request: SimilarityRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> SimilarityResult:
    """Compute cosine similarity for rows or selected feature columns."""
    try:
        return recommendation_service.run_similarity(db, file_id=file_id, request=request)
    except RecommendationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/results/{result_id}",
    response_model=(
        RegressionResult
        | ClassificationResult
        | ClusteringResult
        | PCAResult
        | TimeseriesResult
        | SimilarityResult
    ),
    summary="Get a stored model result",
)
def get_model_result(
    result_id: str,
    _: Annotated[User, Depends(require_viewer)],
    db: Annotated[Session, Depends(get_db)],
) -> (
    RegressionResult
    | ClassificationResult
    | ClusteringResult
    | PCAResult
    | TimeseriesResult
    | SimilarityResult
):
    """Return a previously trained model or analysis result."""
    try:
        return regression_service.get_result(result_id, db)
    except RegressionError:
        pass
    try:
        return classification_service.get_result(result_id, db)
    except ClassificationError:
        pass
    try:
        return clustering_service.get_result(result_id, db)
    except ClusteringError:
        pass
    try:
        return pca_service.get_result(result_id, db)
    except PCAError:
        pass
    try:
        return timeseries_service.get_result(result_id, db)
    except TimeseriesError:
        pass
    try:
        return recommendation_service.get_result(result_id, db)
    except RecommendationError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Model result not found",
    )
