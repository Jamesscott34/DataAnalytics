"""SQL analysis request and response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SQLImportRequest(BaseModel):
    """Request body for importing CSV rows into SQL tables."""

    max_rows: int | None = Field(default=None, ge=1)


class SQLQueryRequest(BaseModel):
    """Read-only SQL query request."""

    query: str = Field(min_length=1)
    params: dict[str, Any] | None = None


class SQLQueryResponse(BaseModel):
    """Tabular SQL query result."""

    columns: list[str]
    rows: list[list[Any]]
    row_count: int


class SQLImportResponse(BaseModel):
    """Response after importing CSV rows for SQL analysis."""

    imported_rows: int
    table_name: str
    columns: list[str]


class SQLGroupTableSchema(BaseModel):
    """Imported table schema within a dataset group."""

    file_id: int
    table_alias: str
    original_filename: str
    table_name: str
    columns: list[str]
    imported_rows: int


class SQLGroupImportResponse(BaseModel):
    """Headers-only import result for a dataset group."""

    group_id: int
    group_name: str
    tables: list[SQLGroupTableSchema]


class SQLPreset(BaseModel):
    """Built-in SQL preset definition."""

    id: str
    name: str
    description: str
    sql: str


class SQLPresetListResponse(BaseModel):
    """List of available SQL presets for a file."""

    presets: list[SQLPreset]
