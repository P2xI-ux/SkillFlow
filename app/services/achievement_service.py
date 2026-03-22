from app.models.entities import UserAchievement
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.attempt_repository import AttemptRepository
from app.repositories.rating_repository import RatingRepository
from app.repositories.test_repository import TestRepository


class AchievementService:
    def __init__(
        self,
        achievement_repository: AchievementRepository,
        attempt_repository: AttemptRepository,
        rating_repository: RatingRepository,
        test_repository: TestRepository,
    ):
        self.achievement_repository = achievement_repository
        self.attempt_repository = attempt_repository
        self.rating_repository = rating_repository
        self.test_repository = test_repository

    def award_if_needed(self, student_id: int, subject_id: int, test_id: int, score: int, max_score: int) -> list[str]:
        earned: list[str] = []
        all_achievements = {item.code: item for item in self.achievement_repository.get_all()}
        user_achievements = self.achievement_repository.get_user_achievements(student_id)
        unlocked_codes = {item.achievement.code for item in user_achievements}
        completed_attempts = self.attempt_repository.get_completed_by_student(student_id)

        if "FIRST_TEST" in all_achievements and len(completed_attempts) >= 1:
            if self._grant(student_id, all_achievements["FIRST_TEST"].code, all_achievements, unlocked_codes):
                earned.append(all_achievements["FIRST_TEST"].name)

        if "PERFECT_SCORE" in all_achievements and max_score and score == max_score:
            if self._grant(student_id, all_achievements["PERFECT_SCORE"].code, all_achievements, unlocked_codes):
                earned.append(all_achievements["PERFECT_SCORE"].name)

        if "STREAK_3" in all_achievements and len(completed_attempts) >= 3:
            if all(item.score == item.max_score for item in completed_attempts[:3]):
                if self._grant(student_id, all_achievements["STREAK_3"].code, all_achievements, unlocked_codes):
                    earned.append(all_achievements["STREAK_3"].name)

        if "SUBJECT_MASTER" in all_achievements:
            position = self.rating_repository.get_position(student_id, subject_id)
            if position and position <= 3:
                if self._grant(student_id, all_achievements["SUBJECT_MASTER"].code, all_achievements, unlocked_codes):
                    earned.append(all_achievements["SUBJECT_MASTER"].name)

        return earned

    def award_test_creator(self, student_id: int) -> list[str]:
        all_achievements = {item.code: item for item in self.achievement_repository.get_all()}
        user_achievements = self.achievement_repository.get_user_achievements(student_id)
        unlocked_codes = {item.achievement.code for item in user_achievements}
        if "TEST_CREATOR" in all_achievements and self._grant(student_id, "TEST_CREATOR", all_achievements, unlocked_codes):
            return [all_achievements["TEST_CREATOR"].name]
        return []

    def _grant(self, student_id: int, achievement_code: str, all_achievements: dict, unlocked_codes: set[str]) -> bool:
        if achievement_code in unlocked_codes:
            return False
        achievement = all_achievements[achievement_code]
        if self.achievement_repository.has_achievement(student_id, achievement.id):
            return False
        self.achievement_repository.save(UserAchievement(student_id=student_id, achievement_id=achievement.id))
        unlocked_codes.add(achievement_code)
        return True
