"""Clustering service for k-means and hierarchical clustering."""

import csv
import uuid
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import UploadedFile
from app.schemas.models import (
    ClusterAssignment,
    ClusteringRequest,
    ClusteringResult,
    ElbowPoint,
)
from app.services.plugin_registry import (
    ClusteringAlgorithmSpec,
    get_clustering_algorithm,
    register_clustering_algorithm,
)
from app.services.result_persistence_service import result_persistence_service
from app.utils.encoding_utils import decode_csv_bytes
from app.utils.type_utils import coerce_float, is_missing, normalize_cell


class ClusteringError(ValueError):
    """Raised when clustering cannot be run on a dataset."""


class ClusteringService:
    """K-means and hierarchical clustering on uploaded CSV files."""

    def __init__(self) -> None:
        self._results: dict[str, ClusteringResult] = {}
        self._register_builtin_algorithms()

    def clear_results(self) -> None:
        """Clear stored clustering results (used in tests)."""
        self._results.clear()

    def run_clustering(
        self,
        db: Session,
        *,
        file_id: int,
        request: ClusteringRequest,
    ) -> ClusteringResult:
        """Cluster rows and return assignments plus elbow data."""
        file = self._get_file(db, file_id)
        matrix = self._load_features(file, request.feature_columns)
        algorithm = get_clustering_algorithm(request.algorithm)

        if matrix.features.shape[0] < request.n_clusters:
            raise ClusteringError(
                f"Need at least {request.n_clusters} rows for {request.n_clusters} clusters",
            )

        scaler = StandardScaler()
        scaled = scaler.fit_transform(matrix.features)

        elbow = self._elbow_data(scaled, request)
        model = algorithm.builder(
            n_clusters=request.n_clusters, random_state=request.random_state
        )
        labels = model.fit_predict(scaled)

        silhouette = None
        if request.n_clusters >= 2 and len(set(labels)) > 1:
            silhouette = round(float(silhouette_score(scaled, labels)), 4)

        assignments = [
            ClusterAssignment(row_index=index, cluster=int(label))
            for index, label in enumerate(labels)
        ]
        cluster_sizes = {
            cluster: sum(1 for item in assignments if item.cluster == cluster)
            for cluster in range(request.n_clusters)
        }

        result = ClusteringResult(
            result_id=str(uuid.uuid4()),
            file_id=file_id,
            algorithm=request.algorithm,
            feature_columns=request.feature_columns,
            row_count=len(assignments),
            n_clusters=request.n_clusters,
            assignments=assignments,
            cluster_sizes=cluster_sizes,
            elbow=elbow,
            silhouette=silhouette,
        )
        return result_persistence_service.save_model(
            db,
            self._results,
            result,
            result_type="clustering",
            algorithm=request.algorithm,
        )

    def get_result(self, result_id: str, db: Session | None = None) -> ClusteringResult:
        """Return a stored clustering result."""
        result = result_persistence_service.load_model(
            db,
            self._results,
            result_id,
            ClusteringResult,
        )
        if result is None:
            raise ClusteringError("Clustering result not found")
        return result

    def _elbow_data(
        self, features: np.ndarray, request: ClusteringRequest
    ) -> list[ElbowPoint]:
        """Compute inertia for k=1..max_k to support elbow plots."""
        max_k = min(request.max_k, features.shape[0])
        points: list[ElbowPoint] = []
        for k in range(1, max_k + 1):
            model = KMeans(n_clusters=k, random_state=request.random_state, n_init=10)
            model.fit(features)
            points.append(ElbowPoint(k=k, inertia=round(float(model.inertia_), 4)))
        return points

    def _register_builtin_algorithms(self) -> None:
        register_clustering_algorithm(
            ClusteringAlgorithmSpec(
                id="kmeans",
                label="K-means",
                description="Partition rows into k spherical clusters.",
                builder=lambda n_clusters, random_state: KMeans(
                    n_clusters=n_clusters,
                    random_state=random_state,
                    n_init=10,
                ),
            ),
        )
        register_clustering_algorithm(
            ClusteringAlgorithmSpec(
                id="hierarchical",
                label="Hierarchical",
                description="Agglomerative clustering with ward linkage.",
                builder=lambda n_clusters, random_state: AgglomerativeClustering(
                    n_clusters=n_clusters,
                ),
            ),
        )

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise ClusteringError("File not found")
        return file

    def _read_file_bytes(self, file: UploadedFile) -> bytes:
        upload_dir = Path(get_settings().upload_dir)
        path = upload_dir / file.stored_path
        if not path.exists():
            raise ClusteringError("Stored file not found")
        return path.read_bytes()

    def _load_features(self, file: UploadedFile, feature_columns: list[str]) -> Any:
        content = self._read_file_bytes(file)
        text = decode_csv_bytes(content)
        reader = csv.reader(StringIO(text, newline=""))
        rows = list(reader)
        if not rows or not rows[0]:
            raise ClusteringError("CSV must contain a header row")

        headers = [header.strip() for header in rows[0]]
        for column in feature_columns:
            if column not in headers:
                raise ClusteringError(f"Feature column not found: {column}")

        column_indexes = {name: index for index, name in enumerate(headers)}
        feature_indexes = [column_indexes[name] for name in feature_columns]

        usable_rows: list[list[str]] = []
        for row in rows[1:]:
            if len(row) < len(headers):
                row = row + [""] * (len(headers) - len(row))
            feature_cells = [normalize_cell(row[index]) for index in feature_indexes]
            if any(is_missing(cell) for cell in feature_cells):
                continue
            usable_rows.append(feature_cells)

        if len(usable_rows) < 3:
            raise ClusteringError("Need at least three complete rows for clustering")

        numeric_features: list[list[float]] = []
        categorical_features: list[list[str]] = []
        numeric_names: list[str] = []
        categorical_names: list[str] = []

        for column_name, column_values in zip(
            feature_columns,
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

        parts: list[np.ndarray] = []
        feature_names: list[str] = []
        if numeric_features:
            parts.append(np.asarray(numeric_features, dtype=float).T)
            feature_names.extend(numeric_names)
        if categorical_features:
            encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
            encoded = encoder.fit_transform(np.asarray(categorical_features).T)
            parts.append(encoded)
            feature_names.extend(
                encoder.get_feature_names_out(categorical_names).tolist(),
            )

        if not parts:
            raise ClusteringError("No usable numeric or categorical features found")

        return _PreparedFeatureMatrix(
            features=np.hstack(parts),
            feature_names=feature_names,
        )


class _PreparedFeatureMatrix:
    """Prepared feature matrix for unsupervised learning."""

    def __init__(self, *, features: np.ndarray, feature_names: list[str]) -> None:
        self.features = features
        self.feature_names = feature_names


clustering_service = ClusteringService()
