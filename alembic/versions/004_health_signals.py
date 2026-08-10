"""Health signals: lifestyle logs, health profiles, blood reports

Revision ID: 004
Revises: 003
Create Date: 2026-08-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

blood_report_status = postgresql.ENUM(
    "pending",
    "processing",
    "completed",
    "failed",
    name="blood_report_status",
    create_type=False,
)


def upgrade() -> None:
    blood_report_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "lifestyle_daily_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("responses", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "log_date"),
    )

    op.create_table(
        "health_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sleep_average", sa.Numeric(4, 1), nullable=True),
        sa.Column("water_average", sa.Numeric(4, 1), nullable=True),
        sa.Column("activity_average", sa.Numeric(3, 2), nullable=True),
        sa.Column("screen_time_average", sa.Numeric(4, 1), nullable=True),
        sa.Column("mood_average", sa.Numeric(3, 2), nullable=True),
        sa.Column("stress_average", sa.Numeric(3, 2), nullable=True),
        sa.Column("energy_average", sa.Numeric(3, 2), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "blood_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("status", blood_report_status, nullable=False),
        sa.Column("extracted_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "upload_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("blood_reports")
    op.drop_table("health_profiles")
    op.drop_table("lifestyle_daily_logs")
    blood_report_status.drop(op.get_bind(), checkfirst=True)
