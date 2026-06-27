"""Exploratory data analysis service.

Loads stored CSV files, infers column types, computes summary statistics,
and caches results by file hash.
"""

import statistics
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.uploaded_file import UploadedFile
from app.schemas.eda import (
    CategoricalStats,
    ColumnSummary,
    EDAResponse,
    EDASuggestions,
    EDASummary,
    NumericStats,
    TopValue,
)
from app.services.classification_service import MAX_DISPLAY_CLASSES
from app.services.result_persistence_service import result_persistence_service
from app.utils.csv_parse_utils import CSVParseError, parse_csv_rows
from app.utils.encoding_utils import decode_csv_bytes
from app.utils.type_utils import (
    coerce_float,
    infer_column_type,
    is_missing,
    normalize_cell,
)


class EDAError(ValueError):
    """Raised when EDA cannot be performed on a dataset."""


class EDAService:
    """Service for exploratory data analysis of uploaded CSV files."""

    def __init__(self) -> None:
        self._cache_by_hash: dict[str, EDAResponse] = {}

    def clear_cache(self) -> None:
        """Clear the in-memory EDA cache (used in tests)."""
        self._cache_by_hash.clear()

    def run_for_file(
        self,
        db: Session,
        *,
        file_id: int,
        force_refresh: bool = False,
    ) -> EDAResponse:
        """Run or return cached EDA for an uploaded file.

        Args:
            db: Active database session.
            file_id: Uploaded file primary key.
            force_refresh: Recompute even when a hash cache entry exists.

        Returns:
            EDAResponse with summary, columns, warnings, and chart data.
        """
        file = self._get_file(db, file_id)
        if not force_refresh:
            cached = self._cache_by_hash.get(file.file_hash)
            if cached is not None:
                return cached.model_copy(update={"cached": True})

        content = self._read_file_bytes(file)
        text = decode_csv_bytes(content)
        response = self._analyze_text(
            text,
            file_hash=file.file_hash,
            file_id=file_id,
            cached=False,
        )
        self._cache_by_hash[file.file_hash] = response
        result_persistence_service.persist(
            db,
            result_id=response.result_id or f"eda:{file.file_hash}",
            file_id=file_id,
            result_type="eda",
            payload=response.model_dump(mode="json"),
        )
        return response

    def get_cached_for_file(self, db: Session, *, file_id: int) -> EDAResponse:
        """Return cached EDA for a file or raise when missing."""
        file = self._get_file(db, file_id)
        cached = self._cache_by_hash.get(file.file_hash)
        if cached is None:
            raise EDAError("EDA has not been run for this file")
        return cached.model_copy(update={"cached": True})

    def get_column_summary(
        self,
        db: Session,
        *,
        file_id: int,
        column_name: str,
    ) -> ColumnSummary:
        """Return a single column summary from cached or fresh EDA."""
        response = self.run_for_file(db, file_id=file_id)
        for column in response.columns:
            if column.name == column_name:
                return column
        raise EDAError(f"Column not found: {column_name}")

    def get_suggestions(self, db: Session, *, file_id: int) -> EDASuggestions:
        """Derive modelling suggestions from EDA output."""
        response = self.run_for_file(db, file_id=file_id)
        date_columns = [
            column.name
            for column in response.columns
            if column.inferred_type == "datetime"
        ]
        target_columns = [
            column.name
            for column in response.columns
            if column.unique_count >= 2
            and column.unique_count <= MAX_DISPLAY_CLASSES
            and (
                column.inferred_type in {"categorical", "boolean"}
                or (
                    column.inferred_type in {"integer", "float"}
                    and column.unique_count < response.summary.row_count
                )
            )
        ]
        feature_columns = [
            column.name
            for column in response.columns
            if column.inferred_type in {"integer", "float", "categorical", "boolean"}
            and column.name not in target_columns
        ]

        suggested: list[str] = []
        if date_columns and any(
            column.inferred_type in {"integer", "float"} for column in response.columns
        ):
            suggested.append("time_series")
        if len(feature_columns) >= 2 and target_columns:
            suggested.append("regression")
        if target_columns:
            suggested.append("classification")
        if len(feature_columns) >= 2:
            suggested.append("clustering")
        if response.summary.duplicate_row_count > 0:
            suggested.append("deduplication_review")

        return EDASuggestions(
            target_columns=target_columns,
            feature_columns=feature_columns,
            date_columns=date_columns,
            suggested_analyses=suggested,
        )

    def _get_file(self, db: Session, file_id: int) -> UploadedFile:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise EDAError("File not found")
        return file

    def _read_file_bytes(self, file: UploadedFile) -> bytes:
        upload_dir = Path(get_settings().upload_dir)
        path = upload_dir / file.stored_path
        if not path.exists():
            raise EDAError("Stored file not found")
        return path.read_bytes()

    def _analyze_text(
        self,
        text: str,
        *,
        file_hash: str,
        file_id: int | None = None,
        cached: bool,
    ) -> EDAResponse:
        try:
            headers, data_rows, parse_warnings = parse_csv_rows(text)
        except CSVParseError as exc:
            raise EDAError(str(exc)) from exc

        settings = get_settings()
        sampled = False
        if len(data_rows) > settings.eda_sample_max_rows:
            data_rows = data_rows[: settings.eda_sample_max_rows]
            sampled = True

        width = len(headers)
        columns_data = [
            [row[index] if index < len(row) else "" for row in data_rows]
            for index in range(width)
        ]

        duplicate_row_count = self._duplicate_row_count(data_rows)
        missing_cells = sum(
            1 for column in columns_data for value in column if is_missing(value)
        )
        total_cells = max(len(data_rows) * width, 1)

        column_summaries = [
            self._summarize_column(name, values, row_count=len(data_rows))
            for name, values in zip(headers, columns_data, strict=True)
        ]
        quality_warnings = self._quality_warnings(
            column_summaries,
            duplicate_row_count=duplicate_row_count,
            row_count=len(data_rows),
        )
        quality_warnings.extend(parse_warnings)
        if sampled:
            quality_warnings.append(
                f"Large dataset sampled to first {settings.eda_sample_max_rows:,} rows for EDA"
            )

        chart_data = self._chart_data(headers, columns_data, column_summaries)
        dataset_charts = self._dataset_charts(headers, columns_data, column_summaries)

        return EDAResponse(
            summary=EDASummary(
                row_count=len(data_rows),
                column_count=width,
                duplicate_row_count=duplicate_row_count,
                missing_cells=missing_cells,
                missing_percent=round((missing_cells / total_cells) * 100, 2),
                file_hash=file_hash,
            ),
            columns=column_summaries,
            quality_warnings=quality_warnings,
            chart_data=chart_data,
            dataset_charts=dataset_charts,
            result_id=str(uuid.uuid4()),
            sampled=sampled,
            cached=cached,
            analyzed_at=datetime.now(UTC),
        )

    def _summarize_column(
        self,
        name: str,
        values: list[str],
        *,
        row_count: int,
    ) -> ColumnSummary:
        non_missing_values = [
            normalize_cell(value) for value in values if not is_missing(value)
        ]
        inferred_type = infer_column_type(values, row_count=row_count)
        missing_count = sum(1 for value in values if is_missing(value))
        missing_percent = round((missing_count / max(row_count, 1)) * 100, 2)
        unique_count = len(set(non_missing_values))

        numeric_stats = None
        categorical_stats = None
        if inferred_type in {"integer", "float"}:
            numeric_stats = self._numeric_stats(non_missing_values)
        elif inferred_type in {"categorical", "boolean", "string"}:
            categorical_stats = self._categorical_stats(non_missing_values)

        return ColumnSummary(
            name=name,
            inferred_type=inferred_type,
            missing_count=missing_count,
            missing_percent=missing_percent,
            unique_count=unique_count,
            sample_values=non_missing_values[:5],
            numeric_stats=numeric_stats,
            categorical_stats=categorical_stats,
        )

    def _numeric_stats(self, values: list[str]) -> NumericStats:
        numbers = [
            number for value in values if (number := coerce_float(value)) is not None
        ]
        if not numbers:
            return NumericStats()
        if len(numbers) >= 2:
            quartiles = statistics.quantiles(numbers, n=4)
        else:
            quartiles = [numbers[0], numbers[0], numbers[0]]
        return NumericStats(
            min=min(numbers),
            max=max(numbers),
            mean=round(statistics.fmean(numbers), 4),
            median=round(statistics.median(numbers), 4),
            std=round(statistics.pstdev(numbers), 4) if len(numbers) > 1 else 0.0,
            q25=round(quartiles[0], 4),
            q75=round(quartiles[2], 4),
        )

    def _categorical_stats(self, values: list[str]) -> CategoricalStats:
        counts = Counter(values)
        top_values = [
            TopValue(value=value, count=count) for value, count in counts.most_common(5)
        ]
        return CategoricalStats(unique_count=len(counts), top_values=top_values)

    def _duplicate_row_count(self, data_rows: list[list[str]]) -> int:
        seen: set[tuple[str, ...]] = set()
        duplicates = 0
        for row in data_rows:
            key = tuple(normalize_cell(value) for value in row)
            if key in seen:
                duplicates += 1
            else:
                seen.add(key)
        return duplicates

    def _quality_warnings(
        self,
        columns: list[ColumnSummary],
        *,
        duplicate_row_count: int,
        row_count: int,
    ) -> list[str]:
        warnings: list[str] = []
        if duplicate_row_count > 0:
            warnings.append(f"{duplicate_row_count} duplicate rows detected")
        for column in columns:
            if column.missing_percent >= 50:
                warnings.append(f"Column '{column.name}' is more than 50% missing")
            if column.unique_count <= 1 and row_count > 1:
                warnings.append(f"Column '{column.name}' appears constant")
        return warnings

    def _chart_data(
        self,
        headers: list[str],
        columns_data: list[list[str]],
        summaries: list[ColumnSummary],
    ) -> dict[str, Any]:
        charts: dict[str, Any] = {}
        for header, values, summary in zip(
            headers,
            columns_data,
            summaries,
            strict=True,
        ):
            if summary.inferred_type in {"integer", "float"}:
                numbers = [
                    number
                    for value in values
                    if (number := coerce_float(value)) is not None
                ]
                if numbers:
                    charts[header] = {
                        "type": "histogram",
                        "bins": self._histogram_bins(numbers),
                    }
            elif summary.categorical_stats is not None:
                charts[header] = {
                    "type": "bar",
                    "values": [
                        {"value": item.value, "count": item.count}
                        for item in summary.categorical_stats.top_values
                    ],
                }
        return charts

    def _histogram_bins(
        self,
        numbers: list[float],
        *,
        bins: int = 8,
    ) -> list[dict[str, float | int]]:
        minimum = min(numbers)
        maximum = max(numbers)
        if minimum == maximum:
            return [{"start": minimum, "end": maximum, "count": len(numbers)}]

        width = (maximum - minimum) / bins
        counts = [0] * bins
        for number in numbers:
            index = min(int((number - minimum) / width), bins - 1)
            counts[index] += 1

        return [
            {
                "start": round(minimum + index * width, 4),
                "end": round(minimum + (index + 1) * width, 4),
                "count": count,
            }
            for index, count in enumerate(counts)
        ]

    def _dataset_charts(
        self,
        headers: list[str],
        columns_data: list[list[str]],
        summaries: list[ColumnSummary],
    ) -> dict[str, Any]:
        """Build scatter, line, and correlation charts for the dataset."""
        charts: dict[str, Any] = {}
        correlation = self._correlation_heatmap(headers, columns_data, summaries)
        if correlation is not None:
            charts["correlation"] = correlation
        scatter = self._scatter_plots(headers, columns_data, summaries)
        if scatter:
            charts["scatter"] = scatter
        line = self._line_charts(headers, columns_data, summaries)
        if line:
            charts["line"] = line
        return charts

    def _correlation_heatmap(
        self,
        headers: list[str],
        columns_data: list[list[str]],
        summaries: list[ColumnSummary],
    ) -> dict[str, Any] | None:
        numeric_columns = [
            (header, index)
            for header, index, summary in zip(
                headers, range(len(headers)), summaries, strict=True
            )
            if summary.inferred_type in {"integer", "float"}
        ]
        if len(numeric_columns) < 2:
            return None

        labels = [header for header, _ in numeric_columns]
        matrix_values: list[list[float]] = []
        for _, index in numeric_columns:
            values = [
                number
                for value in columns_data[index]
                if (number := coerce_float(value)) is not None
            ]
            matrix_values.append(values)

        min_len = min(len(values) for values in matrix_values)
        if min_len < 2:
            return None

        array = np.array([values[:min_len] for values in matrix_values], dtype=float)
        corr = np.corrcoef(array)
        return {
            "type": "correlation",
            "labels": labels,
            "matrix": [[round(float(value), 4) for value in row] for row in corr],
        }

    def _scatter_plots(
        self,
        headers: list[str],
        columns_data: list[list[str]],
        summaries: list[ColumnSummary],
    ) -> list[dict[str, Any]]:
        numeric_columns = [
            (header, index)
            for header, index, summary in zip(
                headers, range(len(headers)), summaries, strict=True
            )
            if summary.inferred_type in {"integer", "float"}
        ]
        plots: list[dict[str, Any]] = []
        max_points = 200
        for left_index in range(min(len(numeric_columns), 3)):
            for right_index in range(left_index + 1, min(len(numeric_columns), 4)):
                x_header, x_index = numeric_columns[left_index]
                y_header, y_index = numeric_columns[right_index]
                points: list[dict[str, float]] = []
                for row_index in range(len(columns_data[0])):
                    x_value = coerce_float(columns_data[x_index][row_index])
                    y_value = coerce_float(columns_data[y_index][row_index])
                    if x_value is None or y_value is None:
                        continue
                    points.append({"x": float(x_value), "y": float(y_value)})
                    if len(points) >= max_points:
                        break
                if len(points) >= 2:
                    plots.append(
                        {
                            "type": "scatter",
                            "x_column": x_header,
                            "y_column": y_header,
                            "points": points,
                        }
                    )
                if len(plots) >= 3:
                    return plots
        return plots

    def _line_charts(
        self,
        headers: list[str],
        columns_data: list[list[str]],
        summaries: list[ColumnSummary],
    ) -> list[dict[str, Any]]:
        from app.utils.type_utils import parse_datetime_value

        date_columns = [
            (header, index)
            for header, index, summary in zip(
                headers, range(len(headers)), summaries, strict=True
            )
            if summary.inferred_type == "datetime"
        ]
        numeric_columns = [
            (header, index)
            for header, index, summary in zip(
                headers, range(len(headers)), summaries, strict=True
            )
            if summary.inferred_type in {"integer", "float"}
        ]
        if not date_columns or not numeric_columns:
            return []

        charts: list[dict[str, Any]] = []
        date_header, date_index = date_columns[0]
        for value_header, value_index in numeric_columns[:2]:
            series: dict[str, float] = {}
            for row_index in range(len(columns_data[0])):
                label = parse_datetime_value(columns_data[date_index][row_index])
                value = coerce_float(columns_data[value_index][row_index])
                if label is None or value is None:
                    continue
                key = label.strftime("%Y-%m-%d")
                series[key] = series.get(key, 0.0) + float(value)
            if len(series) >= 2:
                points = [
                    {"x": label, "y": round(amount, 4)}
                    for label, amount in sorted(series.items())
                ][:200]
                charts.append(
                    {
                        "type": "line",
                        "x_column": date_header,
                        "y_column": value_header,
                        "points": points,
                    }
                )
        return charts


eda_service = EDAService()
