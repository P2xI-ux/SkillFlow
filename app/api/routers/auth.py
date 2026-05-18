from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.errors import validation_error
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas import TokenResponse, UserLogin, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    try:
        token, user = AuthService(UserRepository(db)).register(payload)
        db.commit()
        db.refresh(user)
        return {"access_token": token, "user": user}
    except ValueError as exc:
        db.rollback()
        raise validation_error(exc) from exc


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    try:
        token, user = AuthService(UserRepository(db)).login(payload)
        return {"access_token": token, "user": user}
    except ValueError as exc:
        raise validation_error(exc) from exc
