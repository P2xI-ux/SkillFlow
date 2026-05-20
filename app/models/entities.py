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

class Faculty(Base):
    __tablename__ = "faculties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), unique=True)
    short_name: Mapped[str] = mapped_column(String(40), unique=True)

    departments = relationship("Department", back_populates="faculty")
    users = relationship("User", back_populates="faculty_rel")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"))

    faculty = relationship("Faculty", back_populates="departments")
    programs = relationship("Program", back_populates="department")
    users = relationship("User", back_populates="department_rel")


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(40), unique=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculties.id"))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)

    faculty = relationship("Faculty")
    department = relationship("Department", back_populates="programs")
    users = relationship("User", back_populates="program_rel")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.STUDENT)
    
    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculties.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("programs.id"), nullable=True)
    study_group: Mapped[str] = mapped_column(String(120), nullable=True)
    admission_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    telegram_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
    telegram_link_code: Mapped[str] = mapped_column(
        String(6), unique=True, nullable=True
    )
    telegram_link_code_created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True
    )
    telegram_link_code_expires_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    faculty_rel = relationship("Faculty", back_populates="users")
    department_rel = relationship("Department", back_populates="users")
    program_rel = relationship("Program", back_populates="users")

    @property
    def computed_course(self) -> int | None:
        if self.admission_year is None:
            return None
        from datetime import date
        today = date.today()
        years_passed = today.year - self.admission_year
        # After September 1 → new academic year started
        if today.month >= 9:
            years_passed += 1
        return min(max(years_passed, 1), 6)

    @property
    def computed_study_group(self) -> str | None:
        if not self.study_group:
            return None
        if not self.admission_year:
            return self.study_group
        
        # Parse the group, e.g. "ПИ-21" or "ИУ5-61Б"
        if '-' not in self.study_group:
            return self.study_group
        
        prefix, suffix = self.study_group.split('-', 1)
        import re
        match = re.search(r'\d+', suffix)
        if not match:
            return self.study_group
        
        digits = match.group()
        first_digit = int(digits[0])
        
        current_course = self.computed_course or 1
        
        reg_year = self.created_at.year if self.created_at else datetime.utcnow().year
        reg_month = self.created_at.month if self.created_at else datetime.utcnow().month
        reg_academic_year = reg_year if reg_month >= 9 else reg_year - 1
        reg_course = reg_academic_year - self.admission_year + 1
        if reg_course < 1:
            reg_course = 1
        
        course_diff = current_course - reg_course
        
        # Check if it was semester or course:
        is_semester = False
        if first_digit in (2 * reg_course, 2 * reg_course - 1):
            is_semester = True
        
        if is_semester:
            from datetime import date
            today = date.today()
            is_spring = (2 <= today.month <= 8)
            current_semester = current_course * 2 if is_spring else current_course * 2 - 1
            new_first_digit = str(current_semester)
        else:
            new_first_digit = str(max(1, first_digit + course_diff))
        
        new_suffix = suffix[:match.start()] + new_first_digit + digits[1:] + suffix[match.end():]
        return f"{prefix}-{new_suffix}"

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
