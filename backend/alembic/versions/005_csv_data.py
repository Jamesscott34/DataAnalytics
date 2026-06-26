"""Add csv_data table.

Revision ID: 005_csv_data
Revises: 004_file_versions
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_csv_data"
down_revision: str | None = "004_file_versions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create csv_data table for SQL analysis imports."""
    op.create_table(
        "csv_data",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_csv_data_file_id", "csv_data", ["file_id"], unique=False)


def downgrade() -> None:
    """Drop csv_data table."""
    op.drop_index("ix_csv_data_file_id", table_name="csv_data")
    op.drop_table("csv_data")
