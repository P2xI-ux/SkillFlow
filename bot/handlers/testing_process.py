import httpx
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.adapter import adapter
from bot.keyboards.inline import retake_confirm_keyboard
from bot.states.testing import TestPassStates, state_storage
from bot.utils import extract_api_error

router = Router()


async def send_question(
    message: Message,
    question: dict,
    index: int,
    total: int,
    state: FSMContext | None = None,
) -> None:
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
                keyboard_btns.append(
                    [
                        InlineKeyboardButton(
                            text=opt, callback_data=f"ans:ma:{opt}"
                        )
                    ]
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
        InlineKeyboardMarkup(inline_keyboard=keyboard_btns)
        if keyboard_btns
        else None
    )

    try:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def process_next_question(
    message: Message, state: FSMContext, last_answer: dict
) -> None:
    data = await state.get_data()
    user_answers = data["user_answers"]
    user_answers.append(last_answer)

    next_index = data["current_index"] + 1
    if next_index < len(data["questions"]):
        await state.update_data(
            current_index=next_index, user_answers=user_answers
        )
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
        telegram_id = data.get("telegram_id", str(message.chat.id))
        try:
            result = await adapter.submit_attempt(
                data["test_id"],
                telegram_id,
                user_answers,
                allow_retake=data.get("allow_retake", False),
            )

            report = (
                f"✅ <b>Тест пройден!</b>\n\n"
                f"📊 <b>Результат:</b> {result['score']} / {result['max_score']} ({result['percentage']}%)\n"
                f"📈 <b>Рейтинг:</b> {'+' if result['rating_delta'] >= 0 else ''}{result['rating_delta']}\n"
            )

            if result.get("earned_achievements"):
                report += (
                    f"\n🏆 <b>Новые достижения:</b>\n"
                    + "\n".join(f"• {a}" for a in result["earned_achievements"])
                    + "\n"
                )

            if result.get("feedback"):
                report += f"\n💡 <i>{result['feedback']}</i>"

            await status_msg.edit_text(report, parse_mode="HTML")
        except httpx.HTTPStatusError as exc:
            error_msg = extract_api_error(exc)
            await status_msg.edit_text(
                f"❌ <b>Ошибка при отправке:</b>\n{error_msg}", parse_mode="HTML"
            )

        await state.clear()


@router.callback_query(F.data.startswith("test:start:"))
@router.callback_query(F.data.startswith("test:retake:"))
async def test_start_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    _, action, test_id = callback_query.data.split(":")
    telegram_id = str(callback_query.from_user.id)

    try:
        test = await adapter.fetch_test_detail(int(test_id), telegram_id)
    except httpx.HTTPStatusError:
        await callback_query.answer("❌ Ошибка доступа к тесту", show_alert=True)
        return

    if action == "retake":
        await state_storage.set_pending_retake(
            callback_query.from_user.id, int(test_id), test["questions"]
        )
        keyboard = retake_confirm_keyboard(int(test_id))
        await callback_query.message.answer(
            f"⚠️ <b>Повторное прохождение</b>\n\n"
            f"Тест: <b>{test['title']}</b>\n"
            "Новая попытка пересчитает ваш вклад в рейтинг по этому тесту.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        await callback_query.answer()
        return

    await state.set_state(TestPassStates.answering)
    await state.update_data(
        test_id=int(test_id),
        telegram_id=telegram_id,
        questions=test["questions"],
        current_index=0,
        user_answers=[],
        current_selection=[],
        matching_state={},
        allow_retake=False,
    )

    await send_question(
        callback_query.message,
        test["questions"][0],
        0,
        len(test["questions"]),
        state,
    )
    await callback_query.answer()


@router.message(Command("confirm_retake"))
async def cmd_confirm_retake(message: Message, state: FSMContext) -> None:
    pending = await state_storage.pop_pending_retake(message.from_user.id)
    if not pending:
        await message.answer("ℹ️ Нет ожидающего ретейка.")
        return
    await state.set_state(TestPassStates.answering)
    await state.update_data(
        test_id=pending["test_id"],
        telegram_id=str(message.from_user.id),
        questions=pending["questions"],
        current_index=0,
        user_answers=[],
        current_selection=[],
        matching_state={},
        allow_retake=True,
    )
    await send_question(
        message,
        pending["questions"][0],
        0,
        len(pending["questions"]),
        state,
    )


@router.message(Command("cancel"))
async def cmd_cancel_retake(message: Message) -> None:
    await state_storage.pop_pending_retake(message.from_user.id)
    await message.answer("Ок, повторное прохождение отменено.")


@router.callback_query(F.data.startswith("test:confirm_retake:"))
async def confirm_retake_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    pending = await state_storage.pop_pending_retake(
        callback_query.from_user.id
    )
    if not pending:
        await callback_query.answer(
            "Нет ожидающего повторного прохождения", show_alert=True
        )
        return
    await state.set_state(TestPassStates.answering)
    await state.update_data(
        test_id=pending["test_id"],
        telegram_id=str(callback_query.from_user.id),
        questions=pending["questions"],
        current_index=0,
        user_answers=[],
        current_selection=[],
        matching_state={},
        allow_retake=True,
    )
    await send_question(
        callback_query.message,
        pending["questions"][0],
        0,
        len(pending["questions"]),
        state,
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("test:cancel_retake:"))
async def cancel_retake_callback(callback_query: CallbackQuery) -> None:
    await state_storage.pop_pending_retake(callback_query.from_user.id)
    await callback_query.message.edit_text("Ок, повторное прохождение отменено.")
    await callback_query.answer()


@router.callback_query(
    TestPassStates.answering, F.data.startswith("ans:")
)
async def handle_answer_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
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
        await process_next_question(
            callback_query.message, state, user_answer
        )

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
            await process_next_question(
                callback_query.message, state, user_answer
            )
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
            await process_next_question(
                callback_query.message, state, user_answer
            )
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


@router.message(TestPassStates.answering)
async def handle_text_answer(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data or await state.get_state() != TestPassStates.answering:
        return

    current_q = data["questions"][data["current_index"]]
    if current_q["question_type"] != "TEXT_ANSWER":
        return

    user_answer = {
        "question_id": current_q["id"],
        "selected_option_ids": [],
        "text_answer": message.text.strip() if message.text else "",
        "matching_answer": None,
    }
    await process_next_question(message, state, user_answer)
