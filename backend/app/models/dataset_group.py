"""Dataset group ORM models.

Lets analysts group multiple uploaded CSV files for multi-table SQL.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.uploaded_file import UploadedFile
    from app.models.user import User


class DatasetGroup(Base):
    """Named collection of related CSV datasets."""

    __tablename__ = "dataset_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    owner: Mapped["User"] = relationship("User")
    members: Mapped[list["DatasetGroupMember"]] = relationship(
        "DatasetGroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="DatasetGroupMember.id",
    )


class DatasetGroupMember(Base):
    """Uploaded file membership in a dataset group."""

    __tablename__ = "dataset_group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "file_id", name="uq_group_file"),
        UniqueConstraint("group_id", "table_alias", name="uq_group_alias"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_id: Mapped[int] = mapped_column(
        ForeignKey("uploaded_files.id", ondelete="CASCADE"),
        nullable=False,
    )
    table_alias: Mapped[str] = mapped_column(String(64), nullable=False)

    group: Mapped["DatasetGroup"] = relationship(
        "DatasetGroup",
        back_populates="members",
    )
    file: Mapped["UploadedFile"] = relationship("UploadedFile")
