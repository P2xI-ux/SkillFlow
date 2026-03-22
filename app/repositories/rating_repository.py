from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.entities import Rating
from app.repositories.base import Repository


class RatingRepository(Repository):
    def get_by_student_subject(self, student_id: int, subject_id: int):
        stmt = select(Rating).where(Rating.student_id == student_id, Rating.subject_id == subject_id)
        return self.db.scalar(stmt)

    def update_score(self, student_id: int, subject_id: int, delta: int):
        rating = self.get_by_student_subject(student_id, subject_id)
        if not rating:
            rating = Rating(student_id=student_id, subject_id=subject_id, total_score=0)
            self.save(rating)
        rating.total_score += delta
        rating.last_updated = datetime.utcnow()
        self.db.flush()
        self._recalculate_positions(subject_id)
        return rating

    def get_leaderboard(self, subject_id: int | None = None):
        stmt = select(Rating).options(joinedload(Rating.student), joinedload(Rating.subject))
        if subject_id:
            stmt = stmt.where(Rating.subject_id == subject_id)
        stmt = stmt.order_by(Rating.subject_id.asc(), Rating.total_score.desc(), Rating.last_updated.asc())
        return self.db.scalars(stmt).unique().all()

    def get_position(self, student_id: int, subject_id: int):
        rating = self.get_by_student_subject(student_id, subject_id)
        return rating.position if rating else None

    def _recalculate_positions(self, subject_id: int):
        ratings = self.db.scalars(
            select(Rating).where(Rating.subject_id == subject_id).order_by(Rating.total_score.desc(), Rating.last_updated.asc())
        ).all()
        for index, item in enumerate(ratings, start=1):
            item.position = index
        self.db.flush()
