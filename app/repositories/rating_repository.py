from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.entities import Rating
from app.repositories.base import Repository


class RatingRepository(Repository):
    def get_by_student_subject(self, student_id: int, subject_id: int):
        stmt = select(Rating).where(
            Rating.student_id == student_id, Rating.subject_id == subject_id
        )
        return self.db.scalar(stmt)

    def update_score(self, student_id: int, subject_id: int, delta: float):
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
        stmt = select(Rating).options(
            joinedload(Rating.student), joinedload(Rating.subject)
        )
        if subject_id:
            stmt = stmt.where(Rating.subject_id == subject_id)
        stmt = stmt.order_by(
            Rating.subject_id.asc(),
            Rating.total_score.desc(),
            Rating.last_updated.asc(),
        )
        return self.db.scalars(stmt).unique().all()

    def get_position(self, student_id: int, subject_id: int):
        rating = self.get_by_student_subject(student_id, subject_id)
        return rating.position if rating else None

    def _recalculate_positions(self, subject_id: int):
        # Using a more efficient approach with a single update if possible,
        # but for compatibility across DBs, we'll fetch IDs and positions.
        # However, we can use a CTE and RANK() to do it more efficiently.
        from sqlalchemy import text

        sql = text("""
            UPDATE ratings
            SET position = sub.new_pos
            FROM (
                SELECT id, RANK() OVER (
                    ORDER BY total_score DESC, last_updated ASC
                ) as new_pos
                FROM ratings
                WHERE subject_id = :subject_id
            ) as sub
            WHERE ratings.id = sub.id
        """)

        # SQLite doesn't support UPDATE FROM, so we use a fallback for SQLite
        # or just use the more efficient approach for the specific DB.
        # For now, let's use the list-based approach but optimized for bulk update if possible.
        # Actually, let's stick to a clean SQLAlchemy approach that is relatively efficient.

        stmt = (
            select(Rating.id)
            .where(Rating.subject_id == subject_id)
            .order_by(Rating.total_score.desc(), Rating.last_updated.asc())
        )
        rating_ids = self.db.scalars(stmt).all()

        if not rating_ids:
            return

        ratings = self.db.scalars(select(Rating).where(Rating.id.in_(rating_ids))).all()
        by_id = {item.id: item for item in ratings}
        for index, r_id in enumerate(rating_ids, start=1):
            by_id[r_id].position = index

        self.db.flush()
