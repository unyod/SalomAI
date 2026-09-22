"""Admin panel keyboards."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.models import RequiredChannel


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users")],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📨 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🚫 Foydalanuvchini bloklash", callback_data="admin_block")],
            [InlineKeyboardButton(text="📢 Force Subscription", callback_data="admin_channels")],
            [InlineKeyboardButton(text="🤖 AI Sozlamalari", callback_data="admin_ai_settings")],
        ]
    )


def channels_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="admin_add_channel")],
            [InlineKeyboardButton(text="📋 Kanallar ro'yxati", callback_data="admin_list_channels")],
            [InlineKeyboardButton(text="« Orqaga", callback_data="admin_back")],
        ]
    )


def channel_actions_keyboard(channel: RequiredChannel) -> InlineKeyboardMarkup:
    status_label = "🔴 O'chirish" if channel.is_active else "🟢 Yoqish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=status_label, callback_data=f"toggle_channel:{channel.id}")],
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_channel:{channel.channel_id}")],
            [InlineKeyboardButton(text="« Orqaga", callback_data="admin_list_channels")],
        ]
    )


def cancel_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_back")]
        ]
    )
