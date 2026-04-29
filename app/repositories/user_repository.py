from datetime import datetime

from sqlalchemy import select

from app.models.entities import User
from app.repositories.base import Repository


class UserRepository(Repository):
    def get_by_email(self, email: str):
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_telegram_id(self, telegram_id: str):
        return self.db.scalar(select(User).where(User.telegram_id == telegram_id))

    def get_by_link_code(self, code: str):
        return self.db.scalar(select(User).where(User.telegram_link_code == code))

    def get_by_active_link_code(self, code: str):
        return self.db.scalar(
            select(User).where(
                User.telegram_link_code == code,
                User.telegram_link_code_expires_at.is_not(None),
                User.telegram_link_code_expires_at > datetime.utcnow(),
            )
        )

    def list_students(self):
        return self.db.scalars(select(User).where(User.role == "STUDENT")).all()
