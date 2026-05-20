from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def test_start_keyboard(already_attempted: bool, test_id: int) -> InlineKeyboardMarkup:
    """Return inline keyboard for starting or retaking a test."""
    button_text = "🔁 Пройти повторно" if already_attempted else "🚀 Начать прохождение"
    callback = f"test:{'retake' if already_attempted else 'start'}:{test_id}"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=button_text, callback_data=callback)]])


def retake_confirm_keyboard(test_id: int) -> InlineKeyboardMarkup:
    """Keyboard shown when user chooses to retake a test."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да, начать заново", callback_data=f"test:confirm_retake:{test_id}"),
                InlineKeyboardButton(text="Отмена", callback_data="test:cancel_retake:0"),
            ]
        ]
    )
