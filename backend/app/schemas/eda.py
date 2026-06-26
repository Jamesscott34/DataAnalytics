"""EDA request and response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EDARequest(BaseModel):
    """Request body for running EDA on a file."""

    force_refresh: bool = False


class NumericStats(BaseModel):
    """Descriptive statistics for numeric columns."""

    min: float | None = None
    max: float | None = None
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    q25: float | None = None
    q75: float | None = None


class TopValue(BaseModel):
    """A frequent categorical value."""

    value: str
    count: int


class CategoricalStats(BaseModel):
    """Summary statistics for categorical columns."""

    unique_count: int
    top_values: list[TopValue]


class ColumnSummary(BaseModel):
    """Per-column EDA summary."""

    name: str
    inferred_type: str
    missing_count: int
    missing_percent: float
    unique_count: int
    sample_values: list[str]
    numeric_stats: NumericStats | None = None
    categorical_stats: CategoricalStats | None = None


class EDASummary(BaseModel):
    """Dataset-level EDA summary."""

    row_count: int
    column_count: int
    duplicate_row_count: int
    missing_cells: int
    missing_percent: float
    file_hash: str = Field(min_length=64, max_length=64)


class EDAResponse(BaseModel):
    """Full EDA response for a dataset."""

    summary: EDASummary
    columns: list[ColumnSummary]
    quality_warnings: list[str]
    chart_data: dict[str, Any]
    cached: bool = False
    analyzed_at: datetime


class EDASuggestions(BaseModel):
    """Suggested columns and analyses derived from EDA."""

    target_columns: list[str]
    feature_columns: list[str]
    date_columns: list[str]
    suggested_analyses: list[str]
