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


REGRESSION_ALGORITHMS: dict[str, RegressionAlgorithmSpec] = {}
CLASSIFICATION_ALGORITHMS: dict[str, ClassificationAlgorithmSpec] = {}


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


def model_registry_response() -> ModelRegistryResponse:
    """Build the model registry payload for clients."""
    return ModelRegistryResponse(
        regression=list_regression_algorithms(),
        classification=list_classification_algorithms(),
        plugins=[],
    )
