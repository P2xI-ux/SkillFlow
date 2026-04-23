from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.entities import Subject, Test, TestAttempt
from app.models.enums import AttemptStatus
from app.repositories.base import Repository


class AttemptRepository(Repository):
    def get_by_student(self, student_id: int):
        stmt = (
            select(TestAttempt)
            .where(TestAttempt.student_id == student_id)
            .options(joinedload(TestAttempt.test).joinedload(Test.subject))
            .order_by(TestAttempt.started_at.desc())
        )
        return self.db.scalars(stmt).unique().all()

    def get_completed_by_student(self, student_id: int):
        stmt = (
            select(TestAttempt)
            .where(TestAttempt.student_id == student_id, TestAttempt.status == AttemptStatus.COMPLETED)
            .options(joinedload(TestAttempt.test).joinedload(Test.subject))
            .order_by(TestAttempt.completed_at.desc())
        )
        return self.db.scalars(stmt).unique().all()

    def get_completed_by_student_for_test(self, student_id: int, test_id: int):
        stmt = (
            select(TestAttempt)
            .where(
                TestAttempt.student_id == student_id,
                TestAttempt.test_id == test_id,
                TestAttempt.status == AttemptStatus.COMPLETED,
            )
            .order_by(TestAttempt.completed_at.desc())
        )
        return self.db.scalars(stmt).first()
