"""Main reply keyboard."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💬 Yangi chat"), KeyboardButton(text="📚 Chatlarim")],
            [KeyboardButton(text="🧠 Memory"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="⚙️ Sozlamalar"), KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
    )
