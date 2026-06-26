"""Regression model training service.

Loads uploaded CSV files, prepares numeric features, trains sklearn regressors,
and returns evaluation metrics plus prediction payloads.
"""

import csv
import math
import uuid
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures
from sklearn.tree import DecisionTreeRegressor
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import UploadedFile
from app.schemas.models import (
    ActualVsPredicted,
    FeatureImportanceItem,
    RegressionExplainability,
    RegressionMetrics,
    RegressionRequest,
    RegressionResult,
)
from app.services.plugin_registry import (
    RegressionAlgorithmSpec,
    get_regression_algorithm,
    register_regression_algorithm,
)
from app.utils.encoding_utils import decode_csv_bytes
from app.utils.type_utils import coerce_float, is_missing, normalize_cell


class RegressionError(ValueError):
    """Raised when regression cannot be trained on a dataset."""


class RegressionService:
    """Service for training regression models on uploaded CSV files."""

    def __init__(self) -> None:
        self._results: dict[str, RegressionResult] = {}
        self._register_builtin_algorithms()

    def clear_results(self) -> None:
        """Clear stored regression results (used in tests)."""
        self._results.clear()

    def run_regression(
        self,
        db: Session,
        *,
        file_id: int,
        request: RegressionRequest,
    ) -> RegressionResult:
        """Train a regression model and return metrics and predictions."""
        file = self._get_file(db, file_id)
        matrix = self._load_matrix(file, request)
        algorithm = get_regression_algorithm(request.algorithm)
        model = algorithm.builder()

        x_train, x_test, y_train, y_test = train_test_split(
            matrix.features,
            matrix.target,
            test_size=request.test_size,
            random_state=request.random_state,
        )
        if len(x_train) < 2 or len(x_test) < 1:
            raise RegressionError("Not enough rows for train/test split")

        model.fit(x_train, y_train)
        predictions = model.predict(x_test)

        metrics = RegressionMetrics(
            mae=round(float(mean_absolute_error(y_test, predictions)), 4),
            rmse=round(
                float(math.sqrt(mean_squared_error(y_test, predictions))),
                4,
            ),
            r2=round(float(r2_score(y_test, predictions)), 4),
        )

        actual_vs_predicted = [
            ActualVsPredicted(
                actual=round(float(actual), 4),
                predicted=round(float(predicted), 4),
            )
            for actual, predicted in zip(y_test, predictions, strict=True)
        ]
        residuals = [
            round(float(actual - predicted), 4)
            for actual, predicted in zip(y_test, predictions, strict=True)
        ]

        importance = self._feature_importance(
            model=model,
            feature_names=matrix.feature_names,
            algorithm=request.algorithm,
        )
        explainability = RegressionExplainability(
            supported=request.algorithm in {"decision_tree", "random_forest", "linear"},
            method="feature_importance",
            notes=(
                "SHAP values are available in the explainability task."
                if request.algorithm in {"decision_tree", "random_forest", "linear"}
                else "Feature importance is approximate for this algorithm."
            ),
        )

        result = RegressionResult(
            result_id=str(uuid.uuid4()),
            file_id=file_id,
            algorithm=request.algorithm,
            target_column=request.target_column,
            feature_columns=request.feature_columns,
            train_rows=len(x_train),
            test_rows=len(x_test),
            metrics=metrics,
            actual_vs_predicted=actual_vs_predicted,
            residuals=residuals,
            feature_importance=importance,
            explainability=explainability,
        )
        self._results[result.result_id] = result
        return result

    def get_result(self, result_id: str) -> RegressionResult:
        """Return a stored regression result."""
        result = self._results.get(result_id)
        if result is None:
            raise RegressionError("Regression result not found")
        return result

    def _register_builtin_algorithms(self) -> None:
        register_regression_algorithm(
            RegressionAlgorithmSpec(
                id="linear",
                label="Linear regression",
                description="Ordinary least squares linear model.",
                builder=lambda: LinearRegression(),
            ),
        )
        register_regression_algorithm(
            RegressionAlgorithmSpec(
                id="polynomial",
                label="Polynomial regression",
                description="Polynomial feature expansion with linear regression.",
                builder=lambda: Pipeline(
                    [
                        ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                        ("model", LinearRegression()),
                    ],
                ),
            ),
        )
        register_regression_algorithm(
            RegressionAlgorithmSpec(
                id="decision_tree",
                label="Decision tree",
                description="Single decision tree regressor.",
                builder=lambda: DecisionTreeRegressor(random_state=42),
            ),
        )
        register_regression_algorithm(
            RegressionAlgorithmSpec(
                id="random_forest",
                label="Random forest",
                description="Ensemble of decision trees for regression.",
                builder=lambda: RandomForestRegressor(
                    n_estimators=100,
                    random_state=42,
                ),
            ),
        )

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise RegressionError("File not found")
        return file

    def _read_file_bytes(self, file: UploadedFile) -> bytes:
        upload_dir = Path(get_settings().upload_dir)
        path = upload_dir / file.stored_path
        if not path.exists():
            raise RegressionError("Stored file not found")
        return path.read_bytes()

    def _load_matrix(self, file: UploadedFile, request: RegressionRequest) -> Any:
        content = self._read_file_bytes(file)
        text = decode_csv_bytes(content)
        reader = csv.reader(StringIO(text, newline=""))
        rows = list(reader)
        if not rows or not rows[0]:
            raise RegressionError("CSV must contain a header row")

        headers = [header.strip() for header in rows[0]]
        if request.target_column not in headers:
            raise RegressionError(f"Target column not found: {request.target_column}")
        for column in request.feature_columns:
            if column not in headers:
                raise RegressionError(f"Feature column not found: {column}")
        if request.target_column in request.feature_columns:
            raise RegressionError("Target column cannot also be a feature column")

        column_indexes = {name: index for index, name in enumerate(headers)}
        target_index = column_indexes[request.target_column]
        feature_indexes = [column_indexes[name] for name in request.feature_columns]

        raw_rows: list[list[str]] = []
        for row in rows[1:]:
            if len(row) < len(headers):
                row = row + [""] * (len(headers) - len(row))
            raw_rows.append(row)

        usable_rows: list[list[str]] = []
        target_values: list[float] = []
        for row in raw_rows:
            target_text = normalize_cell(row[target_index])
            if is_missing(target_text):
                continue
            target_value = coerce_float(target_text)
            if target_value is None:
                raise RegressionError(
                    f"Target column must be numeric: {request.target_column}",
                )
            feature_cells = [normalize_cell(row[index]) for index in feature_indexes]
            if any(is_missing(cell) for cell in feature_cells):
                continue
            usable_rows.append(feature_cells)
            target_values.append(target_value)

        if len(usable_rows) < 4:
            raise RegressionError("Need at least four complete rows for regression")

        numeric_features: list[list[float]] = []
        categorical_features: list[list[str]] = []
        numeric_names: list[str] = []
        categorical_names: list[str] = []

        for column_name, column_values in zip(
            request.feature_columns,
            zip(*usable_rows, strict=True),
            strict=True,
        ):
            numeric_attempt = [coerce_float(value) for value in column_values]
            if all(value is not None for value in numeric_attempt):
                numeric_features.append(
                    [float(value) for value in numeric_attempt if value is not None],
                )
                numeric_names.append(column_name)
            else:
                categorical_features.append(list(column_values))
                categorical_names.append(column_name)

        transformers: list[tuple[str, Any, list[int]]] = []
        feature_blocks: list[np.ndarray] = []
        feature_names: list[str] = []

        if numeric_features:
            numeric_array = np.array(numeric_features, dtype=float).T
            feature_blocks.append(numeric_array)
            feature_names.extend(numeric_names)

        if categorical_features:
            categorical_array = np.array(categorical_features, dtype=str).T
            encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            encoded = encoder.fit_transform(categorical_array)
            feature_blocks.append(encoded)
            for name, categories in zip(
                categorical_names,
                encoder.categories_,
                strict=True,
            ):
                for category in categories:
                    feature_names.append(f"{name}={category}")

        features = (
            np.hstack(feature_blocks)
            if len(feature_blocks) > 1
            else feature_blocks[0]
        )
        target = np.array(target_values, dtype=float)

        return _PreparedMatrix(
            features=features,
            target=target,
            feature_names=feature_names,
        )

    def _feature_importance(
        self,
        *,
        model: Any,
        feature_names: list[str],
        algorithm: str,
    ) -> list[FeatureImportanceItem]:
        if algorithm == "random_forest":
            estimator = model
            values = estimator.feature_importances_
        elif algorithm == "decision_tree":
            values = model.feature_importances_
        elif algorithm == "linear":
            values = np.abs(model.coef_)
        elif algorithm == "polynomial":
            linear_step = model.named_steps["model"]
            values = np.abs(linear_step.coef_)
        else:
            return []

        if len(values) != len(feature_names):
            feature_names = [
                f"feature_{index}"
                for index in range(len(values))
            ]

        pairs = sorted(
            zip(feature_names, values, strict=False),
            key=lambda item: item[1],
            reverse=True,
        )
        return [
            FeatureImportanceItem(
                feature=name,
                importance=round(float(score), 4),
            )
            for name, score in pairs[:20]
            if float(score) > 0
        ]


class _PreparedMatrix:
    """Prepared feature matrix and target vector."""

    def __init__(
        self,
        *,
        features: np.ndarray,
        target: np.ndarray,
        feature_names: list[str],
    ) -> None:
        self.features = features
        self.target = target
        self.feature_names = feature_names


regression_service = RegressionService()
