import json

from app.core.security import get_password_hash
from app.models.entities import Achievement, AnswerOption, Question, Subject, Test, User
from app.models.enums import QuestionType, Role, TestStatus


DEFAULT_SUBJECTS = [
    ("Программирование", "PROG"),
    ("Математика", "MATH"),
    ("Физика", "PHYS"),
]

DEFAULT_ACHIEVEMENTS = [
    ("FIRST_TEST", "Первый тест", "Пройти хотя бы один тест"),
    ("STREAK_3", "Серия побед", "Три идеальных результата подряд"),
    ("SUBJECT_MASTER", "Эксперт предмета", "Попасть в топ-3 предмета"),
    ("TEST_CREATOR", "Создатель", "Опубликовать первый тест"),
    ("PERFECT_SCORE", "Идеальный результат", "Пройти тест без ошибок"),
]


def seed_core_data(db):
    for name, code in DEFAULT_SUBJECTS:
        if not db.query(Subject).filter(Subject.code == code).first():
            db.add(Subject(name=name, code=code))
    for code, name, description in DEFAULT_ACHIEVEMENTS:
        if not db.query(Achievement).filter(Achievement.code == code).first():
            db.add(Achievement(code=code, name=name, description=description))
    db.commit()


def seed_demo_data(db):
    seed_core_data(db)
    subject = db.query(Subject).filter(Subject.code == "PROG").first()

    student = _get_or_create_user(
        db,
        email="student@skillflow.local",
        full_name="Demo Student",
        role=Role.STUDENT,
        faculty="ИнПИТ",
        study_group="ДЕМО-1",
        course=2,
        program_code="09.03.01",
    )
    teacher = _get_or_create_user(
        db,
        email="teacher@skillflow.local",
        full_name="Demo Teacher",
        role=Role.TEACHER,
        faculty="ИнПИТ",
        department="ИКСП",
    )
    if subject and subject not in teacher.teaching_subjects:
        teacher.teaching_subjects.append(subject)

    if subject and not db.query(Test).filter(Test.title == "Demo Python Basics").first():
        test = Test(
            title="Demo Python Basics",
            description="Короткий опубликованный тест для проверки полного сценария.",
            difficulty=2,
            question_count=2,
            max_score=15,
            created_by_role=Role.STUDENT.value,
            status=TestStatus.PUBLISHED,
            subject=subject,
            author=student,
            moderator=teacher,
        )
        db.add(test)
        db.flush()

        choice = Question(
            text="Что выведет print(2 + 2)?",
            points=5,
            question_type=QuestionType.SINGLE_CHOICE,
            sort_order=1,
            test=test,
        )
        choice.answer_options = [
            AnswerOption(text="4", is_correct=True, sort_order=1),
            AnswerOption(text="22", is_correct=False, sort_order=2),
        ]
        matching = Question(
            text="Сопоставьте тип и пример",
            points=10,
            question_type=QuestionType.MATCHING,
            payload=json.dumps(
                {"pairs": [{"left": "str", "right": "'text'"}, {"left": "int", "right": "42"}]},
                ensure_ascii=False,
            ),
            sort_order=2,
            test=test,
        )
        db.add_all([choice, matching])

    db.commit()


def _get_or_create_user(db, **kwargs):
    user = db.query(User).filter(User.email == kwargs["email"]).first()
    if user:
        return user
    user = User(password_hash=get_password_hash("Demo12345"), **kwargs)
    db.add(user)
    db.flush()
    return user
