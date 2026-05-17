"""add integrity indexes for telegram link code and attempts

Revision ID: 20260517_02
Revises: 20260429_01
Create Date: 2026-05-17
"""

from alembic import op
import sqlalchemy as sa


revision = "20260517_02"
down_revision = "20260429_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_users_telegram_link_code", "users", ["telegram_link_code"], unique=False)
    op.create_index("ix_test_attempts_student_test_completed", "test_attempts", ["student_id", "test_id", "status"], unique=False)


def downgrade():
    op.drop_index("ix_test_attempts_student_test_completed", table_name="test_attempts")
    op.drop_index("ix_users_telegram_link_code", table_name="users")
