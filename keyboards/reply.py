"""
Reply клавиатуры
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def contact_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса контакта"""
    builder = ReplyKeyboardBuilder()

    builder.add(KeyboardButton(
        text="📱 Поделиться контактом",
        request_contact=True
    ))

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def remove_keyboard() -> ReplyKeyboardMarkup:
    """Убрать клавиатуру"""
    return ReplyKeyboardMarkup(
        keyboard=[],
        resize_keyboard=True,
        remove_keyboard=True
    )
