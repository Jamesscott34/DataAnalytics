"""Add security scans table.

Revision ID: 002_security_scans
Revises: 001_initial
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_security_scans"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create security_scans table."""
    scan_status = sa.Enum("safe", "warning", "blocked", name="scanstatus")
    scan_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "security_scans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("status", scan_status, nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("issues", sa.JSON(), nullable=False),
        sa.Column("recommended_action", sa.String(length=512), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "scanned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop security_scans table."""
    op.drop_table("security_scans")
    sa.Enum(name="scanstatus").drop(op.get_bind(), checkfirst=True)
