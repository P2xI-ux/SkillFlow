"""Integration module.

Содержимое модуля:
- TelegramAdapter
- Telegram bot entrypoint is located in bot/main.py
"""

from app.services.telegram_adapter import TelegramAdapter

__all__ = ["TelegramAdapter"]
