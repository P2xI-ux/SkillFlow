import asyncio
import os

from aiohttp import ClientError
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp_socks import ProxyConnectionError

from app.core.config import settings
from bot.handlers import base_router, tests_router, testing_process_router

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", settings.telegram_bot_token)
TELEGRAM_PROXY_URL = (os.getenv("TELEGRAM_PROXY_URL") or "").strip()

session = (
    AiohttpSession(proxy=TELEGRAM_PROXY_URL)
    if TELEGRAM_PROXY_URL
    else AiohttpSession()
)


async def main() -> None:
    if not BOT_TOKEN:
        print("CRITICAL: TELEGRAM_BOT_TOKEN is not set.")
        return

    dp = Dispatcher()

    # Register modular routers
    dp.include_router(base_router)
    dp.include_router(tests_router)
    dp.include_router(testing_process_router)

    bot = Bot(token=BOT_TOKEN, session=session)

    print(
        "🤖 SkillFlow Bot started..."
        + (
            " Telegram proxy is enabled."
            if TELEGRAM_PROXY_URL
            else " Telegram proxy is disabled."
        )
    )

    while True:
        try:
            await dp.start_polling(bot)
        except (
            ClientError,
            ProxyConnectionError,
            OSError,
            asyncio.TimeoutError,
        ) as exc:
            print(
                f"Telegram connection failed: {exc}. Retrying in 15 seconds..."
            )
            await asyncio.sleep(15)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🤖 Bot stopped.")
