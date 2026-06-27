"""Plugin registry for built-in and extensible model algorithms."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.schemas.models import ModelAlgorithmInfo, ModelRegistryResponse


@dataclass(frozen=True)
class RegressionAlgorithmSpec:
    """Metadata for a regression algorithm."""

    id: str
    label: str
    description: str
    builder: Callable[..., Any]


@dataclass(frozen=True)
class ClassificationAlgorithmSpec:
    """Metadata for a classification algorithm."""

    id: str
    label: str
    description: str
    builder: Callable[..., Any]


@dataclass(frozen=True)
class ClusteringAlgorithmSpec:
    """Metadata for a clustering algorithm."""

    id: str
    label: str
    description: str
    builder: Callable[..., Any]


@dataclass(frozen=True)
class TimeseriesAlgorithmSpec:
    """Metadata for a time series algorithm."""

    id: str
    label: str
    description: str


REGRESSION_ALGORITHMS: dict[str, RegressionAlgorithmSpec] = {}
CLASSIFICATION_ALGORITHMS: dict[str, ClassificationAlgorithmSpec] = {}
CLUSTERING_ALGORITHMS: dict[str, ClusteringAlgorithmSpec] = {}
TIMESERIES_ALGORITHMS: dict[str, TimeseriesAlgorithmSpec] = {}


def register_regression_algorithm(spec: RegressionAlgorithmSpec) -> None:
    """Register a regression algorithm for API discovery and dispatch."""
    REGRESSION_ALGORITHMS[spec.id] = spec


def list_regression_algorithms() -> list[ModelAlgorithmInfo]:
    """Return regression algorithms exposed by the API."""
    return [
        ModelAlgorithmInfo(
            id=spec.id,
            label=spec.label,
            model_type="regression",
            description=spec.description,
        )
        for spec in REGRESSION_ALGORITHMS.values()
    ]


def get_regression_algorithm(algorithm_id: str) -> RegressionAlgorithmSpec:
    """Look up a regression algorithm or raise when unknown."""
    spec = REGRESSION_ALGORITHMS.get(algorithm_id)
    if spec is None:
        raise KeyError(f"Unknown regression algorithm: {algorithm_id}")
    return spec


def register_classification_algorithm(spec: ClassificationAlgorithmSpec) -> None:
    """Register a classification algorithm for API discovery and dispatch."""
    CLASSIFICATION_ALGORITHMS[spec.id] = spec


def list_classification_algorithms() -> list[ModelAlgorithmInfo]:
    """Return classification algorithms exposed by the API."""
    return [
        ModelAlgorithmInfo(
            id=spec.id,
            label=spec.label,
            model_type="classification",
            description=spec.description,
        )
        for spec in CLASSIFICATION_ALGORITHMS.values()
    ]


def get_classification_algorithm(algorithm_id: str) -> ClassificationAlgorithmSpec:
    """Look up a classification algorithm or raise when unknown."""
    spec = CLASSIFICATION_ALGORITHMS.get(algorithm_id)
    if spec is None:
        raise KeyError(f"Unknown classification algorithm: {algorithm_id}")
    return spec


def register_clustering_algorithm(spec: ClusteringAlgorithmSpec) -> None:
    """Register a clustering algorithm for API discovery and dispatch."""
    CLUSTERING_ALGORITHMS[spec.id] = spec


def list_clustering_algorithms() -> list[ModelAlgorithmInfo]:
    """Return clustering algorithms exposed by the API."""
    return [
        ModelAlgorithmInfo(
            id=spec.id,
            label=spec.label,
            model_type="clustering",
            description=spec.description,
        )
        for spec in CLUSTERING_ALGORITHMS.values()
    ]


def get_clustering_algorithm(algorithm_id: str) -> ClusteringAlgorithmSpec:
    """Look up a clustering algorithm or raise when unknown."""
    spec = CLUSTERING_ALGORITHMS.get(algorithm_id)
    if spec is None:
        raise KeyError(f"Unknown clustering algorithm: {algorithm_id}")
    return spec


def register_timeseries_algorithm(spec: TimeseriesAlgorithmSpec) -> None:
    """Register a time series algorithm for API discovery."""
    TIMESERIES_ALGORITHMS[spec.id] = spec


def list_timeseries_algorithms() -> list[ModelAlgorithmInfo]:
    """Return time series algorithms exposed by the API."""
    return [
        ModelAlgorithmInfo(
            id=spec.id,
            label=spec.label,
            model_type="timeseries",
            description=spec.description,
        )
        for spec in TIMESERIES_ALGORITHMS.values()
    ]


def get_timeseries_algorithm(algorithm_id: str) -> TimeseriesAlgorithmSpec:
    """Look up a time series algorithm or raise when unknown."""
    spec = TIMESERIES_ALGORITHMS.get(algorithm_id)
    if spec is None:
        raise KeyError(f"Unknown time series algorithm: {algorithm_id}")
    return spec


def model_registry_response() -> ModelRegistryResponse:
    """Build the model registry payload for clients."""
    from app.services.analytics_plugins import list_plugin_specs

    return ModelRegistryResponse(
        regression=list_regression_algorithms(),
        classification=list_classification_algorithms(),
        clustering=list_clustering_algorithms(),
        timeseries=list_timeseries_algorithms(),
        plugins=[
            {
                "name": plugin.name,
                "display_name": plugin.display_name,
                "description": plugin.description,
                "applicable": plugin.applicable,
            }
            for plugin in list_plugin_specs()
        ],
    )
