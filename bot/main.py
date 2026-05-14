import asyncio
import json
import os

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from aiogram.client.session.aiohttp import AiohttpSession

from app.core.config import settings
from app.services.telegram_adapter import TelegramAdapter

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", settings.telegram_bot_token)
API_BASE_URL = os.getenv("API_BASE_URL", settings.api_base_url)
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL")

session = AiohttpSession(proxy=TELEGRAM_PROXY_URL) if TELEGRAM_PROXY_URL else AiohttpSession()

adapter = TelegramAdapter(API_BASE_URL)


class TestPassStates(StatesGroup):
    answering = State()


async def start(message: Message):
    await message.answer(
        "Привет! Я SkillFlow Bot. Команды: /tests, /rating, /link <код>, /stats."
    )


async def tests(message: Message):
    telegram_id = str(message.from_user.id)
    try:
        items = await adapter.fetch_tests(telegram_id)
    except httpx.HTTPStatusError:
        items = await adapter.fetch_tests()

    if not items:
        await message.answer("Пока нет опубликованных тестов.")
        return
    lines = []
    for item in items[:10]:
        marker = " ✅" if item.get("attempted") else ""
        lines.append(
            f"• #{item['id']} {item['title']} ({item['subject_name']}, сложность {item['difficulty']}){marker}"
        )
    await message.answer("\n".join(lines) + "\n\nОткрыть тест: /open <id>")


async def open_test(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("Используйте /open <id_теста>.")
        return

    test_id = int(parts[1].strip())
    telegram_id = str(message.from_user.id)
    try:
        test = await adapter.fetch_test_detail(test_id, telegram_id)
    except httpx.HTTPStatusError:
        await message.answer(
            "Тест не найден или у вас нет доступа. Возможно, нужно выполнить /link."
        )
        return

    # Check if attempted in the list (fetch_tests has attempted flag, detail might not)
    # For simplicity, we just offer to start.
    msg = f"<b>{test['title']}</b>\n{test['description']}\n\nПредмет: {test['subject_name']}\nСложность: {test['difficulty']}\nВопросов: {len(test['questions'])}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Начать прохождение", callback_data=f"test:start:{test_id}"
                )
            ],
        ]
    )
    await message.answer(msg, reply_markup=keyboard, parse_mode="HTML")


async def test_start_callback(callback_query: CallbackQuery, state: FSMContext):
    _, action, test_id = callback_query.data.split(":")
    telegram_id = str(callback_query.from_user.id)

    try:
        test = await adapter.fetch_test_detail(int(test_id), telegram_id)
    except httpx.HTTPStatusError:
        await callback_query.answer("Ошибка доступа к тесту", show_alert=True)
        return

    await state.set_state(TestPassStates.answering)
    await state.update_data(
        test_id=int(test_id),
        questions=test["questions"],
        current_index=0,
        user_answers=[],
    )

    await send_question(
        callback_query.message, test["questions"][0], 0, len(test["questions"])
    )
    await callback_query.answer()


