"""Machine learning request and response schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field

RegressionAlgorithm = Literal[
    "linear",
    "polynomial",
    "decision_tree",
    "random_forest",
]


class RegressionRequest(BaseModel):
    """Train a regression model on an uploaded CSV file."""

    algorithm: RegressionAlgorithm
    target_column: str
    feature_columns: list[str] = Field(min_length=1)
    test_size: float = Field(default=0.2, gt=0.0, lt=1.0)
    random_state: int = 42


class RegressionMetrics(BaseModel):
    """Regression evaluation metrics on the hold-out test set."""

    mae: float
    rmse: float
    r2: float


class ActualVsPredicted(BaseModel):
    """Single actual vs predicted pair."""

    actual: float
    predicted: float


class FeatureImportanceItem(BaseModel):
    """Feature contribution for tree-based or linear models."""

    feature: str
    importance: float


class RegressionExplainability(BaseModel):
    """Lightweight explainability payload returned with regression results."""

    supported: bool = False
    method: str | None = None
    notes: str | None = None


class RegressionResult(BaseModel):
    """Regression training result."""

    result_id: str
    model_type: Literal["regression"] = "regression"
    file_id: int
    algorithm: RegressionAlgorithm
    target_column: str
    feature_columns: list[str]
    train_rows: int
    test_rows: int
    metrics: RegressionMetrics
    actual_vs_predicted: list[ActualVsPredicted]
    residuals: list[float]
    feature_importance: list[FeatureImportanceItem] = Field(default_factory=list)
    explainability: RegressionExplainability = Field(
        default_factory=RegressionExplainability,
    )


class ModelAlgorithmInfo(BaseModel):
    """Registered model algorithm metadata."""

    id: str
    label: str
    model_type: str
    description: str


class ModelRegistryResponse(BaseModel):
    """Available built-in model algorithms."""

    regression: list[ModelAlgorithmInfo]
    classification: list[ModelAlgorithmInfo] = Field(default_factory=list)
    plugins: list[dict[str, Any]] = Field(default_factory=list)


ClassificationAlgorithm = Literal[
    "logistic",
    "decision_tree",
    "random_forest",
    "knn",
    "svm",
    "naive_bayes",
]


class ClassificationRequest(BaseModel):
    """Train a classification model on an uploaded CSV file."""

    algorithm: ClassificationAlgorithm
    target_column: str
    feature_columns: list[str] = Field(min_length=1)
    test_size: float = Field(default=0.2, gt=0.0, lt=1.0)
    random_state: int = 42


class ClassificationMetrics(BaseModel):
    """Classification evaluation metrics on the hold-out test set."""

    accuracy: float
    precision: float
    recall: float
    f1: float


class ConfusionMatrix(BaseModel):
    """Confusion matrix with row/column class labels."""

    labels: list[str] = Field(default_factory=list)
    matrix: list[list[int]] = Field(default_factory=list)
    included: bool = True
    class_count: int = 0
    message: str | None = None


class ClassReportItem(BaseModel):
    """Per-class precision, recall, and F1."""

    label: str
    precision: float
    recall: float
    f1: float
    support: int


class ClassificationPrediction(BaseModel):
    """Single actual vs predicted label with optional confidence."""

    actual: str
    predicted: str
    confidence: float | None = None


class ClassificationResult(BaseModel):
    """Classification training result."""

    result_id: str
    model_type: Literal["classification"] = "classification"
    file_id: int
    algorithm: ClassificationAlgorithm
    target_column: str
    feature_columns: list[str]
    train_rows: int
    test_rows: int
    metrics: ClassificationMetrics
    confusion_matrix: ConfusionMatrix
    classification_report: list[ClassReportItem]
    predictions: list[ClassificationPrediction]
