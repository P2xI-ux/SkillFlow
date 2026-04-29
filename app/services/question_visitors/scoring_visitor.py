import json

from app.models.entities import Question
from app.models.enums import QuestionType
from app.schemas import AttemptAnswer
from app.services.question_visitors.base import QuestionScoreResult


class ScoringVisitor:
    def score(self, question: Question, answer: AttemptAnswer | None) -> QuestionScoreResult:
        if question.question_type == QuestionType.SINGLE_CHOICE:
            return self.visit_single_choice(question, answer)
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            return self.visit_multiple_choice(question, answer)
        if question.question_type == QuestionType.TEXT_ANSWER:
            return self.visit_text_answer(question, answer)
        if question.question_type == QuestionType.MATCHING:
            return self.visit_matching(question, answer)
        raise ValueError(f"Unsupported question type: {question.question_type}")

    def visit_single_choice(self, question: Question, answer: AttemptAnswer | None) -> QuestionScoreResult:
        selected_ids = sorted(answer.selected_option_ids if answer else [])
        correct_ids = sorted(option.id for option in question.answer_options if option.is_correct)
        is_correct = len(selected_ids) == 1 and selected_ids == correct_ids
        return self._choice_result(question, selected_ids, correct_ids, is_correct)

    def visit_multiple_choice(self, question: Question, answer: AttemptAnswer | None) -> QuestionScoreResult:
        selected_ids = sorted(answer.selected_option_ids if answer else [])
        correct_ids = sorted(option.id for option in question.answer_options if option.is_correct)
        is_correct = selected_ids == correct_ids
        return self._choice_result(question, selected_ids, correct_ids, is_correct)

    def visit_text_answer(self, question: Question, answer: AttemptAnswer | None) -> QuestionScoreResult:
        payload = self._payload(question)
        expected = self._normalize_text(payload.get("correct_answer", ""))
        actual = self._normalize_text(answer.text_answer if answer else "")
        is_correct = bool(expected) and actual == expected
        return QuestionScoreResult(
            question_id=question.id,
            is_correct=is_correct,
            points_earned=question.points if is_correct else 0,
            text_answer=answer.text_answer if answer else "",
            answer_payload={"text_answer": answer.text_answer if answer else ""},
        )

    def visit_matching(self, question: Question, answer: AttemptAnswer | None) -> QuestionScoreResult:
        pairs = self._payload(question).get("pairs", [])
        expected = {str(pair["left"]).strip(): str(pair["right"]).strip() for pair in pairs}
        actual = {str(left).strip(): str(right).strip() for left, right in (answer.matching_answer or {}).items()} if answer else {}
        is_correct = bool(expected) and actual == expected
        return QuestionScoreResult(
            question_id=question.id,
            is_correct=is_correct,
            points_earned=question.points if is_correct else 0,
            matching_answer=actual,
            answer_payload={"matching_answer": actual},
        )

    def _choice_result(self, question: Question, selected_ids: list[int], correct_ids: list[int], is_correct: bool):
        return QuestionScoreResult(
            question_id=question.id,
            is_correct=is_correct,
            points_earned=question.points if is_correct else 0,
            selected_option_ids=selected_ids,
            correct_option_ids=correct_ids,
        )

    def _payload(self, question: Question) -> dict:
        if not question.payload:
            return {}
        return json.loads(question.payload)

    def _normalize_text(self, value: str | None) -> str:
        return " ".join((value or "").strip().casefold().split())
