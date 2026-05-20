import httpx
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.adapter import adapter
from bot.keyboards.inline import test_start_keyboard
from bot.states.testing import state_storage

router = Router()


@router.message(Command("tests"))
async def cmd_tests(message: Message) -> None:
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


@router.message(Command("mytests"))
async def cmd_mytests(message: Message) -> None:
    telegram_id = str(message.from_user.id)
    try:
        items = await adapter.fetch_tests(telegram_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            await message.answer(
                "🔐 Сначала выполните /link <code>&lt;код&gt;</code>.", parse_mode="HTML"
            )
            return
        await message.answer("❌ Не удалось получить ваши тесты.")
        return

    attempted = [i for i in items if i.get("attempted")]
    if not attempted:
        await message.answer("📭 У вас пока нет пройденных тестов.")
        return

    lines = ["<b>✅ Пройденные тесты:</b>\n"]
    for item in attempted[:15]:
        lines.append(f"• <b>#{item['id']}</b> {item['title']} — <i>{item['subject_name']}</i>")
    lines.append("\nДля повторного прохождения: /retake <code>&lt;id&gt;</code>")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("open"))
async def cmd_open(message: Message) -> None:
    parts = message.text.split(maxsplit=1) if message.text else []
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer(
            "❌ Используйте: /open <code>&lt;id_теста&gt;</code>", parse_mode="HTML"
        )
        return

    test_id = int(parts[1].strip())
    telegram_id = str(message.from_user.id)
    try:
        test = await adapter.fetch_test_detail(test_id, telegram_id)
        tests_list = await adapter.fetch_tests(telegram_id)
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

    already_attempted = any(
        item.get("id") == test_id and item.get("attempted") for item in tests_list
    )
    msg = (
        f"🎯 <b>{test['title']}</b>\n\n"
        f"📝 {test['description'] or 'Без описания'}\n\n"
        f"📖 <b>Предмет:</b> {test['subject_name']}\n"
        f"⚙️ <b>Сложность:</b> {test['difficulty']}\n"
        f"❓ <b>Вопросов:</b> {len(test['questions'])}"
    )

    keyboard = test_start_keyboard(already_attempted, test_id)
    await message.answer(msg, reply_markup=keyboard, parse_mode="HTML")


@router.message(Command("retake"))
async def cmd_retake(message: Message) -> None:
    parts = message.text.split(maxsplit=1) if message.text else []
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer(
            "❌ Используйте: /retake <code>&lt;id_теста&gt;</code>", parse_mode="HTML"
        )
        return

    test_id = int(parts[1].strip())
    telegram_id = str(message.from_user.id)
    try:
        test = await adapter.fetch_test_detail(test_id, telegram_id)
    except httpx.HTTPStatusError:
        await message.answer("❓ Тест не найден или недоступен.")
        return

    await message.answer(
        f"⚠️ Вы запускаете повторное прохождение теста <b>{test['title']}</b>.\n"
        "Подтвердите: /confirm_retake или отмените: /cancel",
        parse_mode="HTML",
    )
    await state_storage.set_pending_retake(message.from_user.id, test_id, test["questions"])


@router.message(Command("rating"))
async def cmd_rating(message: Message) -> None:
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


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
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
