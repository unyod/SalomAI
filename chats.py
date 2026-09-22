"""Chats list and chat-detail inline keyboards."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import Chat
from utils.helpers import truncate_text


def chats_list_keyboard(chats: list[Chat]) -> InlineKeyboardMarkup:
    buttons = []
    for chat in chats:
        pin = "📌 " if chat.is_pinned else ""
        label = f"{pin}{truncate_text(chat.title, 35)}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"open_chat:{chat.id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def chat_detail_keyboard(chat_id: int, is_pinned: bool) -> InlineKeyboardMarkup:
    pin_label = "📌 Unpin" if is_pinned else "📌 Pin qilish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Davom ettirish", callback_data=f"continue_chat:{chat_id}")],
            [InlineKeyboardButton(text="✏️ Nomini o'zgartirish", callback_data=f"rename_chat:{chat_id}")],
            [InlineKeyboardButton(text=pin_label, callback_data=f"pin_chat:{chat_id}")],
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_chat:{chat_id}")],
            [InlineKeyboardButton(text="« Orqaga", callback_data="my_chats")],
        ]
    )


def confirm_delete_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete:{chat_id}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"open_chat:{chat_id}"),
            ]
        ]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
        ]
    )


def stop_chat_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛑 Chatni tugatish", callback_data="stop_chat")]
        ]
    )
