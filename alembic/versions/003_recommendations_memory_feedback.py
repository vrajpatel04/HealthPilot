"""Recommendations, user memories, feedback

Revision ID: 003
Revises: 002
Create Date: 2026-08-09
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

feedback_action = postgresql.ENUM(
    "displayed", "clicked", "saved", "ignored", "started", "completed",
    name="feedback_action",
    create_type=False,
)


def upgrade() -> None:
    feedback_action.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "user_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("primary_interest", sa.String(length=255), nullable=True),
        sa.Column("secondary_interest", sa.String(length=255), nullable=True),
        sa.Column("preferences", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("successful_recommendations", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_memories_session_id", "user_memories", ["session_id"])

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("primary_product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("secondary_product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("product_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False, server_default="0.50"),
        sa.Column("behavior_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("behavior_summary", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("why_recommended", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_recommendations_session_id", "recommendations", ["session_id"])
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])

    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recommendations.id"), nullable=False),
        sa.Column("action", feedback_action, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_index("ix_recommendations_user_id", table_name="recommendations")
    op.drop_index("ix_recommendations_session_id", table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_index("ix_user_memories_session_id", table_name="user_memories")
    op.drop_table("user_memories")
    feedback_action.drop(op.get_bind(), checkfirst=True)
