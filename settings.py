"""Settings and memory keyboards."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from services.ai import list_available_models


def settings_keyboard(memory_enabled: bool) -> InlineKeyboardMarkup:
    mem_label = "🟢 Memory: ON" if memory_enabled else "🔴 Memory: OFF"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 AI Model", callback_data="settings_model")],
            [InlineKeyboardButton(text=mem_label, callback_data="settings_toggle_memory")],
            [InlineKeyboardButton(text="🌐 Til", callback_data="settings_language")],
            [InlineKeyboardButton(text="🗑 Barcha chatlarni o'chirish", callback_data="settings_clear_chats")],
            [InlineKeyboardButton(text="🔄 Sozlamalarni tiklash", callback_data="settings_reset")],
        ]
    )


def ai_model_keyboard(current_model: str) -> InlineKeyboardMarkup:
    models = list_available_models()
    buttons = []
    for m in models:
        mark = "✅ " if m == current_model else ""
        buttons.append([InlineKeyboardButton(text=f"{mark}{m.capitalize()}", callback_data=f"set_model:{m}")])
    buttons.append([InlineKeyboardButton(text="« Orqaga", callback_data="settings_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="set_lang:uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru")],
            [InlineKeyboardButton(text="🇺🇸 English", callback_data="set_lang:en")],
            [InlineKeyboardButton(text="« Orqaga", callback_data="settings_back")],
        ]
    )


def memory_keyboard(memory_enabled: bool) -> InlineKeyboardMarkup:
    toggle_label = "🔴 Memory OFF qilish" if memory_enabled else "🟢 Memory ON qilish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_label, callback_data="memory_toggle")],
            [InlineKeyboardButton(text="🗑 Memory'ni tozalash", callback_data="memory_clear")],
        ]
    )


def confirm_clear_keyboard(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data=f"confirm_{action}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="cancel_action"),
            ]
        ]
    )
