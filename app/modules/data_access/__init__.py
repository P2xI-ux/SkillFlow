"""Data Access module.

Содержимое модуля:
- Repository base class
- concrete repositories for users, tests, attempts, ratings, achievements
"""

from app.repositories.achievement_repository import AchievementRepository
from app.repositories.attempt_repository import AttemptRepository
from app.repositories.base import Repository
from app.repositories.rating_repository import RatingRepository
from app.repositories.test_repository import TestRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "Repository",
    "UserRepository",
    "TestRepository",
    "AttemptRepository",
    "RatingRepository",
    "AchievementRepository",
]
