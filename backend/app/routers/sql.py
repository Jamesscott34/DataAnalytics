"""SQL analysis API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.sql import (
    SQLGroupImportResponse,
    SQLImportRequest,
    SQLImportResponse,
    SQLPresetListResponse,
    SQLQueryRequest,
    SQLQueryResponse,
)
from app.services.dataset_group_service import DatasetGroupError, dataset_group_service
from app.services.sql_analysis_service import SQLAnalysisError, sql_analysis_service

router = APIRouter(prefix="/sql", tags=["sql"])


@router.post(
    "/groups/{group_id}/import",
    response_model=SQLGroupImportResponse,
    summary="Import all files in a dataset group",
)
def import_group_tables(
    group_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> SQLGroupImportResponse:
    """Import every CSV in a group and return column headers only."""
    try:
        group = dataset_group_service.ensure_group_access(
            db,
            group_id=group_id,
            user=current_user,
        )
        if not group.members:
            raise SQLAnalysisError("Group has no files to import")
        return sql_analysis_service.import_group(
            db,
            group_id=group.id,
            members=group.members,
            group_name=group.name,
        )
    except (SQLAnalysisError, DatasetGroupError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/groups/{group_id}/query",
    response_model=SQLQueryResponse,
    summary="Run SQL against a dataset group",
)
def run_group_sql_query(
    group_id: int,
    request: SQLQueryRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> SQLQueryResponse:
    """Execute read-only SQL across tables in a dataset group."""
    try:
        group = dataset_group_service.ensure_group_access(
            db,
            group_id=group_id,
            user=current_user,
        )
        table_names = [
            sql_analysis_service.table_name_for_file(member.file_id)
            for member in group.members
        ]
        if not table_names:
            raise SQLAnalysisError("Group has no imported tables")
        return sql_analysis_service.run_group_query(
            db,
            table_names=table_names,
            query=request.query,
            params=request.params,
        )
    except (SQLAnalysisError, DatasetGroupError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/groups/{group_id}/presets",
    response_model=SQLPresetListResponse,
    summary="List SQL presets for a dataset group",
)
def list_group_sql_presets(
    group_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer)],
) -> SQLPresetListResponse:
    """Return SQL presets for all tables in a group."""
    try:
        group = dataset_group_service.ensure_group_access(
            db,
            group_id=group_id,
            user=current_user,
        )
        tables = []
        for member in group.members:
            schema = sql_analysis_service.get_import_schema(db, file_id=member.file_id)
            if schema is None:
                continue
            columns, _ = schema
            tables.append(
                (
                    member.table_alias,
                    sql_analysis_service.table_name_for_file(member.file_id),
                    columns,
                ),
            )
        presets = sql_analysis_service.list_group_presets(tables=tables)
        return SQLPresetListResponse(presets=presets)
    except DatasetGroupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{file_id}/import",
    response_model=SQLImportResponse,
    summary="Import CSV rows for SQL analysis",
)
def import_csv_rows(
    file_id: int,
    request: SQLImportRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> SQLImportResponse:
    """Import stored CSV rows into a queryable SQLite table."""
    try:
        return sql_analysis_service.import_rows(
            db,
            file_id=file_id,
            max_rows=request.max_rows,
        )
    except SQLAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/{file_id}/query",
    response_model=SQLQueryResponse,
    summary="Run a read-only SQL query",
)
def run_sql_query(
    file_id: int,
    request: SQLQueryRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> SQLQueryResponse:
    """Execute a validated read-only SQL query against imported rows."""
    try:
        return sql_analysis_service.run_query(
            db,
            file_id=file_id,
            query=request.query,
            params=request.params,
        )
    except SQLAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{file_id}/presets",
    response_model=SQLPresetListResponse,
    summary="List SQL presets for a file",
)
def list_sql_presets(
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_viewer)],
) -> SQLPresetListResponse:
    """Return built-in SQL presets for an imported file."""
    try:
        presets = sql_analysis_service.list_presets(db, file_id=file_id)
    except SQLAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return SQLPresetListResponse(presets=presets)


@router.post(
    "/{file_id}/presets/{preset_id}/run",
    response_model=SQLQueryResponse,
    summary="Run a built-in SQL preset",
)
def run_sql_preset(
    file_id: int,
    preset_id: str,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_analyst)],
) -> SQLQueryResponse:
    """Execute a built-in SQL preset against imported rows."""
    try:
        return sql_analysis_service.run_preset(
            db,
            file_id=file_id,
            preset_id=preset_id,
        )
    except SQLAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
