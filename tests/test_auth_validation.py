def test_password_strength_requires_letter_and_digit():
    from app.schemas import UserRegister
    from app.models.enums import Role

    try:
        UserRegister(
            email="student@example.com",
            password="12345678",
            full_name="Student",
            role=Role.STUDENT,
        )
    except ValueError as exc:
        assert "букву" in str(exc)
    else:
        raise AssertionError("Expected ValueError")



def test_teacher_rejects_student_profile_fields():
    from app.models.enums import Role
    from app.schemas import UserRegister

    payload = UserRegister(
        email="teacher@example.com",
        password="Strong123",
        full_name="Teacher",
        role=Role.TEACHER,
        faculty="ИнПИТ",
        department="ИКСП",
        subject_ids=[1],
        study_group="b-1",
    )

    class _Repo:
        db = type("DB", (), {"scalars": lambda self, *_: type("R", (), {"all": lambda self: []})()})()
        def get_by_email(self, *_):
            return None
        def save(self, *_):
            return None

    from app.services.auth_service import AuthService

    try:
        AuthService(_Repo()).register(payload)
    except ValueError as exc:
        assert "Преподавателю" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_student_profile_requires_group_course_program():
    from app.models.enums import Role
    from app.schemas import UserRegister

    try:
        UserRegister(
            email="s@example.com",
            password="Strong123",
            full_name="Student",
            role=Role.STUDENT,
            faculty="ИнПИТ",
            study_group="",
            course=0,
            program_code="",
        )
    except ValueError as exc:
        assert "студента" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")


def test_teacher_profile_requires_department_and_subjects():
    from app.models.enums import Role
    from app.schemas import UserRegister

    try:
        UserRegister(
            email="t@example.com",
            password="Strong123",
            full_name="Teacher",
            role=Role.TEACHER,
            faculty="ИнПИТ",
            department="",
            subject_ids=[],
        )
    except ValueError as exc:
        assert "преподавателя" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError")


def test_user_response_does_not_expose_telegram_link_code():
    from app.models.enums import Role
    from app.schemas import UserResponse

    schema = UserResponse(
        id=1,
        email="student@example.com",
        full_name="Student",
        role=Role.STUDENT,
        telegram_id=None,
    )

    assert "telegram_link_code" not in schema.model_dump()
