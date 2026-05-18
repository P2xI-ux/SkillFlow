from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_test_service
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.repositories.achievement_repository import AchievementRepository
from app.schemas import AchievementResponse, StatsResponse, UserResponse

router = APIRouter(tags=["profile"])


@router.get("/users/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/achievements/me", response_model=list[AchievementResponse])
def my_achievements(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    items = AchievementRepository(db).get_user_achievements(current_user.id)
    return [
        {
            "code": item.achievement.code,
            "name": item.achievement.name,
            "description": item.achievement.description,
            "earned_at": item.earned_at,
        }
        for item in items
    ]


@router.get("/stats/me", response_model=StatsResponse)
def my_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return get_test_service(db).build_stats(current_user)
