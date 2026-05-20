from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.entities import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def verify_internal_service_token(x_service_token: str | None = Header(default=None)):
    if not settings.internal_service_token:
        return
    if x_service_token != settings.internal_service_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal service token"
        )


def get_current_user(
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
    x_telegram_id: str | None = Header(default=None),
    x_bot_token: str | None = Header(default=None),
    x_service_token: str | None = Header(default=None),
) -> User:
    # 1. Try Bot/Service Authentication
    is_bot_auth = False
    if x_telegram_id:
        if settings.internal_service_token and x_service_token == settings.internal_service_token:
            is_bot_auth = True
        elif settings.telegram_bot_token and x_bot_token == settings.telegram_bot_token:
            is_bot_auth = True

    if is_bot_auth:
        user = UserRepository(db).get_by_telegram_id(x_telegram_id)
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram user not linked"
        )

    # 2. Try Standard JWT Authentication
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    user = UserRepository(db).get_by_id(User, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


def get_current_user_optional(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_telegram_id: str | None = Header(default=None),
    x_bot_token: str | None = Header(default=None),
    x_service_token: str | None = Header(default=None),
) -> User | None:
    # 1. Try Bot/Service Authentication
    is_bot_auth = False
    if x_telegram_id:
        if settings.internal_service_token and x_service_token == settings.internal_service_token:
            is_bot_auth = True
        elif settings.telegram_bot_token and x_bot_token == settings.telegram_bot_token:
            is_bot_auth = True

    if is_bot_auth:
        return UserRepository(db).get_by_telegram_id(x_telegram_id)

    # 2. Try Standard JWT Authentication
    if not authorization or not authorization.startswith("Bearer "):
        return None
    user_id = decode_access_token(authorization.replace("Bearer ", ""))
    if not user_id:
        return None
    return UserRepository(db).get_by_id(User, int(user_id))
