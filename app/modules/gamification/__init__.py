"""Gamification module.

Содержимое модуля:
- Rating, Achievement, UserAchievement
- EventBus (Observer)
- RatingStrategy hierarchy (Strategy)
- AchievementService
"""

from app.models.entities import Achievement, Rating, UserAchievement
from app.services.achievement_service import AchievementService
from app.services.event_bus import EventBus
from app.services.rating_strategy import (
    BonusStrategy,
    FirstAttemptStrategy,
    RatingContext,
    RatingStrategy,
    RatingStrategyFactory,
    StandardStrategy,
    TournamentStrategy,
)

__all__ = [
    "Rating",
    "Achievement",
    "UserAchievement",
    "EventBus",
    "AchievementService",
    "RatingStrategy",
    "StandardStrategy",
    "BonusStrategy",
    "FirstAttemptStrategy",
    "RatingContext",
    "TournamentStrategy",
    "RatingStrategyFactory",
]
