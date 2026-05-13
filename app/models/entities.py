from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AttemptStatus, QuestionType, Role, TestStatus

teacher_subjects = Table(
    "teacher_subjects",
    Base.metadata,
    Column("teacher_id", ForeignKey("users.id"), primary_key=True),
    Column("subject_id", ForeignKey("subjects.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.STUDENT)
    faculty: Mapped[str] = mapped_column(String(120), nullable=True)
    study_group: Mapped[str] = mapped_column(String(120), nullable=True)
    course: Mapped[int] = mapped_column(Integer, nullable=True)
    department: Mapped[str] = mapped_column(String(120), nullable=True)
    program_code: Mapped[str] = mapped_column(String(32), nullable=True)
    telegram_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
    telegram_link_code: Mapped[str] = mapped_column(String(6), nullable=True)
    telegram_link_code_created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True
    )
    telegram_link_code_expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tests = relationship("Test", back_populates="author", foreign_keys="Test.author_id")
    moderated_tests = relationship(
        "Test", back_populates="moderator", foreign_keys="Test.moderator_id"
    )
    attempts = relationship("TestAttempt", back_populates="student")
    ratings = relationship("Rating", back_populates="student")
    earned_achievements = relationship("UserAchievement", back_populates="student")
    teaching_subjects = relationship(
        "Subject", secondary=teacher_subjects, back_populates="teachers"
    )


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)

    tests = relationship("Test", back_populates="subject")
    ratings = relationship("Rating", back_populates="subject")
    teachers = relationship(
        "User", secondary=teacher_subjects, back_populates="teaching_subjects"
    )


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_by_role: Mapped[str] = mapped_column(String(32), nullable=True)
    status: Mapped[TestStatus] = mapped_column(
        Enum(TestStatus), default=TestStatus.DRAFT
    )
    moderation_comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    moderator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

    author = relationship("User", back_populates="tests", foreign_keys=[author_id])
    moderator = relationship(
        "User", back_populates="moderated_tests", foreign_keys=[moderator_id]
    )
    subject = relationship("Subject", back_populates="tests")
    questions = relationship(
        "Question", back_populates="test", cascade="all, delete-orphan"
    )
    attempts = relationship("TestAttempt", back_populates="test")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    points: Mapped[float] = mapped_column(Float, default=1.0)
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType))
    payload: Mapped[str] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))

    test = relationship("Test", back_populates="questions")
    answer_options = relationship(
        "AnswerOption", back_populates="question", cascade="all, delete-orphan"
    )
    answers = relationship("UserAnswer", back_populates="question")


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))

    question = relationship("Question", back_populates="answer_options")


class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, default=0.0)
    rating_delta: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus), default=AttemptStatus.IN_PROGRESS
    )
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    test = relationship("Test", back_populates="attempts")
    student = relationship("User", back_populates="attempts")
    answers = relationship(
        "UserAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    selected_option_ids: Mapped[str] = mapped_column(Text, default="")
    answer_payload: Mapped[str] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    points_earned: Mapped[float] = mapped_column(Float, default=0.0)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("test_attempts.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))

    attempt = relationship("TestAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", name="uq_rating_student_subject"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    position: Mapped[int] = mapped_column(Integer, nullable=True)

    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))

    student = relationship("User", back_populates="ratings")
    subject = relationship("Subject", back_populates="ratings")


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)

    earned = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (
        UniqueConstraint("student_id", "achievement_id", name="uq_user_achievement"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"))

    student = relationship("User", back_populates="earned_achievements")
    achievement = relationship("Achievement", back_populates="earned")
