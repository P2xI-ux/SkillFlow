import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from app.core.config import settings
from app.services.telegram_adapter import TelegramAdapter

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", settings.telegram_bot_token)
API_BASE_URL = os.getenv("API_BASE_URL", settings.api_base_url)
adapter = TelegramAdapter(API_BASE_URL)
user_tokens: dict[str, str] = {}


def format_tests(items: list[dict]) -> str:
    if not items:
        return "Пока нет опубликованных тестов."
    return "\n".join(f"• {item['title']} ({item['subject_name']}, сложность {item['difficulty']})" for item in items[:10])


async def start(message: Message):
    await message.answer(
        "Привет! Я SkillFlow Bot. Команды: /tests, /rating, /link <код>, /token <jwt>, /stats."
    )


async def tests(message: Message):
    items = await adapter.fetch_tests()
    await message.answer(format_tests(items))


async def rating(message: Message):
    items = await adapter.fetch_rating()
    if not items:
        await message.answer("Рейтинг пока пуст.")
        return
    top = "\n".join(f"#{item['position']} {item['student_name']} — {item['total_score']} ({item['subject_name']})" for item in items[:10])
    await message.answer(top)


async def token(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Используй /token <jwt_токен> из веб-приложения.")
        return
    user_tokens[str(message.from_user.id)] = parts[1].strip()
    await message.answer("JWT сохранён. Теперь доступна команда /stats.")


async def stats(message: Message):
    token_value = user_tokens.get(str(message.from_user.id))
    if not token_value:
        await message.answer("Сначала отправь /token <jwt_токен> или используй веб для привязки.")
        return
    stats_payload = await adapter.fetch_stats(token_value)
    await message.answer(
        f"Пройдено: {stats_payload['tests_completed']}\n"
        f"Средний результат: {stats_payload['average_score_percent']}%\n"
        f"Рейтинг: {stats_payload['rating_total']}"
    )


async def link(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Используй /link <6-значный код>.")
        return
    result = await adapter.connect_account(parts[1].strip(), str(message.from_user.id))
    await message.answer(f"Аккаунт {result['email']} привязан к Telegram.")


async def main():
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN не задан. Бот не запущен.")
        return
    dp = Dispatcher()
    dp.message.register(start, Command("start", "help"))
    dp.message.register(tests, Command("tests"))
    dp.message.register(rating, Command("rating"))
    dp.message.register(token, Command("token"))
    dp.message.register(stats, Command("stats"))
    dp.message.register(link, Command("link"))

    bot = Bot(BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
