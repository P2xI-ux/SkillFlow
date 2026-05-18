from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_test_service
from app.api.errors import api_error, validation_error
from app.api.serializers import can_view_test, serialize_test_detail, serialize_test_list_item
from app.core.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models.entities import User
from app.models.enums import Role
from app.repositories.attempt_repository import AttemptRepository
from app.repositories.test_repository import TestRepository
from app.schemas import (
    AttemptResult,
    AttemptSubmission,
    ModerateTestRequest,
    TestCreate,
    TestDetail,
    TestListItem,
)

router = APIRouter(prefix="/tests", tags=["tests"])


@router.post("", response_model=TestDetail)
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
        raise validation_error(exc) from exc


@router.get("", response_model=list[TestListItem])
def list_tests(
    subject_id: int | None = None,
    mine: bool = False,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    repo = TestRepository(db)
    if mine:
        if not current_user:
            raise api_error(401, "AUTH_REQUIRED", "Нужна авторизация")
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


@router.get("/pending", response_model=list[TestListItem])
def list_pending_tests(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != Role.TEACHER:
        raise api_error(
            403, "FORBIDDEN", "Только преподаватель видит очередь модерации"
        )
    subject_ids = [subject.id for subject in current_user.teaching_subjects]
    if not subject_ids:
        return []
    return [
        serialize_test_list_item(item)
        for item in TestRepository(db).get_pending(subject_ids)
    ]


@router.get("/{test_id}", response_model=TestDetail)
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    test = TestRepository(db).get_full(test_id)
    if not test:
        raise api_error(404, "NOT_FOUND", "Тест не найден")
    if not can_view_test(test, current_user):
        raise api_error(403, "FORBIDDEN", "Нет доступа к тесту")
    return serialize_test_detail(test)


@router.post("/{test_id}/submit", response_model=TestDetail)
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
        raise validation_error(exc) from exc


@router.post("/{test_id}/moderate", response_model=TestDetail)
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
        raise validation_error(exc) from exc


@router.post("/{test_id}/attempt", response_model=AttemptResult)
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
        raise validation_error(exc) from exc
