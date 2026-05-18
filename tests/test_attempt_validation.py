class DummyQuestion:
    def __init__(self, qid):
        self.id = qid


class DummyTest:
    def __init__(self, ids):
        self.questions = [DummyQuestion(i) for i in ids]


class DummyAnswer:
    def __init__(self, question_id):
        self.question_id = question_id


def test_validate_attempt_answers_rejects_duplicates():
    from app.services.test_service import TestService

    test = DummyTest([1, 2])
    answers = [DummyAnswer(1), DummyAnswer(1)]
    try:
        TestService._validate_attempt_answers(test, answers)
    except ValueError as exc:
        assert "дублирующиеся" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_validate_attempt_answers_rejects_unknown_question_ids():
    from app.services.test_service import TestService

    test = DummyTest([1, 2])
    answers = [DummyAnswer(1), DummyAnswer(3)]
    try:
        TestService._validate_attempt_answers(test, answers)
    except ValueError as exc:
        assert "нет в тесте" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_validate_attempt_answers_requires_all_questions_answered():
    from app.services.test_service import TestService

    test = DummyTest([1, 2, 3])
    answers = [DummyAnswer(1), DummyAnswer(2)]
    try:
        TestService._validate_attempt_answers(test, answers)
    except ValueError as exc:
        assert "Не на все вопросы" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
import json

from app.models.entities import AnswerOption, Question
from app.models.enums import QuestionType
from app.schemas import AttemptAnswer
from app.services.test_service import TestService


class _TestWithQuestions:
    def __init__(self, questions):
        self.questions = questions


def test_attempt_validation_rejects_unknown_option_id():
    question = Question(id=1, text="Pick", points=5, question_type=QuestionType.SINGLE_CHOICE)
    question.answer_options = [AnswerOption(id=10, text="A", is_correct=True)]

    try:
        TestService._validate_attempt_answers(
            _TestWithQuestions([question]),
            [AttemptAnswer(question_id=1, selected_option_ids=[999])],
        )
    except ValueError as exc:
        assert "варианты" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_attempt_validation_rejects_incomplete_matching_answer():
    question = Question(
        id=2,
        text="Match",
        points=10,
        question_type=QuestionType.MATCHING,
        payload=json.dumps({"pairs": [{"left": "A", "right": "1"}, {"left": "B", "right": "2"}]}),
    )

    try:
        TestService._validate_attempt_answers(
            _TestWithQuestions([question]),
            [AttemptAnswer(question_id=2, matching_answer={"A": "1"})],
        )
    except ValueError as exc:
        assert "соответствие" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
