from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.models.entities import Question, Test
from app.models.enums import TestStatus
from app.repositories.base import Repository


class TestRepository(Repository):
    def get_full(self, test_id: int):
        stmt = (
            select(Test)
            .where(Test.id == test_id)
            .options(
                joinedload(Test.subject),
                joinedload(Test.author),
                selectinload(Test.questions).selectinload(Question.answer_options),
            )
        )
        return self.db.scalars(stmt).unique().first()

    def _list_base(self):
        return select(Test).options(joinedload(Test.subject), joinedload(Test.author), selectinload(Test.questions))

    def get_published(self, subject_id: int | None = None):
        stmt = self._list_base().where(Test.status == TestStatus.PUBLISHED)
        if subject_id:
            stmt = stmt.where(Test.subject_id == subject_id)
        return self.db.scalars(stmt.order_by(Test.created_at.desc())).unique().all()

    def get_by_author(self, author_id: int):
        stmt = self._list_base().where(Test.author_id == author_id)
        return self.db.scalars(stmt.order_by(Test.created_at.desc())).unique().all()

    def get_pending(self):
        stmt = self._list_base().where(Test.status == TestStatus.PENDING_MODERATION)
        return self.db.scalars(stmt.order_by(Test.created_at.asc())).unique().all()
