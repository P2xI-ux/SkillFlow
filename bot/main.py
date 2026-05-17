import asyncio
import json
import os
from typing import Any

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.core.config import settings
from app.services.telegram_adapter import TelegramAdapter

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", settings.telegram_bot_token)
API_BASE_URL = os.getenv("API_BASE_URL", settings.api_base_url)
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL")

session = (
    AiohttpSession(proxy=TELEGRAM_PROXY_URL) if TELEGRAM_PROXY_URL else AiohttpSession()
)

adapter = TelegramAdapter(API_BASE_URL)


class TestPassStates(StatesGroup):
    answering = State()


async def start(message: Message):
    await message.answer(
        "👋 <b>Привет! Я SkillFlow Bot.</b>\n\n"
        "Я помогу тебе проходить тесты и следить за учебным прогрессом прямо в Telegram.\n\n"
        "<b>Доступные команды:</b>\n"
        "📂 /tests — список доступных тестов\n"
        "📊 /stats — твоя личная статистика\n"
        "🏆 /rating — глобальный рейтинг студентов\n"
        "🔗 /link <code>&lt;код&gt;</code> — привязать аккаунт из веб-версии\n"
        "❓ /help — показать это сообщение",
        parse_mode="HTML",
    )


async def tests(message: Message):
    telegram_id = str(message.from_user.id)
    try:
        items = await adapter.fetch_tests(telegram_id)
    except httpx.HTTPStatusError:
        items = await adapter.fetch_tests()

    if not items:
        await message.answer("📭 Пока нет опубликованных тестов.")
        return

    lines = ["<b>📚 Доступные тесты:</b>\n"]
    for item in items[:10]:
        marker = "✅" if item.get("attempted") else "📝"
        lines.append(
            f"{marker} <b>#{item['id']}</b> {item['title']}\n"
            f"   └ <i>{item['subject_name']} | Сложн: {item['difficulty']}</i>"
        )
    lines.append("\nЧтобы начать, используй: /open <code>&lt;id&gt;</code>")
    await message.answer("\n".join(lines), parse_mode="HTML")


