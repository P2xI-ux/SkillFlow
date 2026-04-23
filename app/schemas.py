from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import QuestionType, Role, TestStatus


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    role: Role
    faculty: str | None = None
    study_group: str | None = None
    course: int | None = None
    department: str | None = None
    program_code: str | None = None
    subject_ids: list[int] = Field(default_factory=list)


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
    telegram_link_code: str | None = None
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


class QuestionCreate(BaseModel):
    text: str
    points: int = Field(ge=1, le=25)
    question_type: QuestionType
    options: list[AnswerOptionCreate] = Field(min_length=2, max_length=10)


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


class SubmitTestRequest(BaseModel):
    test_id: int


class AttemptAnswer(BaseModel):
    question_id: int
    selected_option_ids: list[int]


class AttemptSubmission(BaseModel):
    answers: list[AttemptAnswer]
    allow_retake: bool = False


class AttemptFeedbackItem(BaseModel):
    question_id: int
    is_correct: bool
    points_earned: int
    selected_option_ids: list[int]
    correct_option_ids: list[int]


class AttemptResult(BaseModel):
    attempt_id: int
    score: int
    max_score: int
    percentage: float
    rating_delta: int
    earned_achievements: list[str]
    feedback: list[AttemptFeedbackItem]


class RatingEntry(BaseModel):
    student_name: str
    total_score: int
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
    rating_total: int
    subject_breakdown: dict[str, int]
    latest_attempts: list[dict]


class TelegramLinkResponse(BaseModel):
    code: str


class TelegramConnectRequest(BaseModel):
    code: str
    telegram_id: str


TokenResponse.model_rebuild()
