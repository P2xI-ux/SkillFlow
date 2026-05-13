import json

from app.models.entities import Question
from app.models.enums import QuestionType
from app.schemas import AttemptAnswer
from app.services.question_visitors.base import QuestionScoreResult


class ScoringVisitor:
    def score(
        self, question: Question, answer: AttemptAnswer | None
    ) -> QuestionScoreResult:
        if question.question_type == QuestionType.SINGLE_CHOICE:
            return self.visit_single_choice(question, answer)
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            return self.visit_multiple_choice(question, answer)
        if question.question_type == QuestionType.TEXT_ANSWER:
            return self.visit_text_answer(question, answer)
        if question.question_type == QuestionType.MATCHING:
            return self.visit_matching(question, answer)
        raise ValueError(f"Unsupported question type: {question.question_type}")

    def visit_single_choice(
        self, question: Question, answer: AttemptAnswer | None
    ) -> QuestionScoreResult:
        selected_ids = sorted(answer.selected_option_ids if answer else [])
        correct_ids = sorted(
            option.id for option in question.answer_options if option.is_correct
        )
        is_correct = len(selected_ids) == 1 and selected_ids == correct_ids
        return self._choice_result(
            question,
            selected_ids,
            correct_ids,
            is_correct,
            question.points if is_correct else 0.0,
        )

    def visit_multiple_choice(
        self, question: Question, answer: AttemptAnswer | None
    ) -> QuestionScoreResult:
        selected_ids = set(answer.selected_option_ids if answer else [])
        correct_ids = set(
            option.id for option in question.answer_options if option.is_correct
        )
        all_option_ids = set(option.id for option in question.answer_options)

        # Standard rule: 0 if any incorrect selected
        incorrect_selected = selected_ids - correct_ids
        if incorrect_selected or not selected_ids:
            return self._choice_result(
                question,
                sorted(list(selected_ids)),
                sorted(list(correct_ids)),
                False,
                0.0,
            )

        # Partial points: (correct_selected / total_correct) * points
        correct_selected_count = len(selected_ids & correct_ids)
        total_correct_count = len(correct_ids)

        is_correct = correct_selected_count == total_correct_count
        points_earned = (
            (correct_selected_count / total_correct_count) * question.points
            if total_correct_count > 0
            else 0.0
        )

        return self._choice_result(
            question,
            sorted(list(selected_ids)),
            sorted(list(correct_ids)),
            is_correct,
            points_earned,
        )

    def visit_text_answer(
        self, question: Question, answer: AttemptAnswer | None
    ) -> QuestionScoreResult:
        payload = self._payload(question)
        expected = self._normalize_text(payload.get("correct_answer", ""))
        actual = self._normalize_text(answer.text_answer if answer else "")
        is_correct = bool(expected) and actual == expected
        return QuestionScoreResult(
            question_id=question.id,
            is_correct=is_correct,
            points_earned=float(question.points) if is_correct else 0.0,
            text_answer=answer.text_answer if answer else "",
            answer_payload={"text_answer": answer.text_answer if answer else ""},
        )

    def visit_matching(
        self, question: Question, answer: AttemptAnswer | None
    ) -> QuestionScoreResult:
        pairs = self._payload(question).get("pairs", [])
        total_pairs = len(pairs)
        if total_pairs == 0:
            return QuestionScoreResult(
                question_id=question.id, is_correct=False, points_earned=0.0
            )

        expected = {
            str(pair["left"]).strip(): str(pair["right"]).strip() for pair in pairs
        }
        actual = (
            {
                str(left).strip(): str(right).strip()
                for left, right in (answer.matching_answer or {}).items()
            }
            if answer
            else {}
        )

        matches = 0
        for left, right in expected.items():
            if actual.get(left) == right:
                matches += 1

        is_correct = matches == total_pairs
        points_earned = (matches / total_pairs) * question.points

        return QuestionScoreResult(
            question_id=question.id,
            is_correct=is_correct,
            points_earned=points_earned,
            matching_answer=actual,
            answer_payload={"matching_answer": actual},
        )

    def _choice_result(
        self,
        question: Question,
        selected_ids: list[int],
        correct_ids: list[int],
        is_correct: bool,
        points_earned: float,
    ):
        return QuestionScoreResult(
            question_id=question.id,
            is_correct=is_correct,
            points_earned=points_earned,
            selected_option_ids=selected_ids,
            correct_option_ids=correct_ids,
        )

    def _payload(self, question: Question) -> dict:
        if not question.payload:
            return {}
        return json.loads(question.payload)

    def _normalize_text(self, value: str | None) -> str:
        return " ".join((value or "").strip().casefold().split())