async def open_test(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer(
            "❌ Используйте: /open <code>&lt;id_теста&gt;</code>", parse_mode="HTML"
        )
        return

    test_id = int(parts[1].strip())
    telegram_id = str(message.from_user.id)
    try:
        test = await adapter.fetch_test_detail(test_id, telegram_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            await message.answer(
                "🔐 <b>Доступ ограничен.</b>\n\n"
                "Сначала привяжите свой аккаунт командой /link <code>&lt;код&gt;</code>.\n"
                "Код можно получить в личном кабинете веб-приложения.",
                parse_mode="HTML",
            )
        else:
            await message.answer("❓ Тест не найден или у вас нет к нему доступа.")
        return

    msg = (
        f"🎯 <b>{test['title']}</b>\n\n"
        f"📝 {test['description'] or 'Без описания'}\n\n"
        f"📖 <b>Предмет:</b> {test['subject_name']}\n"
        f"⚙️ <b>Сложность:</b> {test['difficulty']}\n"
        f"❓ <b>Вопросов:</b> {len(test['questions'])}"
    )

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
        await callback_query.answer("❌ Ошибка доступа к тесту", show_alert=True)
        return

    await state.set_state(TestPassStates.answering)
    await state.update_data(
        test_id=int(test_id),
        questions=test["questions"],
        current_index=0,
        user_answers=[],
        current_selection=[],  # For multiple choice
        matching_state={},  # For matching
    )

    await send_question(
        callback_query.message, test["questions"][0], 0, len(test["questions"])
    )
    await callback_query.answer()


async def send_question(
    message: Message, question, index: int, total: int, state: FSMContext = None
):
    text = f"<b>Вопрос {index + 1} из {total}</b>\n\n{question['text']}"
    keyboard_btns = []

    q_type = question["question_type"]

    if q_type == "SINGLE_CHOICE":
        for opt in question["options"]:
            keyboard_btns.append(
                [
                    InlineKeyboardButton(
                        text=opt["text"], callback_data=f"ans:sc:{opt['id']}"
                    )
                ]
            )

    elif q_type == "MULTIPLE_CHOICE":
        data = await state.get_data() if state else {}
        selection = data.get("current_selection", [])
        for opt in question["options"]:
            marker = "🔘" if opt["id"] in selection else "⚪️"
            keyboard_btns.append(
                [
                    InlineKeyboardButton(
                        text=f"{marker} {opt['text']}",
                        callback_data=f"ans:mc:{opt['id']}",
                    )
                ]
            )
        keyboard_btns.append(
            [InlineKeyboardButton(text="✅ Готово", callback_data="ans:mc:done")]
        )
        text += "\n\n<i>Выберите один или несколько вариантов и нажмите «Готово».</i>"

    elif q_type == "TEXT_ANSWER":
        text += "\n\n<i>⌨️ Отправьте текстовый ответ сообщением.</i>"

    elif q_type == "MATCHING":
        data = await state.get_data() if state else {}
        matching_state = data.get("matching_state", {})
        left_items = question["matching_left"]
        options = question["matching_options"]

        # Find first unassigned left item
        current_left = None
        for item in left_items:
            if item not in matching_state:
                current_left = item
                break

        if current_left:
            text += f"\n\n👉 <b>Установите соответствие для:</b> <code>{current_left}</code>"
            for opt in options:
                # Optional: hide already used right options
                # used_rights = set(matching_state.values())
                # if opt in used_rights: continue
                keyboard_btns.append(
                    [InlineKeyboardButton(text=opt, callback_data=f"ans:ma:{opt}")]
                )
        else:
            # All matched, show summary and confirm
            text += "\n\n<b>Ваши пары:</b>\n"
            for l, r in matching_state.items():
                text += f"• {l} ↔️ {r}\n"
            keyboard_btns.append(
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить", callback_data="ans:ma:done"
                    ),
                    InlineKeyboardButton(
                        text="🔄 Сбросить", callback_data="ans:ma:reset"
                    ),
                ]
            )

    keyboard = (
        InlineKeyboardMarkup(inline_keyboard=keyboard_btns) if keyboard_btns else None
    )

    if message.edit_text:
        try:
            await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            # If message is identical, aiogram might throw error
            pass
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def handle_answer_callback(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data or await state.get_state() != TestPassStates.answering:
        return

    parts = callback_query.data.split(":")
    prefix = parts[1]  # sc, mc, ma
    ans_value = parts[2]

    current_q = data["questions"][data["current_index"]]

    # --- Single Choice ---
    if prefix == "sc":
        user_answer = {
            "question_id": current_q["id"],
            "selected_option_ids": [int(ans_value)],
            "text_answer": None,
            "matching_answer": None,
        }
        await process_next_question(callback_query.message, state, user_answer)

    # --- Multiple Choice ---
    elif prefix == "mc":
        selection = data.get("current_selection", [])
        if ans_value == "done":
            user_answer = {
                "question_id": current_q["id"],
                "selected_option_ids": selection,
                "text_answer": None,
                "matching_answer": None,
            }
            await state.update_data(current_selection=[])
            await process_next_question(callback_query.message, state, user_answer)
        else:
            opt_id = int(ans_value)
            if opt_id in selection:
                selection.remove(opt_id)
            else:
                selection.append(opt_id)
            await state.update_data(current_selection=selection)
            await send_question(
                callback_query.message,
                current_q,
                data["current_index"],
                len(data["questions"]),
                state,
            )

    # --- Matching ---
    elif prefix == "ma":
        matching_state = data.get("matching_state", {})
        if ans_value == "done":
            user_answer = {
                "question_id": current_q["id"],
                "selected_option_ids": [],
                "text_answer": None,
                "matching_answer": matching_state,
            }
            await state.update_data(matching_state={})
            await process_next_question(callback_query.message, state, user_answer)
        elif ans_value == "reset":
            await state.update_data(matching_state={})
            await send_question(
                callback_query.message,
                current_q,
                data["current_index"],
                len(data["questions"]),
                state,
            )
        else:
            # Find current left item
            left_items = current_q["matching_left"]
            current_left = None
            for item in left_items:
                if item not in matching_state:
                    current_left = item
                    break

            if current_left:
                matching_state[current_left] = ans_value
                await state.update_data(matching_state=matching_state)
                await send_question(
                    callback_query.message,
                    current_q,
                    data["current_index"],
                    len(data["questions"]),
                    state,
                )

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
        # Use new message for next question to avoid excessive editing of the same message
        await send_question(
            message,
            data["questions"][next_index],
            next_index,
            len(data["questions"]),
            state,
        )
    else:
        # Finish test
        status_msg = await message.answer(
            "⌛ <b>Тест завершен.</b> Отправляем результаты в систему..."
        )
        telegram_id = str(message.chat.id)
        try:
            result = await adapter.submit_attempt(
                data["test_id"], telegram_id, user_answers, allow_retake=False
            )

            report = (
                f"✅ <b>Тест пройден!</b>\n\n"
                f"📊 <b>Результат:</b> {result['score']} / {result['max_score']} ({result['percentage']}%)\n"
                f"📈 <b>Рейтинг:</b> {'+' if result['rating_delta'] >= 0 else ''}{result['rating_delta']}\n"
            )

            if result.get("earned_achievements"):
                report += f"\n🏆 <b>Новые достижения:</b>\n" + "\n".join(
                    f"• {a}" for a in result["earned_achievements"]
                )

            if result.get("feedback"):
                report += f"\n💡 <i>{result['feedback']}</i>"

            await status_msg.edit_text(report, parse_mode="HTML")
        except httpx.HTTPStatusError as exc:
            error_data = exc.response.json()
            error_msg = error_data.get("detail", "Неизвестная ошибка")
            await status_msg.edit_text(
                f"❌ <b>Ошибка при отправке:</b>\n{error_msg}", parse_mode="HTML"
            )

        await state.clear()


async def rating(message: Message):
    try:
        items = await adapter.fetch_rating()
    except Exception:
        await message.answer("❌ Не удалось получить данные рейтинга.")
        return

    if not items:
        await message.answer("📊 Рейтинг пока пуст.")
        return

    lines = ["<b>🏆 Глобальный рейтинг студентов:</b>\n"]
    for item in items[:10]:
        medal = (
            "🥇"
            if item["position"] == 1
            else "🥈"
            if item["position"] == 2
            else "🥉"
            if item["position"] == 3
            else "👤"
        )
        lines.append(f"{medal} <b>{item['position']}. {item['student_name']}</b>")
        lines.append(
            f"   └ <i>{item['total_score']} баллов | {item['subject_name']}</i>"
        )

    await message.answer("\n".join(lines), parse_mode="HTML")


async def stats(message: Message):
    telegram_id = str(message.from_user.id)
    try:
        s = await adapter.fetch_stats(telegram_id)

        msg = (
            f"👤 <b>Твоя статистика:</b>\n\n"
            f"✅ <b>Пройдено тестов:</b> {s['tests_completed']}\n"
            f"🎯 <b>Средний результат:</b> {s['average_score_percent']}%\n"
            f"💎 <b>Суммарный рейтинг:</b> {s['rating_total']}\n\n"
            f"📚 <b>Баллы по предметам:</b>\n"
        )

        if s["subject_breakdown"]:
            for sub, score in s["subject_breakdown"].items():
                msg += f"• {sub}: {score}\n"
        else:
            msg += "<i>Нет данных</i>"

        await message.answer(msg, parse_mode="HTML")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            await message.answer(
                "🔐 Сначала выполните /link <code>&lt;код&gt;</code> из веб-приложения.",
                parse_mode="HTML",
            )
        else:
            await message.answer("❌ Ошибка при получении статистики.")


async def link(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "⌨️ Используйте: /link <code>&lt;6-значный код&gt;</code>", parse_mode="HTML"
        )
        return

    code = parts[1].strip()
    try:
        result = await adapter.connect_account(code, str(message.from_user.id))
        await message.answer(
            f"✅ <b>Успешно!</b>\n\n"
            f"Аккаунт <b>{result['email']}</b> теперь привязан к этому Telegram.\n"
            f"Теперь ты можешь проходить тесты и смотреть статистику.",
            parse_mode="HTML",
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 410:
            await message.answer(
                "❌ <b>Код привязки истёк.</b>\nПолучите новый код в веб-приложении.",
                parse_mode="HTML",
            )
        elif exc.response.status_code == 404:
            await message.answer(
                "❌ <b>Код не найден.</b> Проверьте правильность ввода.",
                parse_mode="HTML",
            )
        else:
            await message.answer("❌ Ошибка при привязке аккаунта.")


async def main():
    if not BOT_TOKEN:
        print("CRITICAL: TELEGRAM_BOT_TOKEN is not set.")
        return

    dp = Dispatcher()

    # Handlers
    dp.message.register(start, Command("start", "help"))
    dp.message.register(tests, Command("tests"))
    dp.message.register(rating, Command("rating"))
    dp.message.register(stats, Command("stats"))
    dp.message.register(link, Command("link"))
    dp.message.register(open_test, Command("open"))

    dp.callback_query.register(test_start_callback, F.data.startswith("test:start:"))
    dp.callback_query.register(
        handle_answer_callback, TestPassStates.answering, F.data.startswith("ans:")
    )
    dp.message.register(handle_text_answer, TestPassStates.answering)

    bot = Bot(token=BOT_TOKEN, session=session)

    print("🤖 SkillFlow Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🤖 Bot stopped.")
