from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.university_catalog import (
    validate_student_profile,
    validate_teacher_profile,
)
from app.models.entities import Subject, User
from app.models.enums import Role
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register(self, payload):
        email = payload.email.strip().lower()
        if self.user_repository.get_by_email(email):
            raise ValueError("Пользователь с таким email уже существует")

        teaching_subjects = []
        faculty = payload.faculty

        if payload.role == Role.TEACHER:
            if payload.study_group or payload.course or payload.program_code:
                raise ValueError("Преподавателю нельзя указывать студенческие поля профиля")
            faculty = validate_teacher_profile(payload.faculty, payload.department)
            if not payload.subject_ids:
                raise ValueError(
                    "Для преподавателя нужно выбрать хотя бы одну дисциплину"
                )
            teaching_subjects = list(
                self.user_repository.db.scalars(
                    select(Subject).where(Subject.id.in_(payload.subject_ids))
                ).all()
            )
            if len(teaching_subjects) != len(set(payload.subject_ids)):
                raise ValueError("Некоторые дисциплины не найдены")

        if payload.role == Role.STUDENT:
            if payload.department or payload.subject_ids:
                raise ValueError("Студенту нельзя указывать преподавательские поля профиля")
            faculty = validate_student_profile(payload.faculty, payload.program_code)

        user = User(
            email=email,
            password_hash=get_password_hash(payload.password),
            full_name=payload.full_name,
            role=payload.role,
            faculty=faculty,
            study_group=payload.study_group,
            course=payload.course,
            department=payload.department,
            program_code=payload.program_code,
            teaching_subjects=teaching_subjects,
        )
        self.user_repository.save(user)
        token = create_access_token(str(user.id))
        return token, user

    def login(self, payload):
        user = self.user_repository.get_by_email(payload.email.strip().lower())
        if not user or not verify_password(payload.password, user.password_hash):
            raise ValueError("Неверный email или пароль")
        return create_access_token(str(user.id)), user
