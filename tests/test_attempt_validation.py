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
