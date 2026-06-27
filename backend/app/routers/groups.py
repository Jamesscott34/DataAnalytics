"""Dataset group API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_analyst, require_viewer
from app.database import get_db
from app.models.user import User
from app.schemas.group import (
    AddGroupMemberRequest,
    CreateGroupRequest,
    GroupListResponse,
    GroupResponse,
)
from app.services.dataset_group_service import DatasetGroupError, dataset_group_service

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post(
    "",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a dataset group",
)
def create_group(
    request: CreateGroupRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> GroupResponse:
    """Group multiple CSV files for multi-table SQL."""
    try:
        return dataset_group_service.create_group(
            db,
            owner_id=current_user.id,
            request=request,
        )
    except DatasetGroupError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=GroupListResponse,
    summary="List dataset groups",
)
def list_groups(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer)],
) -> GroupListResponse:
    """Return dataset groups for the current user."""
    return dataset_group_service.list_groups(db, user=current_user)


@router.get(
    "/{group_id}",
    response_model=GroupResponse,
    summary="Get a dataset group",
)
def get_group(
    group_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer)],
) -> GroupResponse:
    """Return one dataset group with member files."""
    try:
        return dataset_group_service.get_group(
            db,
            group_id=group_id,
            user=current_user,
        )
    except DatasetGroupError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if str(exc) == "Group not found"
            else status.HTTP_403_FORBIDDEN
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post(
    "/{group_id}/members",
    response_model=GroupResponse,
    summary="Add a file to a group",
)
def add_group_member(
    group_id: int,
    request: AddGroupMemberRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> GroupResponse:
    """Add an uploaded CSV to a dataset group."""
    try:
        return dataset_group_service.add_member(
            db,
            group_id=group_id,
            user=current_user,
            file_id=request.file_id,
            table_alias=request.table_alias,
        )
    except DatasetGroupError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{group_id}/members/{file_id}",
    response_model=GroupResponse,
    summary="Remove a file from a group",
)
def remove_group_member(
    group_id: int,
    file_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst)],
) -> GroupResponse:
    """Remove a file from a dataset group."""
    try:
        return dataset_group_service.remove_member(
            db,
            group_id=group_id,
            file_id=file_id,
            user=current_user,
        )
    except DatasetGroupError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
