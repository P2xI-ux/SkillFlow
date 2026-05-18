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
def university_catalog():
    return get_catalog_payload()
