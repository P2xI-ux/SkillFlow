import json
import random
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.events import event_bus
from app.core.university_catalog import get_catalog_payload
from app.dependencies import get_current_user, get_current_user_optional
from app.models.entities import Subject, Test, User
from app.models.enums import Role, TestStatus
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.attempt_repository import AttemptRepository
from app.repositories.rating_repository import RatingRepository
from app.repositories.test_repository import TestRepository
from app.repositories.user_repository import UserRepository
from app.schemas import (
    AchievementResponse,
    AttemptResult,
    AttemptSubmission,
    ModerateTestRequest,
    StatsResponse,
    SubjectResponse,
    TelegramConnectRequest,
    TelegramLinkResponse,
    TestCreate,
    TestDetail,
    TestListItem,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.test_service import TestService

router = APIRouter(prefix="/api")




def _generate_telegram_link_code(user_repo: UserRepository, max_attempts: int = 20) -> str:
    for _ in range(max_attempts):
        code = "".join(random.choices(string.digits, k=6))
        if not user_repo.get_by_active_link_code(code):
            return code
    raise HTTPException(
        status_code=503,
        detail="Не удалось сгенерировать Telegram link code. Попробуйте позже",
    )

def get_test_service(db: Session):
    return TestService(
        TestRepository(db),
        AttemptRepository(db),
        RatingRepository(db),
        AchievementRepository(db),
        UserRepository(db),
        event_bus,
    )


@router.post("/auth/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    try:
        token, user = AuthService(UserRepository(db)).register(payload)
        db.commit()
        db.refresh(user)
        return {"access_token": token, "user": user}
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    try:
        token, user = AuthService(UserRepository(db)).login(payload)
        return {"access_token": token, "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/subjects", response_model=list[SubjectResponse])
def list_subjects(db: Session = Depends(get_db)):
    return db.scalars(select(Subject).order_by(Subject.name.asc())).all()


@router.get("/university/catalog")
def university_catalog():
    return get_catalog_payload()


@router.get("/users/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/tests", response_model=TestDetail)
def create_test(
    payload: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        test = get_test_service(db).create_test(payload, current_user.id)
        db.commit()
        return serialize_test_detail(test)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/tests", response_model=list[TestListItem])
def list_tests(
    subject_id: int | None = None,
    mine: bool = False,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    repo = TestRepository(db)
    if mine:
        if not current_user:
            raise HTTPException(status_code=401, detail="Нужна авторизация")
        return [
            serialize_test_list_item(item)
            for item in repo.get_by_author(current_user.id)
        ]
    attempted_test_ids: set[int] = set()
    if current_user and current_user.role == Role.STUDENT:
        attempted_test_ids = {
            item.test_id
            for item in AttemptRepository(db).get_completed_by_student(current_user.id)
        }
    return [
        serialize_test_list_item(item, item.id in attempted_test_ids)
        for item in repo.get_published(subject_id)
    ]


@router.get("/tests/pending", response_model=list[TestListItem])
def list_pending_tests(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.TEACHER:
        raise HTTPException(
            status_code=403, detail="Только преподаватель видит очередь модерации"
        )
    subject_ids = [subject.id for subject in current_user.teaching_subjects]
    if not subject_ids:
        return []
    return [
        serialize_test_list_item(item)
        for item in TestRepository(db).get_pending(subject_ids)
    ]


@router.get("/tests/{test_id}", response_model=TestDetail)
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    test = TestRepository(db).get_full(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    if (
        test.status != TestStatus.PUBLISHED
        and current_user.role != Role.TEACHER
        and test.author_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Нет доступа к тесту")
    return serialize_test_detail(test)


@router.post("/tests/{test_id}/submit", response_model=TestDetail)
def submit_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        test = get_test_service(db).submit_for_moderation(test_id, current_user)
        db.commit()
        return serialize_test_detail(test)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tests/{test_id}/moderate", response_model=TestDetail)
def moderate_test(
    test_id: int,
    payload: ModerateTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        test = get_test_service(db).moderate_test(
            test_id, current_user, payload.action, payload.comment
        )
        db.commit()
        return serialize_test_detail(test)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/tests/{test_id}/attempt", response_model=AttemptResult)
def attempt_test(
    test_id: int,
    payload: AttemptSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = get_test_service(db).take_test(
            test_id, current_user, payload.answers, payload.allow_retake
        )
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ratings")
def ratings(subject_id: int | None = None, db: Session = Depends(get_db)):
    leaderboard = RatingRepository(db).get_leaderboard(subject_id)
    return [
        {
            "student_name": item.student.full_name,
            "total_score": item.total_score,
            "position": item.position,
            "subject_name": item.subject.name,
            "faculty": item.student.faculty,
        }
        for item in leaderboard
    ]


@router.get("/achievements/me", response_model=list[AchievementResponse])
def my_achievements(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    items = AchievementRepository(db).get_user_achievements(current_user.id)
    return [
        {
            "code": item.achievement.code,
            "name": item.achievement.name,
            "description": item.achievement.description,
            "earned_at": item.earned_at,
        }
        for item in items
    ]


@router.get("/stats/me", response_model=StatsResponse)
def my_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return get_test_service(db).build_stats(current_user)


@router.post("/telegram/link-code", response_model=TelegramLinkResponse)
def create_link_code(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.telegram_id:
        raise HTTPException(
            status_code=409,
            detail="Аккаунт уже привязан к Telegram",
        )

    user_repo = UserRepository(db)
    now = datetime.utcnow()
    if (
        current_user.telegram_link_code
        and current_user.telegram_link_code_expires_at
        and current_user.telegram_link_code_expires_at > now
    ):
        return {
            "code": current_user.telegram_link_code,
            "expires_at": current_user.telegram_link_code_expires_at,
            "ttl_seconds": max(
                0,
                int((current_user.telegram_link_code_expires_at - now).total_seconds()),
            ),
        }

    current_user.telegram_link_code = _generate_telegram_link_code(user_repo)
    current_user.telegram_link_code_created_at = now
    current_user.telegram_link_code_expires_at = now + timedelta(
        seconds=settings.telegram_link_code_ttl_seconds
    )
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {
        "code": current_user.telegram_link_code,
        "expires_at": current_user.telegram_link_code_expires_at,
        "ttl_seconds": settings.telegram_link_code_ttl_seconds,
    }


@router.post("/telegram/connect")
def connect_telegram(payload: TelegramConnectRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    existing_user = user_repo.get_by_telegram_id(payload.telegram_id)
    if existing_user:
        raise HTTPException(status_code=409, detail="Telegram аккаунт уже привязан")
    user = user_repo.get_by_active_link_code(payload.code)
    if not user:
        expired_user = user_repo.get_by_link_code(payload.code)
        if expired_user:
            expired_user.telegram_link_code = None
            expired_user.telegram_link_code_created_at = None
            expired_user.telegram_link_code_expires_at = None
            db.add(expired_user)
            db.commit()
            raise HTTPException(status_code=410, detail="Telegram link code expired")
        raise HTTPException(status_code=404, detail="Telegram link code not found")
    user.telegram_id = payload.telegram_id
    user.telegram_link_code = None
    user.telegram_link_code_created_at = None
    user.telegram_link_code_expires_at = None
    db.add(user)
    db.commit()
    return {"status": "connected", "email": user.email}


def serialize_test_list_item(test: Test, attempted: bool = False):
    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "difficulty": test.difficulty,
        "status": test.status,
        "subject_name": test.subject.name,
        "author_name": test.author.full_name,
        "moderation_comment": test.moderation_comment,
        "question_count": len(test.questions),
        "attempted": attempted,
    }


def serialize_test_detail(test: Test):
    return {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "difficulty": test.difficulty,
        "status": test.status,
        "subject_name": test.subject.name,
        "author_name": test.author.full_name,
        "moderation_comment": test.moderation_comment,
        "questions": [
            serialize_question(question)
            for question in sorted(test.questions, key=lambda item: item.sort_order)
        ],
    }


def serialize_question(question):
    payload = json.loads(question.payload) if question.payload else {}
    matching_pairs = payload.get("pairs", [])
    matching_options = [pair["right"] for pair in matching_pairs]
    return {
        "id": question.id,
        "text": question.text,
        "points": question.points,
        "question_type": question.question_type,
        "sort_order": question.sort_order,
        "options": [
            {"id": option.id, "text": option.text, "sort_order": option.sort_order}
            for option in sorted(
                question.answer_options, key=lambda item: item.sort_order
            )
        ],
        "matching_left": [pair["left"] for pair in matching_pairs],
        "matching_options": random.sample(matching_options, len(matching_options))
        if matching_options
        else [],
    }
