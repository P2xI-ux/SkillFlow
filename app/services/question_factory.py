from dataclasses import dataclass
import json

from app.models.entities import AnswerOption, Question
from app.models.enums import QuestionType


@dataclass
class BaseQuestion:
    text: str
    points: int

    def build_model(self, test_id: int, sort_order: int) -> Question:
        raise NotImplementedError


@dataclass
class SingleChoiceQuestion(BaseQuestion):
    options: list[dict]

    def build_model(self, test_id: int, sort_order: int) -> Question:
        correct_count = sum(1 for option in self.options if option["is_correct"])
        if correct_count != 1:
            raise ValueError("SINGLE_CHOICE requires exactly one correct option")
        question = Question(
            test_id=test_id,
            text=self.text,
            points=self.points,
            question_type=QuestionType.SINGLE_CHOICE,
            sort_order=sort_order,
        )
        question.answer_options = [
            AnswerOption(text=option["text"], is_correct=option["is_correct"], sort_order=index)
            for index, option in enumerate(self.options, start=1)
        ]
        return question


@dataclass
class MultipleChoiceQuestion(BaseQuestion):
    options: list[dict]

    def build_model(self, test_id: int, sort_order: int) -> Question:
        correct_count = sum(1 for option in self.options if option["is_correct"])
        if correct_count < 1:
            raise ValueError("MULTIPLE_CHOICE requires at least one correct option")
        question = Question(
            test_id=test_id,
            text=self.text,
            points=self.points,
            question_type=QuestionType.MULTIPLE_CHOICE,
            sort_order=sort_order,
        )
        question.answer_options = [
            AnswerOption(text=option["text"], is_correct=option["is_correct"], sort_order=index)
            for index, option in enumerate(self.options, start=1)
        ]
        return question


@dataclass
class TextAnswerQuestion(BaseQuestion):
    correct_answer: str

    def build_model(self, test_id: int, sort_order: int) -> Question:
        if not self.correct_answer.strip():
            raise ValueError("TEXT_ANSWER requires a non-empty correct answer")
        return Question(
            test_id=test_id,
            text=self.text,
            points=self.points,
            question_type=QuestionType.TEXT_ANSWER,
            sort_order=sort_order,
            payload=json.dumps({"correct_answer": self.correct_answer.strip()}, ensure_ascii=False),
        )


@dataclass
class MatchingQuestion(BaseQuestion):
    matching_pairs: list[dict]

    def build_model(self, test_id: int, sort_order: int) -> Question:
        if len(self.matching_pairs) < 2:
            raise ValueError("MATCHING requires at least two pairs")
        pairs = [{"left": str(pair["left"]).strip(), "right": str(pair["right"]).strip()} for pair in self.matching_pairs]
        if any(not pair["left"] or not pair["right"] for pair in pairs):
            raise ValueError("MATCHING pairs require non-empty left and right values")
        return Question(
            test_id=test_id,
            text=self.text,
            points=self.points,
            question_type=QuestionType.MATCHING,
            sort_order=sort_order,
            payload=json.dumps({"pairs": pairs}, ensure_ascii=False),
        )


class QuestionFactory:
    @staticmethod
    def create(question_type: QuestionType, data: dict):
        if question_type == QuestionType.SINGLE_CHOICE:
            return SingleChoiceQuestion(**data)
        if question_type == QuestionType.MULTIPLE_CHOICE:
            return MultipleChoiceQuestion(**data)
        if question_type == QuestionType.TEXT_ANSWER:
            return TextAnswerQuestion(**data)
        if question_type == QuestionType.MATCHING:
            return MatchingQuestion(**data)
        raise ValueError(f"Unknown question type: {question_type}")
