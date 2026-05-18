from sqlalchemy.orm import Session

from app.core.events import event_bus
from app.repositories.achievement_repository import AchievementRepository
from app.repositories.attempt_repository import AttemptRepository
from app.repositories.rating_repository import RatingRepository
from app.repositories.test_repository import TestRepository
from app.repositories.user_repository import UserRepository
from app.services.test_service import TestService


def get_test_service(db: Session) -> TestService:
    return TestService(
        TestRepository(db),
        AttemptRepository(db),
        RatingRepository(db),
        AchievementRepository(db),
        UserRepository(db),
        event_bus,
    )
