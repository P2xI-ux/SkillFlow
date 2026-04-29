"""add question payload, test metadata, and telegram link ttl

Revision ID: 20260429_01
Revises:
Create Date: 2026-04-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE questiontype ADD VALUE IF NOT EXISTS 'TEXT_ANSWER'")
        op.execute("ALTER TYPE questiontype ADD VALUE IF NOT EXISTS 'MATCHING'")

    op.add_column("users", sa.Column("telegram_link_code_created_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("telegram_link_code_expires_at", sa.DateTime(), nullable=True))
    op.add_column("tests", sa.Column("question_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tests", sa.Column("max_score", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tests", sa.Column("created_by_role", sa.String(length=32), nullable=True))
    op.add_column("questions", sa.Column("payload", sa.Text(), nullable=True))
    op.add_column("user_answers", sa.Column("answer_payload", sa.Text(), nullable=True))


def downgrade():
    # PostgreSQL enum values are intentionally left in place; removing enum labels
    # safely requires recreating the type and all dependent columns.
    op.drop_column("user_answers", "answer_payload")
    op.drop_column("questions", "payload")
    op.drop_column("tests", "created_by_role")
    op.drop_column("tests", "max_score")
    op.drop_column("tests", "question_count")
    op.drop_column("users", "telegram_link_code_expires_at")
    op.drop_column("users", "telegram_link_code_created_at")
