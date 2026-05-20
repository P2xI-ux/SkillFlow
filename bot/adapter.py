import os
from app.core.config import settings
from app.services.telegram_adapter import TelegramAdapter

API_BASE_URL = os.getenv("API_BASE_URL", settings.api_base_url)
adapter = TelegramAdapter(API_BASE_URL)
