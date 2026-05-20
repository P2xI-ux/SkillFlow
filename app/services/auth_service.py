from sqlalchemy import select

from app.core.security import create_access_token, get_password_hash, verify_password
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
        faculty_id = payload.faculty_id
        department_id = None
        program_id = None
        admission_year = None

        if payload.role == Role.TEACHER:
            if payload.study_group or payload.admission_year or payload.program_id:
                raise ValueError("Преподавателю нельзя указывать студенческие поля профиля")
            if not payload.department_id:
                raise ValueError("Для преподавателя необходимо выбрать кафедру")
            
            from app.models.entities import Department
            department = self.user_repository.db.scalar(
                select(Department).where(Department.id == payload.department_id)
            )
            if not department:
                raise ValueError("Указанная кафедра не найдена")
            
            if faculty_id and department.faculty_id != faculty_id:
                raise ValueError(
                    f"Кафедра {department.code} не относится к выбранному институту"
                )
            faculty_id = department.faculty_id
            department_id = department.id

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
            if payload.department_id or payload.subject_ids:
                raise ValueError("Студенту нельзя указывать преподавательские поля профиля")
            if not payload.program_id:
                raise ValueError("Для студента необходимо выбрать направление подготовки")
            
            from app.models.entities import Program
            program = self.user_repository.db.scalar(
                select(Program).where(Program.id == payload.program_id)
            )
            if not program:
                raise ValueError("Указанное направление не найдено")
            
            if faculty_id and program.faculty_id != faculty_id:
                raise ValueError(
                    f"Направление {program.code} не относится к выбранному институту"
                )
            faculty_id = program.faculty_id
            program_id = program.id
            department_id = program.department_id
            admission_year = payload.admission_year

        user = User(
            email=email,
            password_hash=get_password_hash(payload.password),
            full_name=payload.full_name,
            role=payload.role,
            faculty_id=faculty_id,
            department_id=department_id,
            program_id=program_id,
            study_group=payload.study_group,
            admission_year=admission_year,
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
