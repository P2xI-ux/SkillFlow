import random
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.errors import api_error
from app.core.config import settings
from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.entities import User
from app.repositories.user_repository import UserRepository
from app.schemas import TelegramConnectRequest, TelegramLinkResponse

router = APIRouter(prefix="/telegram", tags=["telegram"])


def generate_telegram_link_code(
    user_repo: UserRepository, max_attempts: int = 20
) -> str:
    for _ in range(max_attempts):
        code = "".join(random.choices(string.digits, k=6))
        if not user_repo.get_by_link_code(code):
            return code
    raise api_error(
        503,
        "LINK_CODE_UNAVAILABLE",
        "Не удалось сгенерировать Telegram link code. Попробуйте позже",
    )


@router.post("/link-code", response_model=TelegramLinkResponse)
def create_link_code(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.telegram_id:
        raise api_error(409, "TELEGRAM_ALREADY_LINKED", "Аккаунт уже привязан к Telegram")

    user_repo = UserRepository(db)
    now = datetime.utcnow()
    if (
        current_user.telegram_link_code
        and current_user.telegram_link_code_expires_at
        and current_user.telegram_link_code_expires_at > now
    ):
        return {
            "code": current_user.telegram_link_code,
            "expires_at": current_user.telegram_link_code_expires_at,
            "ttl_seconds": max(
                0,
                int((current_user.telegram_link_code_expires_at - now).total_seconds()),
            ),
        }

    current_user.telegram_link_code = generate_telegram_link_code(user_repo)
    current_user.telegram_link_code_created_at = now
    current_user.telegram_link_code_expires_at = now + timedelta(
        seconds=settings.telegram_link_code_ttl_seconds
    )
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {
        "code": current_user.telegram_link_code,
        "expires_at": current_user.telegram_link_code_expires_at,
        "ttl_seconds": settings.telegram_link_code_ttl_seconds,
    }


@router.post("/connect")
def connect_telegram(payload: TelegramConnectRequest, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    existing_user = user_repo.get_by_telegram_id(payload.telegram_id)
    if existing_user:
        raise api_error(409, "TELEGRAM_ALREADY_LINKED", "Telegram аккаунт уже привязан")
    user = user_repo.get_by_active_link_code(payload.code)
    if not user:
        expired_user = user_repo.get_by_link_code(payload.code)
        if expired_user:
            expired_user.telegram_link_code = None
            expired_user.telegram_link_code_created_at = None
            expired_user.telegram_link_code_expires_at = None
            db.add(expired_user)
            db.commit()
            raise api_error(410, "LINK_CODE_EXPIRED", "Telegram link code expired")
        raise api_error(404, "LINK_CODE_NOT_FOUND", "Telegram link code not found")
    user.telegram_id = payload.telegram_id
    user.telegram_link_code = None
    user.telegram_link_code_created_at = None
    user.telegram_link_code_expires_at = None
    db.add(user)
    db.commit()
    return {"status": "connected", "email": user.email}
