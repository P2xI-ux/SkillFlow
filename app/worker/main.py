import asyncio
import logging

from aiogram import Bot
from arq.connections import RedisSettings
from app.core.config import settings

# Force default asyncio event loop policy to avoid issues with uvloop in arq worker.
# We do this after imports to override any event loop policy changes made by imported modules (e.g., aiogram or uvloop).
asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

logger = logging.getLogger(__name__)


async def send_telegram_notification(ctx, telegram_id: str, message: str) -> bool:
    logger.info(f"Worker received request to send notification to {telegram_id}: {message}")
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not configured, skipping telegram message")
        return False

    bot = Bot(token=settings.telegram_bot_token)
    try:
        await bot.send_message(chat_id=telegram_id, text=message)
        logger.info(f"Successfully sent telegram notification to {telegram_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send telegram notification to {telegram_id}: {e}")
        return False
    finally:
        await bot.session.close()


async def startup(ctx):
    logger.info("Worker starting up...")


async def shutdown(ctx):
    logger.info("Worker shutting down...")


# Configure Redis settings for arq
redis_settings = RedisSettings.from_dsn(settings.redis_url)


class WorkerSettings:
    functions = [send_telegram_notification]
    redis_settings = redis_settings
    on_startup = startup
    on_shutdown = shutdown
