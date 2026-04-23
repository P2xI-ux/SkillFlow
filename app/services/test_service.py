from datetime import datetime

from app.models.entities import Test, TestAttempt, User, UserAnswer
from app.models.enums import AttemptStatus, Role, TestStatus
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.attempt_repository import AttemptRepository
from app.repositories.rating_repository import RatingRepository
from app.repositories.test_repository import TestRepository
from app.repositories.user_repository import UserRepository
from app.services.achievement_service import AchievementService
from app.services.event_bus import EventBus
from app.services.question_factory import QuestionFactory
from app.services.rating_strategy import RatingStrategyFactory
from app.services.state_machine import TestStateMachine


class TestService:
    def __init__(
        self,
        test_repository: TestRepository,
        attempt_repository: AttemptRepository,
        rating_repository: RatingRepository,
        achievement_repository: AchievementRepository,
        user_repository: UserRepository,
        event_bus: EventBus,
    ):
        self.test_repository = test_repository
        self.attempt_repository = attempt_repository
        self.rating_repository = rating_repository
        self.achievement_repository = achievement_repository
        self.user_repository = user_repository
        self.event_bus = event_bus
        self.achievement_service = AchievementService(
            achievement_repository,
            attempt_repository,
            rating_repository,
            test_repository,
        )
        self._subscribe_events()

    def _subscribe_events(self):
        if getattr(self.event_bus, "_skillflow_registered", False):
            return
        self.event_bus.subscribe("TEST_COMPLETED", self._handle_rating_update)
        self.event_bus.subscribe("TEST_COMPLETED", self._handle_achievement_update)
        self.event_bus.subscribe("TEST_PUBLISHED", self._handle_creator_achievement)
        self.event_bus._skillflow_registered = True

    def create_test(self, payload, author_id: int):
        author = self.user_repository.get_by_id(User, author_id)
        if not author:
            raise ValueError("Автор теста не найден")
        if author.role != Role.STUDENT:
            raise ValueError("Создавать тесты может только студент")
        test = Test(
            title=payload.title,
            description=payload.description,
            subject_id=payload.subject_id,
            difficulty=payload.difficulty,
            author_id=author_id,
            status=TestStatus.DRAFT,
        )
        self.test_repository.save(test)
        for index, question_payload in enumerate(payload.questions, start=1):
            factory = QuestionFactory.create(
                question_payload.question_type,
                {
                    "text": question_payload.text,
                    "points": question_payload.points,
                    "options": [option.model_dump() for option in question_payload.options],
                },
            )
            self.test_repository.save(factory.build_model(test.id, index))
        self.test_repository.db.flush()
        return self.test_repository.get_full(test.id)

    def submit_for_moderation(self, test_id: int, current_user):
        test = self.test_repository.get_full(test_id)
        if not test:
            raise ValueError("Тест не найден")
        if test.author_id != current_user.id:
            raise ValueError("Можно отправить только свой тест")
        TestStateMachine(test.status).apply(test, "submit")
        self.test_repository.db.flush()
        return test

    def moderate_test(self, test_id: int, current_user, action: str, comment: str | None):
        if current_user.role != Role.TEACHER:
            raise ValueError("Модерировать тесты может только преподаватель")
        test = self.test_repository.get_full(test_id)
        if not test:
            raise ValueError("Тест не найден")
        allowed_subject_ids = {subject.id for subject in current_user.teaching_subjects}
        if test.subject_id not in allowed_subject_ids:
            raise ValueError("Можно модерировать только тесты по своим дисциплинам")
        machine = TestStateMachine(test.status)
        if action == "approve":
            machine.apply(test, "approve")
            test.moderator_id = current_user.id
            test.moderation_comment = comment
            self.test_repository.db.flush()
            self.event_bus.publish("TEST_PUBLISHED", {"student_id": test.author_id})
        else:
            machine.apply(test, "reject")
            test.moderator_id = current_user.id
            test.moderation_comment = comment or "Нужно доработать вопросы"
            self.test_repository.db.flush()
        return test

    def take_test(self, test_id: int, current_user, answers: list, allow_retake: bool = False):
        if current_user.role != Role.STUDENT:
            raise ValueError("Проходить тесты может только студент")
        test = self.test_repository.get_full(test_id)
        if not test or test.status != TestStatus.PUBLISHED:
            raise ValueError("Опубликованный тест не найден")
        previous_attempt = self.attempt_repository.get_completed_by_student_for_test(current_user.id, test.id)
        if previous_attempt and not allow_retake:
            raise ValueError("Тест уже был пройден. Повторная попытка требует явного подтверждения.")
        answer_map = {item.question_id: sorted(item.selected_option_ids) for item in answers}
        max_score = sum(question.points for question in test.questions)
        attempt = TestAttempt(
            test_id=test.id,
            student_id=current_user.id,
            max_score=max_score,
            status=AttemptStatus.COMPLETED,
            completed_at=datetime.utcnow(),
        )
        self.attempt_repository.save(attempt)

        score = 0
        feedback = []
        for question in sorted(test.questions, key=lambda value: value.sort_order):
            selected_ids = answer_map.get(question.id, [])
            correct_ids = sorted(option.id for option in question.answer_options if option.is_correct)
            is_correct = selected_ids == correct_ids
            points_earned = question.points if is_correct else 0
            score += points_earned
            self.attempt_repository.save(
                UserAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    selected_option_ids=",".join(str(item) for item in selected_ids),
                    is_correct=is_correct,
                    points_earned=points_earned,
                )
            )
            feedback.append(
                {
                    "question_id": question.id,
                    "is_correct": is_correct,
                    "points_earned": points_earned,
                    "selected_option_ids": selected_ids,
                    "correct_option_ids": correct_ids,
                }
            )

        attempt.score = score
        strategy = RatingStrategyFactory.build(test.difficulty)
        rating_delta = strategy.calculate(score, test.difficulty) if current_user.role == Role.STUDENT else 0
        if previous_attempt:
            rating_delta -= previous_attempt.rating_delta
        attempt.rating_delta = rating_delta
        self.attempt_repository.db.flush()
        earned = self.event_bus.publish(
            "TEST_COMPLETED",
            {
                "student_id": current_user.id,
                "subject_id": test.subject_id,
                "test_id": test.id,
                "score": score,
                "max_score": max_score,
                "difficulty": test.difficulty,
                "rating_delta": rating_delta,
            },
        )
        return {
            "attempt_id": attempt.id,
            "score": score,
            "max_score": max_score,
            "percentage": round((score / max_score) * 100, 2) if max_score else 0,
            "rating_delta": rating_delta,
            "earned_achievements": earned,
            "feedback": feedback,
        }

    def _handle_rating_update(self, event):
        payload = event.payload
        self.rating_repository.update_score(payload["student_id"], payload["subject_id"], payload["rating_delta"])
        return []

    def _handle_achievement_update(self, event):
        payload = event.payload
        return self.achievement_service.award_if_needed(
            payload["student_id"],
            payload["subject_id"],
            payload["test_id"],
            payload["score"],
            payload["max_score"],
        )

    def _handle_creator_achievement(self, event):
        payload = event.payload
        return self.achievement_service.award_test_creator(payload["student_id"])

    def build_stats(self, current_user):
        attempts = self.attempt_repository.get_completed_by_student(current_user.id)
        latest_by_test: dict[int, TestAttempt] = {}
        for attempt in attempts:
            if attempt.test_id not in latest_by_test:
                latest_by_test[attempt.test_id] = attempt
        unique_attempts = list(latest_by_test.values())
        ratings = self.rating_repository.get_leaderboard()
        my_ratings = [item for item in ratings if item.student_id == current_user.id]
        subject_breakdown = {item.subject.name: item.total_score for item in my_ratings}
        total_score = sum(item.total_score for item in my_ratings)
        avg = (
            round(sum((item.score / item.max_score) * 100 for item in unique_attempts if item.max_score) / len(unique_attempts), 2)
            if unique_attempts
            else 0
        )
        latest = [
            {
                "test_title": item.test.title,
                "subject_name": item.test.subject.name,
                "score": item.score,
                "max_score": item.max_score,
                "completed_at": item.completed_at.isoformat() if item.completed_at else None,
            }
            for item in unique_attempts[:5]
        ]
        return {
            "tests_completed": len(unique_attempts),
            "average_score_percent": avg,
            "rating_total": total_score,
            "subject_breakdown": subject_breakdown,
            "latest_attempts": latest,
        }
