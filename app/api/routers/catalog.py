from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.university_catalog import get_catalog_payload
from app.models.entities import Subject
from app.schemas import SubjectResponse

router = APIRouter(tags=["catalog"])


@router.get("/subjects", response_model=list[SubjectResponse])
def list_subjects(db: Session = Depends(get_db)):
    return db.scalars(select(Subject).order_by(Subject.name.asc())).all()


@router.get("/university/catalog")
def university_catalog(db: Session = Depends(get_db)):
    from app.models.entities import Faculty, Department, Program

    faculties = db.scalars(select(Faculty)).all()
    payload = []
    for faculty in faculties:
        departments = db.scalars(
            select(Department).where(Department.faculty_id == faculty.id)
        ).all()
        programs = db.scalars(
            select(Program).where(Program.faculty_id == faculty.id)
        ).all()

        payload.append({
            "id": faculty.id,
            "full_name": faculty.full_name,
            "short_name": faculty.short_name,
            "departments": [
                {"id": dept.id, "name": dept.name, "code": dept.code}
                for dept in departments
            ],
            "programs": [
                {"id": prog.id, "name": prog.name, "code": prog.code}
                for prog in programs
            ]
        })
    return payload
