from dataclasses import dataclass

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
            raise ValueError("У вопроса SINGLE_CHOICE должен быть ровно один правильный ответ")
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
            raise ValueError("У вопроса MULTIPLE_CHOICE должен быть хотя бы один правильный ответ")
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


class QuestionFactory:
    @staticmethod
    def create(question_type: QuestionType, data: dict):
        if question_type == QuestionType.SINGLE_CHOICE:
            return SingleChoiceQuestion(**data)
        if question_type == QuestionType.MULTIPLE_CHOICE:
            return MultipleChoiceQuestion(**data)
        raise ValueError(f"Неизвестный тип вопроса: {question_type}")
