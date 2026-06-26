"""Add dataset_groups tables.

Revision ID: 007_dataset_groups
Revises: 006_fix_csv_data_id
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007_dataset_groups"
down_revision: str | None = "006_fix_csv_data_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create dataset group tables."""
    op.create_table(
        "dataset_groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "dataset_group_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("table_alias", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["dataset_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "file_id", name="uq_group_file"),
        sa.UniqueConstraint("group_id", "table_alias", name="uq_group_alias"),
    )


def downgrade() -> None:
    """Drop dataset group tables."""
    op.drop_table("dataset_group_members")
    op.drop_table("dataset_groups")
