"""Similarity and recommendation service."""

import csv
import uuid
from io import StringIO
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import UploadedFile
from app.schemas.models import (
    SimilarityMatrixRow,
    SimilarityRequest,
    SimilarityResult,
    SimilarityTopPair,
)
from app.utils.encoding_utils import decode_csv_bytes
from app.utils.type_utils import coerce_float, is_missing, normalize_cell


class RecommendationError(ValueError):
    """Raised when similarity analysis cannot access a dataset."""


class RecommendationService:
    """Cosine similarity for rows or feature columns."""

    def __init__(self) -> None:
        self._results: dict[str, SimilarityResult] = {}

    def clear_results(self) -> None:
        """Clear stored results (used in tests)."""
        self._results.clear()

    def run_similarity(
        self,
        db: Session,
        *,
        file_id: int,
        request: SimilarityRequest,
    ) -> SimilarityResult:
        """Run cosine similarity and return a matrix preview plus top pairs."""
        file = self._get_file(db, file_id)
        prepared = self._load_numeric_matrix(file, request)
        if not prepared.suitable:
            result = self._unsuitable_result(file_id, request, prepared.note)
            self._results[result.result_id] = result
            return result

        labels = prepared.labels
        matrix = prepared.matrix
        if request.mode == "item":
            matrix = matrix.T
            labels = request.feature_columns

        similarity = self._cosine_similarity(matrix)
        preview = [
            SimilarityMatrixRow(
                label=labels[index],
                values=[round(float(value), 4) for value in row[:5]],
            )
            for index, row in enumerate(similarity[:5])
        ]
        top_pairs = self._top_pairs(labels, similarity, request.top_n)

        result = SimilarityResult(
            result_id=str(uuid.uuid4()),
            file_id=file_id,
            mode=request.mode,
            feature_columns=request.feature_columns,
            row_count=prepared.row_count,
            item_count=len(labels),
            similarity_matrix_preview=preview,
            top_pairs=top_pairs,
            suitable=True,
            suitability_note=(
                "Cosine similarity computed successfully. Higher scores indicate more "
                "similar rows or items."
            ),
        )
        self._results[result.result_id] = result
        return result

    def get_result(self, result_id: str) -> SimilarityResult:
        """Return a stored similarity result."""
        result = self._results.get(result_id)
        if result is None:
            raise RecommendationError("Similarity result not found")
        return result

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise RecommendationError("File not found")
        return file

    def _read_file_bytes(self, file: UploadedFile) -> bytes:
        path = Path(get_settings().upload_dir) / file.stored_path
        if not path.exists():
            raise RecommendationError("Stored file not found")
        return path.read_bytes()

    def _load_numeric_matrix(
        self,
        file: UploadedFile,
        request: SimilarityRequest,
    ) -> "_PreparedSimilarityMatrix":
        content = self._read_file_bytes(file)
        text = decode_csv_bytes(content)
        rows = list(csv.reader(StringIO(text, newline="")))
        if not rows or not rows[0]:
            return _PreparedSimilarityMatrix.unsuitable("CSV must contain a header row")

        headers = [header.strip() for header in rows[0]]
        missing_columns = [
            column
            for column in [*request.feature_columns, request.id_column]
            if column and column not in headers
        ]
        if missing_columns:
            raise RecommendationError(f"Column not found: {missing_columns[0]}")

        column_indexes = {name: index for index, name in enumerate(headers)}
        feature_indexes = [column_indexes[name] for name in request.feature_columns]
        id_index = column_indexes.get(request.id_column) if request.id_column else None

        labels: list[str] = []
        numeric_rows: list[list[float]] = []
        for row_index, row in enumerate(rows[1:], start=1):
            if len(row) < len(headers):
                row = row + [""] * (len(headers) - len(row))
            values = [normalize_cell(row[index]) for index in feature_indexes]
            if any(is_missing(value) for value in values):
                continue
            numeric_values = [coerce_float(value) for value in values]
            if any(value is None for value in numeric_values):
                continue
            numeric_rows.append([float(value) for value in numeric_values if value is not None])
            if id_index is not None:
                label = normalize_cell(row[id_index]) or f"row {row_index}"
            else:
                label = f"row {row_index}"
            labels.append(label)

        if len(numeric_rows) < 2:
            return _PreparedSimilarityMatrix.unsuitable(
                "Similarity needs at least two complete numeric rows.",
            )
        if request.mode == "item" and len(request.feature_columns) < 2:
            return _PreparedSimilarityMatrix.unsuitable(
                "Item similarity needs at least two numeric feature columns.",
            )

        matrix = np.asarray(numeric_rows, dtype=float)
        if np.allclose(matrix, 0):
            return _PreparedSimilarityMatrix.unsuitable(
                "Similarity is not suitable when all selected values are zero.",
            )
        return _PreparedSimilarityMatrix(
            matrix=matrix,
            labels=labels,
            row_count=len(numeric_rows),
            suitable=True,
            note="",
        )

    def _cosine_similarity(self, matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1)
        safe_norms = np.where(norms == 0, 1, norms)
        normalized = matrix / safe_norms[:, np.newaxis]
        return np.clip(normalized @ normalized.T, -1.0, 1.0)

    def _top_pairs(
        self,
        labels: list[str],
        similarity: np.ndarray,
        top_n: int,
    ) -> list[SimilarityTopPair]:
        pairs: list[SimilarityTopPair] = []
        for left_index in range(len(labels)):
            for right_index in range(left_index + 1, len(labels)):
                pairs.append(
                    SimilarityTopPair(
                        left=labels[left_index],
                        right=labels[right_index],
                        score=round(float(similarity[left_index, right_index]), 4),
                    ),
                )
        return sorted(pairs, key=lambda pair: pair.score, reverse=True)[:top_n]

    def _unsuitable_result(
        self,
        file_id: int,
        request: SimilarityRequest,
        note: str,
    ) -> SimilarityResult:
        return SimilarityResult(
            result_id=str(uuid.uuid4()),
            file_id=file_id,
            mode=request.mode,
            feature_columns=request.feature_columns,
            row_count=0,
            item_count=0,
            similarity_matrix_preview=[],
            top_pairs=[],
            suitable=False,
            suitability_note=note,
        )


class _PreparedSimilarityMatrix:
    """Prepared numeric matrix for similarity analysis."""

    def __init__(
        self,
        *,
        matrix: np.ndarray,
        labels: list[str],
        row_count: int,
        suitable: bool,
        note: str,
    ) -> None:
        self.matrix = matrix
        self.labels = labels
        self.row_count = row_count
        self.suitable = suitable
        self.note = note

    @classmethod
    def unsuitable(cls, note: str) -> "_PreparedSimilarityMatrix":
        return cls(
            matrix=np.asarray([], dtype=float),
            labels=[],
            row_count=0,
            suitable=False,
            note=note,
        )


recommendation_service = RecommendationService()
