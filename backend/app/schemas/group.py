"""Dataset group request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class GroupMemberInput(BaseModel):
    """File to add when creating a group."""

    file_id: int
    table_alias: str | None = None


class CreateGroupRequest(BaseModel):
    """Create a dataset group."""

    name: str = Field(min_length=1, max_length=128)
    members: list[GroupMemberInput] = Field(default_factory=list)


class AddGroupMemberRequest(BaseModel):
    """Add a file to an existing group."""

    file_id: int
    table_alias: str | None = None


class GroupMemberResponse(BaseModel):
    """File membership in a dataset group."""

    file_id: int
    table_alias: str
    original_filename: str
    table_name: str
    columns: list[str] = Field(default_factory=list)
    imported_rows: int | None = None


class GroupResponse(BaseModel):
    """Dataset group with member files."""

    id: int
    name: str
    created_at: datetime
    members: list[GroupMemberResponse]


class GroupListResponse(BaseModel):
    """List of dataset groups."""

    items: list[GroupResponse]
    total: int
