from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.entities import Rating
from app.repositories.rating_repository import RatingRepository


def test_rating_repository_recalculates_positions_after_updates():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        repo = RatingRepository(db)
        repo.update_score(student_id=1, subject_id=1, delta=10)
        repo.update_score(student_id=2, subject_id=1, delta=20)
        repo.update_score(student_id=3, subject_id=1, delta=15)
        db.commit()

        rows = db.query(Rating).filter(Rating.subject_id == 1).order_by(Rating.position.asc()).all()
        assert [r.student_id for r in rows] == [2, 3, 1]
        assert [r.position for r in rows] == [1, 2, 3]
    finally:
        db.close()
