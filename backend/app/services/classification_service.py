"""Classification model training service."""

import csv
import uuid
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import UploadedFile
from app.schemas.models import (
    ClassificationMetrics,
    ClassificationPrediction,
    ClassificationRequest,
    ClassificationResult,
    ClassReportItem,
    ConfusionMatrix,
)
from app.services.plugin_registry import (
    ClassificationAlgorithmSpec,
    get_classification_algorithm,
    register_classification_algorithm,
)
from app.services.result_persistence_service import result_persistence_service
from app.utils.encoding_utils import decode_csv_bytes
from app.utils.type_utils import coerce_float, is_missing, normalize_cell


class ClassificationError(ValueError):
    """Raised when classification cannot be trained on a dataset."""


# Confusion matrices above this size are omitted from API responses and reports.
MAX_DISPLAY_CLASSES = 12


class ClassificationService:
    """Service for training classification models on uploaded CSV files."""

    def __init__(self) -> None:
        self._results: dict[str, ClassificationResult] = {}
        self._register_builtin_algorithms()

    def clear_results(self) -> None:
        """Clear stored classification results (used in tests)."""
        self._results.clear()

    def run_classification(
        self,
        db: Session,
        *,
        file_id: int,
        request: ClassificationRequest,
    ) -> ClassificationResult:
        """Train a classifier and return metrics and predictions."""
        file = self._get_file(db, file_id)
        matrix = self._load_matrix(file, request)
        algorithm = get_classification_algorithm(request.algorithm)
        model = algorithm.builder()

        stratify = matrix.target
        class_count = len(set(matrix.target))
        test_count = max(1, int(len(matrix.target) * request.test_size))
        if (
            class_count < 2
            or min(Counter(matrix.target).values()) < 2
            or test_count < class_count
        ):
            stratify = None

        x_train, x_test, y_train, y_test = train_test_split(
            matrix.features,
            matrix.target,
            test_size=request.test_size,
            random_state=request.random_state,
            stratify=stratify,
        )
        if len(x_train) < 2 or len(x_test) < 1:
            raise ClassificationError("Not enough rows for train/test split")

        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        confidence_scores = self._confidence_scores(model, x_test)

        y_test_labels = matrix.label_encoder.inverse_transform(y_test)
        prediction_labels = matrix.label_encoder.inverse_transform(predictions)

        metrics = ClassificationMetrics(
            accuracy=round(float(accuracy_score(y_test, predictions)), 4),
            precision=round(
                float(
                    precision_score(
                        y_test,
                        predictions,
                        average="weighted",
                        zero_division=0,
                    ),
                ),
                4,
            ),
            recall=round(
                float(
                    recall_score(
                        y_test,
                        predictions,
                        average="weighted",
                        zero_division=0,
                    ),
                ),
                4,
            ),
            f1=round(
                float(
                    f1_score(
                        y_test,
                        predictions,
                        average="weighted",
                        zero_division=0,
                    ),
                ),
                4,
            ),
        )

        labels = [str(label) for label in matrix.label_encoder.classes_]
        class_count = len(labels)
        if class_count > MAX_DISPLAY_CLASSES:
            confusion = ConfusionMatrix(
                labels=[],
                matrix=[],
                included=False,
                class_count=class_count,
                message=(
                    f"Confusion matrix omitted ({class_count} classes). "
                    f"Use a categorical target with at most {MAX_DISPLAY_CLASSES} classes, "
                    "or use regression for numeric targets."
                ),
            )
            report = []
        else:
            matrix_values = confusion_matrix(
                y_test,
                predictions,
                labels=list(range(class_count)),
            )
            confusion = ConfusionMatrix(
                labels=labels,
                matrix=matrix_values.astype(int).tolist(),
                included=True,
                class_count=class_count,
            )
            report = self._classification_report(
                y_test=y_test,
                predictions=predictions,
                label_encoder=matrix.label_encoder,
            )
        prediction_rows = [
            ClassificationPrediction(
                actual=str(actual),
                predicted=str(predicted),
                confidence=confidence,
            )
            for actual, predicted, confidence in zip(
                y_test_labels,
                prediction_labels,
                confidence_scores,
                strict=True,
            )
        ]

        result = ClassificationResult(
            result_id=str(uuid.uuid4()),
            file_id=file_id,
            algorithm=request.algorithm,
            target_column=request.target_column,
            feature_columns=request.feature_columns,
            train_rows=len(x_train),
            test_rows=len(x_test),
            metrics=metrics,
            confusion_matrix=confusion,
            classification_report=report,
            predictions=prediction_rows,
        )
        return result_persistence_service.save_model(
            db,
            self._results,
            result,
            result_type="classification",
            algorithm=request.algorithm,
        )

    def get_result(
        self, result_id: str, db: Session | None = None
    ) -> ClassificationResult:
        """Return a stored classification result."""
        result = result_persistence_service.load_model(
            db,
            self._results,
            result_id,
            ClassificationResult,
        )
        if result is None:
            raise ClassificationError("Classification result not found")
        return result

    def _register_builtin_algorithms(self) -> None:
        register_classification_algorithm(
            ClassificationAlgorithmSpec(
                id="logistic",
                label="Logistic regression",
                description="Linear classifier for binary and multiclass labels.",
                builder=lambda: Pipeline(
                    [
                        ("scaler", StandardScaler()),
                        ("model", LogisticRegression(max_iter=1000)),
                    ],
                ),
            ),
        )
        register_classification_algorithm(
            ClassificationAlgorithmSpec(
                id="decision_tree",
                label="Decision tree",
                description="Single decision tree classifier.",
                builder=lambda: DecisionTreeClassifier(random_state=42),
            ),
        )
        register_classification_algorithm(
            ClassificationAlgorithmSpec(
                id="random_forest",
                label="Random forest",
                description="Ensemble of decision trees for classification.",
                builder=lambda: RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                ),
            ),
        )
        register_classification_algorithm(
            ClassificationAlgorithmSpec(
                id="knn",
                label="K-nearest neighbors",
                description="Distance-based classifier with scaled features.",
                builder=lambda: Pipeline(
                    [
                        ("scaler", StandardScaler()),
                        ("model", KNeighborsClassifier()),
                    ],
                ),
            ),
        )
        register_classification_algorithm(
            ClassificationAlgorithmSpec(
                id="svm",
                label="Support vector machine",
                description="SVM classifier with probability estimates.",
                builder=lambda: Pipeline(
                    [
                        ("scaler", StandardScaler()),
                        (
                            "model",
                            SVC(probability=True, random_state=42),
                        ),
                    ],
                ),
            ),
        )
        register_classification_algorithm(
            ClassificationAlgorithmSpec(
                id="naive_bayes",
                label="Naive Bayes",
                description="Gaussian naive Bayes classifier.",
                builder=lambda: GaussianNB(),
            ),
        )

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise ClassificationError("File not found")
        return file

    def _read_file_bytes(self, file: UploadedFile) -> bytes:
        upload_dir = Path(get_settings().upload_dir)
        path = upload_dir / file.stored_path
        if not path.exists():
            raise ClassificationError("Stored file not found")
        return path.read_bytes()

    def _load_matrix(self, file: UploadedFile, request: ClassificationRequest) -> Any:
        content = self._read_file_bytes(file)
        text = decode_csv_bytes(content)
        reader = csv.reader(StringIO(text, newline=""))
        rows = list(reader)
        if not rows or not rows[0]:
            raise ClassificationError("CSV must contain a header row")

        headers = [header.strip() for header in rows[0]]
        if request.target_column not in headers:
            raise ClassificationError(
                f"Target column not found: {request.target_column}"
            )
        for column in request.feature_columns:
            if column not in headers:
                raise ClassificationError(f"Feature column not found: {column}")
        if request.target_column in request.feature_columns:
            raise ClassificationError("Target column cannot also be a feature column")

        column_indexes = {name: index for index, name in enumerate(headers)}
        target_index = column_indexes[request.target_column]
        feature_indexes = [column_indexes[name] for name in request.feature_columns]

        raw_rows: list[list[str]] = []
        for row in rows[1:]:
            if len(row) < len(headers):
                row = row + [""] * (len(headers) - len(row))
            raw_rows.append(row)

        usable_rows: list[list[str]] = []
        target_values: list[str] = []
        for row in raw_rows:
            target_text = normalize_cell(row[target_index])
            if is_missing(target_text):
                continue
            feature_cells = [normalize_cell(row[index]) for index in feature_indexes]
            if any(is_missing(cell) for cell in feature_cells):
                continue
            usable_rows.append(feature_cells)
            target_values.append(target_text)

        if len(usable_rows) < 4:
            raise ClassificationError(
                "Need at least four complete rows for classification"
            )

        label_encoder = LabelEncoder()
        encoded_target = label_encoder.fit_transform(target_values)
        if len(label_encoder.classes_) < 2:
            raise ClassificationError("Target column must have at least two classes")

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
            np.hstack(feature_blocks) if len(feature_blocks) > 1 else feature_blocks[0]
        )

        return _PreparedClassificationMatrix(
            features=features,
            target=encoded_target,
            feature_names=feature_names,
            label_encoder=label_encoder,
        )

    def _confidence_scores(self, model: Any, x_test: np.ndarray) -> list[float | None]:
        estimator = model
        if hasattr(model, "named_steps"):
            estimator = model.named_steps.get("model", model)
        if not hasattr(estimator, "predict_proba"):
            return [None] * len(x_test)
        probabilities = model.predict_proba(x_test)
        return [round(float(max(row)), 4) for row in probabilities]

    def _classification_report(
        self,
        *,
        y_test: np.ndarray,
        predictions: np.ndarray,
        label_encoder: LabelEncoder,
    ) -> list[ClassReportItem]:
        report: list[ClassReportItem] = []
        for index, label in enumerate(label_encoder.classes_):
            mask_actual = y_test == index
            mask_predicted = predictions == index
            true_positive = int(np.sum((y_test == index) & (predictions == index)))
            predicted_positive = int(np.sum(mask_predicted))
            actual_positive = int(np.sum(mask_actual))
            precision = (
                true_positive / predicted_positive if predicted_positive else 0.0
            )
            recall = true_positive / actual_positive if actual_positive else 0.0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall)
                else 0.0
            )
            report.append(
                ClassReportItem(
                    label=str(label),
                    precision=round(float(precision), 4),
                    recall=round(float(recall), 4),
                    f1=round(float(f1), 4),
                    support=actual_positive,
                ),
            )
        return report


class _PreparedClassificationMatrix:
    """Prepared feature matrix and encoded target labels."""

    def __init__(
        self,
        *,
        features: np.ndarray,
        target: np.ndarray,
        feature_names: list[str],
        label_encoder: LabelEncoder,
    ) -> None:
        self.features = features
        self.target = target
        self.feature_names = feature_names
        self.label_encoder = label_encoder


classification_service = ClassificationService()
