from dataclasses import dataclass, field


@dataclass
class QuestionScoreResult:
    question_id: int
    is_correct: bool
    points_earned: int
    selected_option_ids: list[int] = field(default_factory=list)
    correct_option_ids: list[int] = field(default_factory=list)
    text_answer: str | None = None
    matching_answer: dict[str, str] | None = None
    answer_payload: dict | None = None

    def as_feedback(self) -> dict:
        return {
            "question_id": self.question_id,
            "is_correct": self.is_correct,
            "points_earned": self.points_earned,
            "selected_option_ids": self.selected_option_ids,
            "correct_option_ids": self.correct_option_ids,
            "text_answer": self.text_answer,
            "matching_answer": self.matching_answer,
        }
