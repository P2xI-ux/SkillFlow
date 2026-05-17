from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.security import get_password_hash, verify_password
from app.core.university_catalog import validate_student_profile, validate_teacher_profile
from app.models.entities import AnswerOption, Question, User
from app.models.enums import QuestionType, Role, TestStatus
from app.repositories.user_repository import UserRepository
from app.schemas import AttemptAnswer
from app.services.event_bus import EventBus
from app.services.question_visitors import ScoringVisitor
from app.services.rating_strategy import BonusStrategy, FirstAttemptStrategy, RatingContext, RatingStrategyFactory, StandardStrategy, TournamentStrategy
from app.services.state_machine import TestStateMachine


class DummyTest:
    def __init__(self, status):
        self.status = status
        self.published_at = None


def test_state_machine_allows_expected_transition():
    test = DummyTest(TestStatus.DRAFT)
    TestStateMachine(test.status).apply(test, "submit")
    assert test.status == TestStatus.PENDING_MODERATION


def test_state_machine_blocks_invalid_transition():
    test = DummyTest(TestStatus.DRAFT)
    try:
        TestStateMachine(test.status).apply(test, "approve")
    except ValueError as exc:
        assert "недопустим" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_rating_strategy_factory_picks_expected_implementation():
    assert isinstance(RatingStrategyFactory.build(RatingContext(score=10, difficulty=2)), StandardStrategy)
    assert isinstance(RatingStrategyFactory.build(RatingContext(score=10, difficulty=4)), StandardStrategy)
    assert isinstance(RatingStrategyFactory.build(RatingContext(score=10, difficulty=5)), BonusStrategy)
    assert isinstance(RatingStrategyFactory.build(RatingContext(score=10, difficulty=2, is_first_attempt=True)), FirstAttemptStrategy)
    assert isinstance(RatingStrategyFactory.build(RatingContext(score=10, difficulty=2, is_tournament=True)), TournamentStrategy)


def test_first_attempt_strategy_adds_bonus():
    strategy = FirstAttemptStrategy()
    assert strategy.calculate(10, 3) == 60


def test_scoring_visitor_scores_choice_and_text_questions():
    visitor = ScoringVisitor()
    choice = Question(id=1, text="Pick", points=5, question_type=QuestionType.SINGLE_CHOICE)
    choice.answer_options = [
        AnswerOption(id=1, text="A", is_correct=True),
        AnswerOption(id=2, text="B", is_correct=False),
    ]
    assert visitor.score(choice, AttemptAnswer(question_id=1, selected_option_ids=[1])).is_correct

    text = Question(id=2, text="Text", points=7, question_type=QuestionType.TEXT_ANSWER, payload='{"correct_answer": "Hello world"}')
    result = visitor.score(text, AttemptAnswer(question_id=2, text_answer=" hello   WORLD "))
    assert result.is_correct
    assert result.points_earned == 7


def test_scoring_visitor_scores_matching_questions():
    visitor = ScoringVisitor()
    question = Question(
        id=3,
        text="Match",
        points=10,
        question_type=QuestionType.MATCHING,
        payload='{"pairs": [{"left": "A", "right": "1"}, {"left": "B", "right": "2"}]}',
    )
    result = visitor.score(question, AttemptAnswer(question_id=3, matching_answer={"A": "1", "B": "2"}))
    assert result.is_correct
    assert result.points_earned == 10


def test_user_repository_returns_only_active_telegram_link_code():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        user = User(
            email="student@example.com",
            password_hash="hash",
            full_name="Student",
            role=Role.STUDENT,
            telegram_link_code="123456",
            telegram_link_code_expires_at=datetime.utcnow() + timedelta(seconds=20),
        )
        db.add(user)
        db.commit()

        repo = UserRepository(db)
        assert repo.get_by_active_link_code("123456").email == "student@example.com"

        user.telegram_link_code_expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.add(user)
        db.commit()
        assert repo.get_by_active_link_code("123456") is None
    finally:
        db.close()


def test_event_bus_collects_messages_from_subscribers():
    bus = EventBus()
    bus.subscribe("TEST_COMPLETED", lambda event: ["earned"])
    assert bus.publish("TEST_COMPLETED", {"student_id": 1}) == ["earned"]


def test_password_hashing_supports_short_passwords():
    password = "123456"

    hashed_password = get_password_hash(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)


def test_password_hashing_supports_unicode_passwords():
    password = "пароль6"

    hashed_password = get_password_hash(password)

    assert verify_password(password, hashed_password)


def test_university_catalog_validates_student_program_binding():
    validate_student_profile("ИнПИТ", "09.03.01")

    try:
        validate_student_profile("ИнПИТ", "13.03.01")
    except ValueError as exc:
        assert "не относится" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_university_catalog_validates_teacher_department_binding():
    validate_teacher_profile("ИнЭН", "ТАЭ")

    try:
        validate_teacher_profile("ИнЭН", "АРХ")
    except ValueError as exc:
        assert "не относится" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_telegram_link_code_generation_reuses_active_code_for_same_user_without_changes():
    from app.api.routes import create_link_code

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        user = User(
            email="linked@example.com",
            password_hash="hash",
            full_name="Linked User",
            role=Role.STUDENT,
            telegram_link_code="654321",
            telegram_link_code_expires_at=datetime.utcnow() + timedelta(minutes=5),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        result = create_link_code(db=db, current_user=user)
        assert result["code"] == "654321"
        assert result["ttl_seconds"] >= 0
    finally:
        db.close()


class _DummyPayload:
    def __init__(self, subject_id=1):
        self.subject_id = subject_id


def test_teacher_cannot_create_test():
    from app.services.test_service import TestService

    class _Repo:
        def __init__(self):
            self.db = type("DB", (), {"flush": lambda self: None})()

    class _UserRepo:
        def __init__(self, user):
            self.user = user
        def get_by_id(self, *_):
            return self.user

    teacher = type("Teacher", (), {"role": Role.TEACHER})()
    service = TestService(_Repo(), None, None, None, _UserRepo(teacher), EventBus())

    try:
        service.create_test(_DummyPayload(), 1)
    except ValueError as exc:
        assert "только студент" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
