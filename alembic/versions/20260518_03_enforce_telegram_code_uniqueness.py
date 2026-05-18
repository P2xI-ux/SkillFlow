"""enforce unique telegram link codes

Revision ID: 20260518_03
Revises: 20260517_02
Create Date: 2026-05-18
"""

from alembic import op


revision = "20260518_03"
down_revision = "20260517_02"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.drop_index("ix_users_telegram_link_code", table_name="users")
        op.create_index(
            "ix_users_telegram_link_code",
            "users",
            ["telegram_link_code"],
            unique=True,
        )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.drop_index("ix_users_telegram_link_code", table_name="users")
        op.create_index(
            "ix_users_telegram_link_code",
            "users",
            ["telegram_link_code"],
            unique=False,
        )
