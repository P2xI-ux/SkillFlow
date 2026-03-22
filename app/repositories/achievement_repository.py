from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.entities import Achievement, UserAchievement
from app.repositories.base import Repository


class AchievementRepository(Repository):
    def get_all(self):
        return self.db.scalars(select(Achievement).order_by(Achievement.id.asc())).all()

    def get_by_code(self, code: str):
        return self.db.scalar(select(Achievement).where(Achievement.code == code))

    def get_user_achievements(self, student_id: int):
        stmt = (
            select(UserAchievement)
            .where(UserAchievement.student_id == student_id)
            .options(joinedload(UserAchievement.achievement))
            .order_by(UserAchievement.earned_at.desc())
        )
        return self.db.scalars(stmt).unique().all()

    def has_achievement(self, student_id: int, achievement_id: int) -> bool:
        stmt = select(UserAchievement).where(
            UserAchievement.student_id == student_id,
            UserAchievement.achievement_id == achievement_id,
        )
        return self.db.scalar(stmt) is not None
