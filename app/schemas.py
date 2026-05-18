from datetime import datetime
import re
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.enums import QuestionType, Role, TestStatus


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str
    role: Role
    faculty: str | None = None
    study_group: str | None = None
    course: int | None = None
    department: str | None = None
    program_code: str | None = None
    subject_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_password_strength(self):
        has_letter = bool(re.search(r"[A-Za-zА-Яа-я]", self.password or ""))
        has_digit = bool(re.search(r"\d", self.password or ""))
        if not (has_letter and has_digit):
            raise ValueError("Пароль должен содержать минимум одну букву и одну цифру")
        return self

    @model_validator(mode="after")
    def validate_role_specific_profile(self):
        if self.role == Role.STUDENT:
            if not (self.study_group or "").strip():
                raise ValueError("Для студента обязательна учебная группа")
            if self.course is None or self.course < 1 or self.course > 6:
                raise ValueError("Для студента курс должен быть от 1 до 6")
            if not (self.program_code or "").strip():
                raise ValueError("Для студента обязателен код направления")
        if self.role == Role.TEACHER:
            if not (self.department or "").strip():
                raise ValueError("Для преподавателя обязательна кафедра")
            if not self.subject_ids:
                raise ValueError("Для преподавателя нужно выбрать хотя бы одну дисциплину")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: Role
    faculty: str | None = None
    study_group: str | None = None
    course: int | None = None
    department: str | None = None
    program_code: str | None = None
    telegram_id: str | None = None
    teaching_subjects: list["SubjectResponse"] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SubjectResponse(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class AnswerOptionCreate(BaseModel):
    text: str
    is_correct: bool = False


class MatchingPairCreate(BaseModel):
    left: str
    right: str


class QuestionCreate(BaseModel):
    text: str
    points: int = Field(ge=1, le=25)
    question_type: QuestionType
    options: list[AnswerOptionCreate] = Field(default_factory=list)
    correct_answer: str | None = None
    matching_pairs: list[MatchingPairCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_question_payload(self):
        if self.question_type in {
            QuestionType.SINGLE_CHOICE,
            QuestionType.MULTIPLE_CHOICE,
        }:
            if not 2 <= len(self.options) <= 10:
                raise ValueError("Choice questions require 2-10 options")
        if (
            self.question_type == QuestionType.TEXT_ANSWER
            and not (self.correct_answer or "").strip()
        ):
            raise ValueError("TEXT_ANSWER requires correct_answer")
        if self.question_type == QuestionType.MATCHING and len(self.matching_pairs) < 2:
            raise ValueError("MATCHING requires at least two pairs")
        return self


class TestCreate(BaseModel):
    title: str
    description: str = ""
    subject_id: int
    difficulty: int = Field(ge=1, le=5)
    questions: list[QuestionCreate] = Field(min_length=1, max_length=50)


class AnswerOptionResponse(BaseModel):
    id: int
    text: str
    sort_order: int

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    text: str
    points: int
    question_type: QuestionType
    sort_order: int
    options: list[AnswerOptionResponse]
    matching_left: list[str] = Field(default_factory=list)
    matching_options: list[str] = Field(default_factory=list)


class TestListItem(BaseModel):
    id: int
    title: str
    description: str
    difficulty: int
    status: TestStatus
    subject_name: str
    author_name: str
    moderation_comment: str | None = None
    question_count: int
    attempted: bool = False


class TestDetail(BaseModel):
    id: int
    title: str
    description: str
    difficulty: int
    status: TestStatus
    subject_name: str
    author_name: str
    moderation_comment: str | None = None
    questions: list[QuestionResponse]


class ModerateTestRequest(BaseModel):
    action: Literal["approve", "reject"]
    comment: str | None = None

    @model_validator(mode="after")
    def validate_moderation_comment(self):
        if self.action == "reject" and not (self.comment or "").strip():
            raise ValueError("Для отклонения теста нужен комментарий")
        return self


class SubmitTestRequest(BaseModel):
    test_id: int


class AttemptAnswer(BaseModel):
    question_id: int
    selected_option_ids: list[int] = Field(default_factory=list)
    text_answer: str | None = None
    matching_answer: dict[str, str] | None = None


class AttemptSubmission(BaseModel):
    answers: list[AttemptAnswer]
    allow_retake: bool = False


class AttemptFeedbackItem(BaseModel):
    question_id: int
    is_correct: bool
    points_earned: float
    selected_option_ids: list[int]
    correct_option_ids: list[int]
    text_answer: str | None = None
    matching_answer: dict[str, str] | None = None


class AttemptResult(BaseModel):
    attempt_id: int
    score: float
    max_score: float
    percentage: float
    rating_delta: float
    earned_achievements: list[str]
    feedback: list[AttemptFeedbackItem]


class RatingEntry(BaseModel):
    student_name: str
    total_score: float
    position: int
    subject_name: str


class AchievementResponse(BaseModel):
    code: str
    name: str
    description: str
    earned_at: datetime


class StatsResponse(BaseModel):
    tests_completed: int
    average_score_percent: float
    rating_total: float
    subject_breakdown: dict[str, float]
    latest_attempts: list[dict]


class TelegramLinkResponse(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    expires_at: datetime
    ttl_seconds: int = Field(ge=0)


class TelegramConnectRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    telegram_id: str = Field(min_length=3, max_length=64)


class ErrorResponse(BaseModel):
    code: str
    message: str


TokenResponse.model_rebuild()
