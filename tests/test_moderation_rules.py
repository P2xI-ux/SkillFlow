from app.schemas import ModerateTestRequest


def test_moderate_test_request_requires_comment_on_reject():
    try:
        ModerateTestRequest(action="reject", comment="   ")
    except ValueError as exc:
        assert "комментарий" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")


def test_moderate_test_request_allows_approve_without_comment():
    payload = ModerateTestRequest(action="approve", comment=None)
    assert payload.action == "approve"
from app.api.routes import _can_view_test
from app.models.enums import Role, TestStatus


class _Subject:
    def __init__(self, subject_id):
        self.id = subject_id


class _User:
    def __init__(self, user_id, role, subjects=None):
        self.id = user_id
        self.role = role
        self.teaching_subjects = subjects or []


class _Test:
    def __init__(self, author_id, subject_id, status):
        self.author_id = author_id
        self.subject_id = subject_id
        self.status = status


def test_teacher_cannot_view_unpublished_test_for_other_subject():
    teacher = _User(10, Role.TEACHER, [_Subject(1)])
    test = _Test(author_id=2, subject_id=99, status=TestStatus.DRAFT)

    assert not _can_view_test(test, teacher)


def test_teacher_can_view_unpublished_test_for_own_subject():
    teacher = _User(10, Role.TEACHER, [_Subject(1)])
    test = _Test(author_id=2, subject_id=1, status=TestStatus.PENDING_MODERATION)

    assert _can_view_test(test, teacher)
