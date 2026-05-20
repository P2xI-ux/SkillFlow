import asyncio
import logging
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.entities import User
from app.repositories.user_repository import UserRepository
from app.core.events import event_bus

logger = logging.getLogger(__name__)

# Global arq Redis pool reference
arq_pool = None


async def init_arq_pool():
    global arq_pool
    try:
        arq_pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        logger.info("Successfully connected to Redis for arq queue")
    except Exception as e:
        logger.error(f"Failed to connect to Redis for arq: {e}. Notifications will not be enqueued.")


async def close_arq_pool():
    global arq_pool
    if arq_pool:
        await arq_pool.close()
        logger.info("Closed Redis connection pool for arq")


def enqueue_notification(telegram_id: str, message: str):
    global arq_pool
    if arq_pool is None:
        logger.warning(f"Arq pool is not initialized. Skipping notification: {message}")
        return
    try:
        asyncio.create_task(arq_pool.enqueue_job("send_telegram_notification", telegram_id, message))
        logger.info(f"Scheduled enqueueing notification for {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to schedule enqueueing job: {e}")


# Event subscription handlers
def handle_test_published(event, service=None):
    payload = event.payload
    student_id = payload.get("student_id")
    if not student_id:
        return []

    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(User, student_id)
        if user and user.telegram_id:
            message = "🎉 Ваш созданный тест был проверен и успешно опубликован модератором!"
            enqueue_notification(user.telegram_id, message)
    except Exception as e:
        logger.error(f"Error in handle_test_published notification handler: {e}")
    finally:
        db.close()
    return []


def handle_test_completed(event, service=None):
    payload = event.payload
    student_id = payload.get("student_id")
    rating_delta = payload.get("rating_delta", 0)
    score = payload.get("score")
    max_score = payload.get("max_score")
    if not student_id:
        return []

    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(User, student_id)
        if user and user.telegram_id:
            sign = "+" if rating_delta >= 0 else ""
            message = (
                f"📝 Вы завершили прохождение теста!\n"
                f"Результат: {score}/{max_score} баллов.\n"
                f"Изменение рейтинга: {sign}{rating_delta}."
            )
            enqueue_notification(user.telegram_id, message)
    except Exception as e:
        logger.error(f"Error in handle_test_completed notification handler: {e}")
    finally:
        db.close()
    return []


def setup_notification_subscriptions():
    event_bus.subscribe("TEST_PUBLISHED", handle_test_published)
    event_bus.subscribe("TEST_COMPLETED", handle_test_completed)
