"""Dataset group management service."""

import re

from sqlalchemy.orm import Session, joinedload

from app.models.dataset_group import DatasetGroup, DatasetGroupMember
from app.models.uploaded_file import UploadedFile
from app.models.user import User, UserRole
from app.schemas.group import (
    CreateGroupRequest,
    GroupListResponse,
    GroupMemberResponse,
    GroupResponse,
)
from app.services.sql_analysis_service import sql_analysis_service

ALIAS_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class DatasetGroupError(ValueError):
    """Raised when group operations fail."""


class DatasetGroupService:
    """CRUD for dataset groups that combine multiple CSV files."""

    def create_group(
        self,
        db: Session,
        *,
        owner_id: int,
        request: CreateGroupRequest,
    ) -> GroupResponse:
        """Create a group and optionally add initial members."""
        group = DatasetGroup(owner_id=owner_id, name=request.name.strip())
        db.add(group)
        db.flush()

        used_aliases: set[str] = set()
        for member_input in request.members:
            self._add_member(
                db,
                group=group,
                file_id=member_input.file_id,
                table_alias=member_input.table_alias,
                used_aliases=used_aliases,
            )

        db.commit()
        return self.get_group(db, group_id=group.id, user_id=owner_id)

    def list_groups(self, db: Session, *, user: User) -> GroupListResponse:
        """List groups visible to the user."""
        query = db.query(DatasetGroup).options(
            joinedload(DatasetGroup.members).joinedload(DatasetGroupMember.file),
        )
        if user.role != UserRole.ADMIN:
            query = query.filter(DatasetGroup.owner_id == user.id)
        groups = query.order_by(DatasetGroup.created_at.desc()).all()
        items = [self._to_response(db, group) for group in groups]
        return GroupListResponse(items=items, total=len(items))

    def get_group(
        self,
        db: Session,
        *,
        group_id: int,
        user: User | None = None,
        user_id: int | None = None,
    ) -> GroupResponse:
        """Return one group if the user may access it."""
        group = self._get_group_or_raise(db, group_id=group_id)
        if user is not None:
            self._ensure_access(group, user)
        elif user_id is not None and group.owner_id != user_id:
            raise DatasetGroupError("You do not have permission to access this group")
        return self._to_response(db, group)

    def ensure_group_access(
        self,
        db: Session,
        *,
        group_id: int,
        user: User,
    ) -> DatasetGroup:
        """Load a group after verifying the user may access it."""
        group = self._get_group_or_raise(db, group_id=group_id)
        self._ensure_access(group, user)
        return group

    def get_group_entity(self, db: Session, *, group_id: int) -> DatasetGroup:
        """Load a group with members for SQL operations."""
        return self._get_group_or_raise(db, group_id=group_id)

    def add_member(
        self,
        db: Session,
        *,
        group_id: int,
        user: User,
        file_id: int,
        table_alias: str | None = None,
    ) -> GroupResponse:
        """Add an uploaded file to a group."""
        group = self._get_group_or_raise(db, group_id=group_id)
        self._ensure_access(group, user)
        used_aliases = {member.table_alias for member in group.members}
        self._add_member(
            db,
            group=group,
            file_id=file_id,
            table_alias=table_alias,
            used_aliases=used_aliases,
        )
        db.commit()
        return self.get_group(db, group_id=group_id, user=user)

    def remove_member(
        self,
        db: Session,
        *,
        group_id: int,
        file_id: int,
        user: User,
    ) -> GroupResponse:
        """Remove a file from a group."""
        group = self._get_group_or_raise(db, group_id=group_id)
        self._ensure_access(group, user)
        member = (
            db.query(DatasetGroupMember)
            .filter(
                DatasetGroupMember.group_id == group_id,
                DatasetGroupMember.file_id == file_id,
            )
            .first()
        )
        if member is None:
            raise DatasetGroupError("File is not in this group")
        db.delete(member)
        db.commit()
        return self.get_group(db, group_id=group_id, user=user)

    def _get_group_or_raise(self, db: Session, *, group_id: int) -> DatasetGroup:
        group = (
            db.query(DatasetGroup)
            .options(
                joinedload(DatasetGroup.members).joinedload(DatasetGroupMember.file),
            )
            .filter(DatasetGroup.id == group_id)
            .first()
        )
        if group is None:
            raise DatasetGroupError("Group not found")
        return group

    def _ensure_access(self, group: DatasetGroup, user: User) -> None:
        if user.role != UserRole.ADMIN and group.owner_id != user.id:
            raise DatasetGroupError("You do not have permission to access this group")

    def _add_member(
        self,
        db: Session,
        *,
        group: DatasetGroup,
        file_id: int,
        table_alias: str | None,
        used_aliases: set[str],
    ) -> DatasetGroupMember:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file is None:
            raise DatasetGroupError(f"File not found: {file_id}")

        alias = self._resolve_alias(
            requested=table_alias,
            filename=file.original_filename,
            used_aliases=used_aliases,
        )
        member = DatasetGroupMember(
            group_id=group.id,
            file_id=file_id,
            table_alias=alias,
        )
        db.add(member)
        used_aliases.add(alias)
        return member

    def _resolve_alias(
        self,
        *,
        requested: str | None,
        filename: str,
        used_aliases: set[str],
    ) -> str:
        base = requested or sql_analysis_service.alias_from_filename(filename)
        alias = base
        counter = 2
        while alias in used_aliases:
            alias = f"{base}_{counter}"
            counter += 1
        if not ALIAS_PATTERN.match(alias):
            raise DatasetGroupError(f"Invalid table alias: {alias}")
        return alias

    def _to_response(self, db: Session, group: DatasetGroup) -> GroupResponse:
        members: list[GroupMemberResponse] = []
        for member in group.members:
            schema = sql_analysis_service.get_import_schema(db, file_id=member.file_id)
            members.append(
                GroupMemberResponse(
                    file_id=member.file_id,
                    table_alias=member.table_alias,
                    original_filename=member.file.original_filename,
                    table_name=sql_analysis_service.table_name_for_file(member.file_id),
                    columns=schema[0] if schema else [],
                    imported_rows=schema[1] if schema else None,
                ),
            )
        return GroupResponse(
            id=group.id,
            name=group.name,
            created_at=group.created_at,
            members=members,
        )


dataset_group_service = DatasetGroupService()