async def send_question(message: Message, question, index: int, total: int):
    text = f"Вопрос {index + 1} из {total}:\n\n{question['text']}"

    keyboard_btns = []
    if (
        question["question_type"] == "SINGLE_CHOICE"
        or question["question_type"] == "MULTIPLE_CHOICE"
    ):
        for opt in question["options"]:
            keyboard_btns.append(
                [
                    InlineKeyboardButton(
                        text=opt["text"], callback_data=f"ans:{opt['id']}"
                    )
                ]
            )
    elif question["question_type"] == "TEXT_ANSWER":
        text += "\n\n<i>Отправьте текстовый ответ сообщением.</i>"
    elif question["question_type"] == "MATCHING":
        text += "\n\n<i>Этот тип вопроса пока доступен только в веб-интерфейсе. Он будет пропущен.</i>"
        keyboard_btns.append(
            [InlineKeyboardButton(text="Пропустить", callback_data="ans:skip")]
        )

    keyboard = (
        InlineKeyboardMarkup(inline_keyboard=keyboard_btns) if keyboard_btns else None
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def handle_answer_callback(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data:
        return

    ans_data = callback_query.data.split(":")[1]
    current_q = data["questions"][data["current_index"]]

    # Simple single/multiple choice handler (treating all as single choice for MVP bot)
    user_answer = {
        "question_id": current_q["id"],
        "selected_option_ids": [int(ans_data)] if ans_data != "skip" else [],
        "text_answer": None,
        "matching_answer": None,
    }

    await process_next_question(callback_query.message, state, user_answer)
    await callback_query.answer()


async def handle_text_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data or await state.get_state() != TestPassStates.answering:
        return

    current_q = data["questions"][data["current_index"]]
    if current_q["question_type"] != "TEXT_ANSWER":
        return

    user_answer = {
        "question_id": current_q["id"],
        "selected_option_ids": [],
        "text_answer": message.text.strip(),
        "matching_answer": None,
    }
    await process_next_question(message, state, user_answer)


async def process_next_question(message: Message, state: FSMContext, last_answer: dict):
    data = await state.get_data()
    user_answers = data["user_answers"]
    user_answers.append(last_answer)

    next_index = data["current_index"] + 1
    if next_index < len(data["questions"]):
        await state.update_data(current_index=next_index, user_answers=user_answers)
        await send_question(
            message, data["questions"][next_index], next_index, len(data["questions"])
        )
    else:
        # Finish test
        await message.answer("⏳ Тест завершен, отправка результатов...")
        telegram_id = str(message.chat.id)
        try:
            result = await adapter.submit_attempt(
                data["test_id"], telegram_id, user_answers, allow_retake=True
            )

            report = (
                f"<b>Результат:</b> {result['score']} / {result['max_score']} ({result['percentage']}%)\n"
                f"Рейтинг: +{result['rating_delta']}\n"
            )
            if result.get("earned_achievements"):
                report += f"\n🏆 <b>Получены достижения:</b>\n" + "\n".join(
                    f"• {a}" for a in result["earned_achievements"]
                )

            await message.answer(report, parse_mode="HTML")
        except httpx.HTTPStatusError as exc:
            await message.answer(f"Ошибка при отправке: {exc.response.text}")

        await state.clear()


async def rating(message: Message):
    items = await adapter.fetch_rating()
    if not items:
        await message.answer("Рейтинг пока пуст.")
        return
    top = "\n".join(
        f"#{item['position']} {item['student_name']} — {item['total_score']} ({item['subject_name']})"
        for item in items[:10]
    )
    await message.answer(top)


async def stats(message: Message):
    telegram_id = str(message.from_user.id)
    try:
        stats_payload = await adapter.fetch_stats(telegram_id)
        await message.answer(
            f"Пройдено: {stats_payload['tests_completed']}\n"
            f"Средний результат: {stats_payload['average_score_percent']}%\n"
            f"Рейтинг: {stats_payload['rating_total']}"
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            await message.answer("Сначала используйте /link <код> из веб-приложения.")
        else:
            await message.answer("Ошибка при получении статистики.")


async def link(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Используйте /link <6-значный код>.")
        return
    try:
        result = await adapter.connect_account(
            parts[1].strip(), str(message.from_user.id)
        )
        await message.answer(f"Аккаунт {result['email']} привязан к Telegram.")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 410:
            await message.answer("Код привязки истёк.")
            return
        if exc.response.status_code == 404:
            await message.answer("Код привязки не найден.")
            return
        raise


async def main():
    if not BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN не задан.")
        return
    dp = Dispatcher()
    dp.message.register(start, Command("start", "help"))
    dp.message.register(tests, Command("tests"))
    dp.message.register(rating, Command("rating"))
    dp.message.register(stats, Command("stats"))
    dp.message.register(link, Command("link"))
<<<<<<< Updated upstream
=======
    dp.message.register(open_test, Command("open"))

    dp.callback_query.register(test_start_callback, F.data.startswith("test:start:"))
    dp.callback_query.register(
        handle_answer_callback, TestPassStates.answering, F.data.startswith("ans:")
    )
    dp.message.register(handle_text_answer, TestPassStates.answering)
>>>>>>> Stashed changes

    bot = Bot(
    token=BOT_TOKEN,
    session=session,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
