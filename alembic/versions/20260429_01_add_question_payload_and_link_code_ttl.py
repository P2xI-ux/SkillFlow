"""baseline schema plus question payload and telegram link ttl

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


role_enum = sa.Enum("STUDENT", "TEACHER", name="role")
test_status_enum = sa.Enum("DRAFT", "PENDING_MODERATION", "PUBLISHED", "ARCHIVED", name="teststatus")
question_type_enum = sa.Enum("SINGLE_CHOICE", "MULTIPLE_CHOICE", "TEXT_ANSWER", "MATCHING", name="questiontype")
attempt_status_enum = sa.Enum("IN_PROGRESS", "COMPLETED", name="attemptstatus")


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE questiontype ADD VALUE IF NOT EXISTS 'TEXT_ANSWER'")
        op.execute("ALTER TYPE questiontype ADD VALUE IF NOT EXISTS 'MATCHING'")

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("full_name", sa.String(length=120), nullable=False),
            sa.Column("role", role_enum, nullable=False),
            sa.Column("faculty", sa.String(length=120), nullable=True),
            sa.Column("study_group", sa.String(length=120), nullable=True),
            sa.Column("course", sa.Integer(), nullable=True),
            sa.Column("department", sa.String(length=120), nullable=True),
            sa.Column("program_code", sa.String(length=32), nullable=True),
            sa.Column("telegram_id", sa.String(length=64), nullable=True),
            sa.Column("telegram_link_code", sa.String(length=6), nullable=True),
            sa.Column("telegram_link_code_created_at", sa.DateTime(), nullable=True),
            sa.Column("telegram_link_code_expires_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("email"),
            sa.UniqueConstraint("telegram_id"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)
    else:
        _add_column_if_missing("users", "telegram_link_code_created_at", sa.Column("telegram_link_code_created_at", sa.DateTime(), nullable=True))
        _add_column_if_missing("users", "telegram_link_code_expires_at", sa.Column("telegram_link_code_expires_at", sa.DateTime(), nullable=True))

    if "subjects" not in existing_tables:
        op.create_table(
            "subjects",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("code", sa.String(length=40), nullable=False),
            sa.UniqueConstraint("name"),
            sa.UniqueConstraint("code"),
        )

    if "teacher_subjects" not in existing_tables:
        op.create_table(
            "teacher_subjects",
            sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
            sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id"), primary_key=True),
        )

    if "tests" not in existing_tables:
        op.create_table(
            "tests",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("difficulty", sa.Integer(), nullable=False),
            sa.Column("question_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("created_by_role", sa.String(length=32), nullable=True),
            sa.Column("status", test_status_enum, nullable=False),
            sa.Column("moderation_comment", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("published_at", sa.DateTime(), nullable=True),
            sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id"), nullable=False),
            sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("moderator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        )
    else:
        _add_column_if_missing("tests", "question_count", sa.Column("question_count", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing("tests", "max_score", sa.Column("max_score", sa.Float(), nullable=False, server_default="0"))
        _add_column_if_missing("tests", "created_by_role", sa.Column("created_by_role", sa.String(length=32), nullable=True))

    if "questions" not in existing_tables:
        op.create_table(
            "questions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("points", sa.Float(), nullable=False),
            sa.Column("question_type", question_type_enum, nullable=False),
            sa.Column("payload", sa.Text(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("test_id", sa.Integer(), sa.ForeignKey("tests.id"), nullable=False),
        )
    else:
        _add_column_if_missing("questions", "payload", sa.Column("payload", sa.Text(), nullable=True))

    if "answer_options" not in existing_tables:
        op.create_table(
            "answer_options",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("is_correct", sa.Boolean(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        )

    if "test_attempts" not in existing_tables:
        op.create_table(
            "test_attempts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("max_score", sa.Float(), nullable=False),
            sa.Column("rating_delta", sa.Float(), nullable=False),
            sa.Column("status", attempt_status_enum, nullable=False),
            sa.Column("test_id", sa.Integer(), sa.ForeignKey("tests.id"), nullable=False),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        )

    if "user_answers" not in existing_tables:
        op.create_table(
            "user_answers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("selected_option_ids", sa.Text(), nullable=True),
            sa.Column("answer_payload", sa.Text(), nullable=True),
            sa.Column("is_correct", sa.Boolean(), nullable=False),
            sa.Column("points_earned", sa.Float(), nullable=False),
            sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("test_attempts.id"), nullable=False),
            sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id"), nullable=False),
        )
    else:
        _add_column_if_missing("user_answers", "answer_payload", sa.Column("answer_payload", sa.Text(), nullable=True))

    if "ratings" not in existing_tables:
        op.create_table(
            "ratings",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("total_score", sa.Float(), nullable=False),
            sa.Column("position", sa.Integer(), nullable=True),
            sa.Column("last_updated", sa.DateTime(), nullable=True),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id"), nullable=False),
            sa.UniqueConstraint("student_id", "subject_id", name="uq_rating_student_subject"),
        )

    if "achievements" not in existing_tables:
        op.create_table(
            "achievements",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.UniqueConstraint("code"),
        )

    if "user_achievements" not in existing_tables:
        op.create_table(
            "user_achievements",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("earned_at", sa.DateTime(), nullable=True),
            sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("achievement_id", sa.Integer(), sa.ForeignKey("achievements.id"), nullable=False),
            sa.UniqueConstraint("student_id", "achievement_id", name="uq_user_achievement"),
        )


def downgrade():
    for table_name in [
        "user_achievements",
        "achievements",
        "ratings",
        "user_answers",
        "test_attempts",
        "answer_options",
        "questions",
        "tests",
        "teacher_subjects",
        "subjects",
        "users",
    ]:
        op.drop_table(table_name)


def _add_column_if_missing(table_name: str, column_name: str, column):
    bind = op.get_bind()
    columns = {item["name"] for item in sa.inspect(bind).get_columns(table_name)}
    if column_name not in columns:
        op.add_column(table_name, column)
