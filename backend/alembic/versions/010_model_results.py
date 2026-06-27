"""Add model_results table for SQL persistence of analysis outputs."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010_model_results"
down_revision: str | None = "009_analysis_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create model_results table."""
    op.create_table(
        "model_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("result_id", sa.String(length=64), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=True),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("result_type", sa.String(length=64), nullable=False),
        sa.Column("algorithm", sa.String(length=64), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("explainability", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["file_id"], ["uploaded_files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
        sa.UniqueConstraint("result_id"),
    )
    op.create_index("ix_model_results_file_id", "model_results", ["file_id"])
    op.create_index("ix_model_results_result_id", "model_results", ["result_id"])


def downgrade() -> None:
    """Drop model_results table."""
    op.drop_index("ix_model_results_result_id", table_name="model_results")
    op.drop_index("ix_model_results_file_id", table_name="model_results")
    op.drop_table("model_results")
