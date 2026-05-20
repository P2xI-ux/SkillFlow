import httpx
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.adapter import adapter
from bot.utils import extract_api_error

router = Router()


@router.message(Command("start", "help"))
async def cmd_start(message: Message) -> None:
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


@router.message(Command("link"))
async def cmd_link(message: Message) -> None:
    parts = message.text.split(maxsplit=1) if message.text else []
    if len(parts) < 2:
        await message.answer(
            "⌨️ Используйте: /link <code>&lt;6-значный код&gt;</code>", parse_mode="HTML"
        )
        return

    code = parts[1].strip()
    if not (len(code) == 6 and code.isdigit()):
        await message.answer("❌ Код должен состоять из 6 цифр.")
        return

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
        elif exc.response.status_code == 409:
            await message.answer("⚠️ Этот Telegram уже привязан к другому аккаунту.")
        else:
            error_msg = extract_api_error(exc)
            await message.answer(f"❌ Ошибка при привязке аккаунта: {error_msg}")
    except Exception as exc:
        await message.answer(f"❌ Произошла ошибка: {exc}")
