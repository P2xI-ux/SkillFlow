from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.seed import seed_core_data
from app.main import app
from app.models.entities import Subject, User


def _client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    with Session() as db:
        seed_core_data(db)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), Session


def _register(client, payload):
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_full_test_lifecycle_and_retake_policy():
    client, Session = _client()
    try:
        with Session() as db:
            subject_id = db.query(Subject).filter(Subject.code == "PROG").one().id
            from app.models.entities import Faculty, Department, Program
            faculty = db.query(Faculty).filter(Faculty.short_name == "ИнПИТ").one()
            dept = db.query(Department).filter(Department.code == "ИКСП").one()
            prog = db.query(Program).filter(Program.code == "09.03.01").one()
            faculty_id = faculty.id
            department_id = dept.id
            program_id = prog.id

        student = _register(
            client,
            {
                "email": "student@example.com",
                "password": "Strong123",
                "full_name": "Student",
                "role": "STUDENT",
                "faculty_id": faculty_id,
                "study_group": "B-1",
                "admission_year": 2024,
                "program_id": program_id,
            },
        )
        teacher = _register(
            client,
            {
                "email": "teacher@example.com",
                "password": "Strong123",
                "full_name": "Teacher",
                "role": "TEACHER",
                "faculty_id": faculty_id,
                "department_id": department_id,
                "subject_ids": [subject_id],
            },
        )

        student_headers = {"Authorization": f"Bearer {student['access_token']}"}
        teacher_headers = {"Authorization": f"Bearer {teacher['access_token']}"}

        created = client.post(
            "/api/tests",
            headers=student_headers,
            json={
                "title": "Lifecycle test",
                "description": "API scenario",
                "subject_id": subject_id,
                "difficulty": 2,
                "questions": [
                    {
                        "text": "2 + 2?",
                        "points": 5,
                        "question_type": "SINGLE_CHOICE",
                        "options": [
                            {"text": "4", "is_correct": True},
                            {"text": "5", "is_correct": False},
                        ],
                    }
                ],
            },
        )
        assert created.status_code == 200, created.text
        test_id = created.json()["id"]
        question = created.json()["questions"][0]
        option_id = question["options"][0]["id"]

        submitted = client.post(f"/api/tests/{test_id}/submit", headers=student_headers)
        assert submitted.status_code == 200, submitted.text

        moderated = client.post(
            f"/api/tests/{test_id}/moderate",
            headers=teacher_headers,
            json={"action": "approve", "comment": "ok"},
        )
        assert moderated.status_code == 200, moderated.text

        attempted = client.post(
            f"/api/tests/{test_id}/attempt",
            headers=student_headers,
            json={"answers": [{"question_id": question["id"], "selected_option_ids": [option_id]}]},
        )
        assert attempted.status_code == 200, attempted.text
        assert attempted.json()["score"] == 5

        duplicate = client.post(
            f"/api/tests/{test_id}/attempt",
            headers=student_headers,
            json={"answers": [{"question_id": question["id"], "selected_option_ids": [option_id]}]},
        )
        assert duplicate.status_code == 400
        assert duplicate.json()["code"] == "VALIDATION_ERROR"

        retake = client.post(
            f"/api/tests/{test_id}/attempt",
            headers=student_headers,
            json={
                "allow_retake": True,
                "answers": [{"question_id": question["id"], "selected_option_ids": [option_id]}],
            },
        )
        assert retake.status_code == 200, retake.text
    finally:
        app.dependency_overrides.clear()


def test_telegram_link_code_expiry_uses_structured_error():
    client, Session = _client()
    try:
        with Session() as db:
            from app.models.entities import Faculty, Program
            faculty = db.query(Faculty).filter(Faculty.short_name == "ИнПИТ").one()
            prog = db.query(Program).filter(Program.code == "09.03.01").one()
            faculty_id = faculty.id
            program_id = prog.id

        student = _register(
            client,
            {
                "email": "telegram@example.com",
                "password": "Strong123",
                "full_name": "Telegram Student",
                "role": "STUDENT",
                "faculty_id": faculty_id,
                "study_group": "B-2",
                "admission_year": 2023,
                "program_id": program_id,
            },
        )
        headers = {"Authorization": f"Bearer {student['access_token']}"}
        code_response = client.post("/api/telegram/link-code", headers=headers)
        assert code_response.status_code == 200, code_response.text
        code = code_response.json()["code"]

        with Session() as db:
            user = db.query(User).filter(User.email == "telegram@example.com").one()
            user.telegram_link_code_expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.commit()

        expired = client.post(
            "/api/telegram/connect",
            json={"code": code, "telegram_id": "123456789"},
        )
        assert expired.status_code == 410
        assert expired.json()["code"] == "LINK_CODE_EXPIRED"
    finally:
        app.dependency_overrides.clear()
