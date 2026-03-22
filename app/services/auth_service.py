from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.entities import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register(self, payload):
        if self.user_repository.get_by_email(payload.email):
            raise ValueError("Пользователь с таким email уже существует")
        user = User(
            email=payload.email,
            password_hash=get_password_hash(payload.password),
            full_name=payload.full_name,
            role=payload.role,
            faculty=payload.faculty,
            study_group=payload.study_group,
            course=payload.course,
            department=payload.department,
        )
        self.user_repository.save(user)
        token = create_access_token(str(user.id))
        return token, user

    def login(self, payload):
        user = self.user_repository.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise ValueError("Неверный email или пароль")
        return create_access_token(str(user.id)), user
