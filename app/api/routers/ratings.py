from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.rating_repository import RatingRepository

router = APIRouter(tags=["ratings"])


@router.get("/ratings")
def ratings(subject_id: int | None = None, db: Session = Depends(get_db)):
    leaderboard = RatingRepository(db).get_leaderboard(subject_id)
    return [
        {
            "student_name": item.student.full_name,
            "total_score": item.total_score,
            "position": item.position,
            "subject_name": item.subject.name,
            "faculty": item.student.faculty_rel.short_name if item.student.faculty_rel else None,
        }
        for item in leaderboard
    ]
