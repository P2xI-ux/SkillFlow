from app.models.entities import Test, User
from app.models.enums import TestStatus
from app.repositories.test_repository import TestRepository
from app.services.question_factory import QuestionFactory


class TestBuilder:
    def __init__(self, test_repository: TestRepository):
        self.test_repository = test_repository

    def build(self, payload, author: User) -> Test:
        test = Test(
            title=payload.title,
            description=payload.description,
            subject_id=payload.subject_id,
            difficulty=payload.difficulty,
            author_id=author.id,
            created_by_role=author.role.value,
            question_count=len(payload.questions),
            max_score=sum(question.points for question in payload.questions),
            status=TestStatus.DRAFT,
        )
        self.test_repository.save(test)

        for index, question_payload in enumerate(payload.questions, start=1):
            question_factory = QuestionFactory.create(
                question_payload.question_type,
                self._question_data(question_payload),
            )
            self.test_repository.save(question_factory.build_model(test.id, index))

        self.test_repository.db.flush()
        return self.test_repository.get_full(test.id)

    def _question_data(self, question_payload) -> dict:
        data = {
            "text": question_payload.text,
            "points": question_payload.points,
        }
        if question_payload.options:
            data["options"] = [option.model_dump() for option in question_payload.options]
        if question_payload.correct_answer is not None:
            data["correct_answer"] = question_payload.correct_answer
        if question_payload.matching_pairs:
            data["matching_pairs"] = [pair.model_dump() for pair in question_payload.matching_pairs]
        return data
