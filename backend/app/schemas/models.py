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
    clustering: list[ModelAlgorithmInfo] = Field(default_factory=list)
    timeseries: list[ModelAlgorithmInfo] = Field(default_factory=list)
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


ClusteringAlgorithm = Literal["kmeans", "hierarchical"]


class ClusteringRequest(BaseModel):
    """Cluster rows in an uploaded CSV file."""

    algorithm: ClusteringAlgorithm
    feature_columns: list[str] = Field(min_length=1)
    n_clusters: int = Field(default=3, ge=2, le=20)
    max_k: int = Field(default=8, ge=2, le=15)
    random_state: int = 42


class ElbowPoint(BaseModel):
    """Inertia for a k-means cluster count."""

    k: int
    inertia: float


class ClusterAssignment(BaseModel):
    """Cluster label for a single row."""

    row_index: int
    cluster: int


class ClusteringResult(BaseModel):
    """Clustering output with elbow diagnostics."""

    result_id: str
    model_type: Literal["clustering"] = "clustering"
    file_id: int
    algorithm: ClusteringAlgorithm
    feature_columns: list[str]
    row_count: int
    n_clusters: int
    assignments: list[ClusterAssignment]
    cluster_sizes: dict[int, int]
    elbow: list[ElbowPoint]
    silhouette: float | None = None


class PCARequest(BaseModel):
    """Run PCA on feature columns from an uploaded CSV file."""

    feature_columns: list[str] = Field(min_length=1)
    n_components: int = Field(default=2, ge=1, le=10)
    random_state: int = 42


class PCALoading(BaseModel):
    """Feature weight for a principal component."""

    feature: str
    weight: float


class PCAComponent(BaseModel):
    """Single principal component summary."""

    name: str
    explained_variance_ratio: float
    loadings: list[PCALoading]


class PCAResult(BaseModel):
    """PCA output with variance and row projections."""

    result_id: str
    model_type: Literal["pca"] = "pca"
    file_id: int
    feature_columns: list[str]
    row_count: int
    n_components: int
    total_explained_variance: float
    components: list[PCAComponent]
    projections: list[list[float]]


TimeseriesAlgorithm = Literal["moving_average", "autoregressive", "arima", "sarimax"]


class TimeseriesRequest(BaseModel):
    """Forecast a numeric series using date and value columns."""

    algorithm: TimeseriesAlgorithm
    date_column: str
    value_column: str
    forecast_periods: int = Field(default=5, ge=1, le=30)
    train_ratio: float = Field(default=0.75, gt=0.5, lt=0.95)
    window: int = Field(default=3, ge=2, le=30)
    ar_lags: int = Field(default=3, ge=1, le=20)
    arima_p: int = Field(default=1, ge=0, le=5)
    arima_d: int = Field(default=1, ge=0, le=2)
    arima_q: int = Field(default=1, ge=0, le=5)
    seasonal_period: int | None = Field(default=None, ge=2, le=365)


class TimeseriesMetrics(BaseModel):
    """Hold-out forecast accuracy metrics."""

    mae: float
    rmse: float
    mape: float | None = None


class TimeseriesPoint(BaseModel):
    """Actual and/or forecast value for one time step."""

    label: str
    actual: float | None = None
    forecast: float | None = None


class TimeseriesResult(BaseModel):
    """Time series forecast output."""

    result_id: str
    model_type: Literal["timeseries"] = "timeseries"
    file_id: int
    algorithm: TimeseriesAlgorithm
    date_column: str
    value_column: str
    row_count: int
    train_rows: int
    test_rows: int
    metrics: TimeseriesMetrics
    history: list[TimeseriesPoint]
    forecast: list[TimeseriesPoint]


SimilarityMode = Literal["row", "item"]


class SimilarityRequest(BaseModel):
    """Run cosine similarity across rows or selected feature columns."""

    mode: SimilarityMode = "row"
    feature_columns: list[str] = Field(min_length=1)
    id_column: str | None = None
    top_n: int = Field(default=10, ge=1, le=50)


class SimilarityMatrixRow(BaseModel):
    """One row in the similarity matrix preview."""

    label: str
    values: list[float]


class SimilarityTopPair(BaseModel):
    """High-scoring pair from a similarity matrix."""

    left: str
    right: str
    score: float


class SimilarityResult(BaseModel):
    """Cosine similarity output with suitability messaging."""

    result_id: str
    model_type: Literal["similarity"] = "similarity"
    file_id: int
    mode: SimilarityMode
    feature_columns: list[str]
    row_count: int
    item_count: int
    similarity_matrix_preview: list[SimilarityMatrixRow]
    top_pairs: list[SimilarityTopPair]
    suitable: bool
    suitability_note: str
