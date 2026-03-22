"""Users module.

Содержимое модуля:
- User entity
- AuthService
- dependencies for current user resolution
"""

from app.models.entities import User
from app.services.auth_service import AuthService

__all__ = ["User", "AuthService"]
