"""Add generated insights table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008_generated_insights"
down_revision: str | None = "007_dataset_groups"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create generated_insights table."""
    op.create_table(
        "generated_insights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("result_id", sa.String(length=64), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=True),
        sa.Column("analysis_type", sa.String(length=64), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generated_insights_result_id", "generated_insights", ["result_id"])
    op.create_index("ix_generated_insights_job_id", "generated_insights", ["job_id"])


def downgrade() -> None:
    """Drop generated_insights table."""
    op.drop_index("ix_generated_insights_job_id", table_name="generated_insights")
    op.drop_index("ix_generated_insights_result_id", table_name="generated_insights")
    op.drop_table("generated_insights")
