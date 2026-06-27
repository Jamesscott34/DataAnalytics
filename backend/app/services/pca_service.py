"""Principal component analysis service."""

import csv
import uuid
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import UploadedFile
from app.schemas.models import (
    PCAComponent,
    PCALoading,
    PCARequest,
    PCAResult,
)
from app.services.result_persistence_service import result_persistence_service
from app.utils.encoding_utils import decode_csv_bytes
from app.utils.type_utils import coerce_float, is_missing, normalize_cell


class PCAError(ValueError):
    """Raised when PCA cannot be run on a dataset."""


class PCAService:
    """PCA on uploaded CSV numeric/categorical feature columns."""

    def __init__(self) -> None:
        self._results: dict[str, PCAResult] = {}

    def clear_results(self) -> None:
        """Clear stored PCA results (used in tests)."""
        self._results.clear()

    def run_pca(
        self,
        db: Session,
        *,
        file_id: int,
        request: PCARequest,
    ) -> PCAResult:
        """Run PCA and return variance ratios, loadings, and projections."""
        file = self._get_file(db, file_id)
        matrix = self._load_features(file, request.feature_columns)
        row_count = matrix.features.shape[0]
        feature_count = matrix.features.shape[1]

        if row_count < 2:
            raise PCAError("Need at least two rows for PCA")
        n_components = min(request.n_components, feature_count, row_count)
        if n_components < 1:
            raise PCAError("Not enough features for PCA")

        scaler = StandardScaler()
        scaled = scaler.fit_transform(matrix.features)
        model = PCA(n_components=n_components, random_state=request.random_state)
        projected = model.fit_transform(scaled)

        components: list[PCAComponent] = []
        for index, ratio in enumerate(model.explained_variance_ratio_):
            loadings = [
                PCALoading(
                    feature=str(matrix.feature_names[feature_index]),
                    weight=round(float(model.components_[index, feature_index]), 4),
                )
                for feature_index in range(feature_count)
            ]
            components.append(
                PCAComponent(
                    name=f"PC{index + 1}",
                    explained_variance_ratio=round(float(ratio), 4),
                    loadings=loadings,
                ),
            )

        projection_limit = min(row_count, 100)
        projections = [
            [round(float(value), 4) for value in row]
            for row in projected[:projection_limit]
        ]

        result = PCAResult(
            result_id=str(uuid.uuid4()),
            file_id=file_id,
            feature_columns=request.feature_columns,
            row_count=row_count,
            n_components=n_components,
            total_explained_variance=round(
                float(sum(model.explained_variance_ratio_)),
                4,
            ),
            components=components,
            projections=projections,
        )
        return result_persistence_service.save_model(
            db,
            self._results,
            result,
            result_type="pca",
        )

    def get_result(self, result_id: str, db: Session | None = None) -> PCAResult:
        """Return a stored PCA result."""
        result = result_persistence_service.load_model(
            db,
            self._results,
            result_id,
            PCAResult,
        )
        if result is None:
            raise PCAError("PCA result not found")
        return result

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise PCAError("File not found")
        return file

    def _read_file_bytes(self, file: UploadedFile) -> bytes:
        upload_dir = Path(get_settings().upload_dir)
        path = upload_dir / file.stored_path
        if not path.exists():
            raise PCAError("Stored file not found")
        return path.read_bytes()

    def _load_features(self, file: UploadedFile, feature_columns: list[str]) -> Any:
        content = self._read_file_bytes(file)
        text = decode_csv_bytes(content)
        reader = csv.reader(StringIO(text, newline=""))
        rows = list(reader)
        if not rows or not rows[0]:
            raise PCAError("CSV must contain a header row")

        headers = [header.strip() for header in rows[0]]
        for column in feature_columns:
            if column not in headers:
                raise PCAError(f"Feature column not found: {column}")

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

        if len(usable_rows) < 2:
            raise PCAError("Need at least two complete rows for PCA")

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
            raise PCAError("No usable numeric or categorical features found")

        return _PreparedFeatureMatrix(
            features=np.hstack(parts),
            feature_names=feature_names,
        )


class _PreparedFeatureMatrix:
    """Prepared feature matrix for PCA."""

    def __init__(self, *, features: np.ndarray, feature_names: list[str]) -> None:
        self.features = features
        self.feature_names = feature_names


pca_service = PCAService()
