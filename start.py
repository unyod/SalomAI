"""
/start handler — register user and show main menu.
Also handles subscription check callback.
"""
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.queries import (
    get_active_channels,
    get_or_create_user,
    get_user_by_telegram_id,
)
from keyboards.main import main_menu_keyboard
from keyboards.subscription import subscription_keyboard
from services.subscription import check_user_subscription, invalidate_cache
from utils.logger import logger

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    tg = message.from_user
    user = await get_or_create_user(
        session,
        telegram_id=tg.id,
        username=tg.username,
        first_name=tg.first_name or "Foydalanuvchi",
    )
    logger.info(f"User started bot: {tg.id}")

    # Skip subscription check for admins
    if tg.id in settings.admin_ids:
        await _show_main_menu(message, user.first_name)
        return

    # Check required channels
    channels = await get_active_channels(session)
    if channels:
        not_subbed = await check_user_subscription(message.bot, tg.id, channels)
        if not_subbed:
            text = (
                "📢 <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
            )
            for ch in not_subbed:
                name = ch.title or ch.username or ch.channel_id
                text += f"🔴 {name}\n"
            await message.answer(text, reply_markup=subscription_keyboard(not_subbed), parse_mode="HTML")
            return

    await _show_main_menu(message, user.first_name)


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    tg_id = callback.from_user.id
    invalidate_cache(tg_id)

    channels = await get_active_channels(session)
    if not channels:
        user = await get_user_by_telegram_id(session, tg_id)
        name = user.first_name if user else "Foydalanuvchi"
        await callback.message.edit_text("✅ Obuna tasdiqlandi!\n\nEndi botdan foydalanishingiz mumkin.")
        await callback.message.answer(
            f"Assalomu alaykum, <b>{name}</b>! 👋\n\nAsosiy menyu:",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    not_subbed = await check_user_subscription(callback.bot, tg_id, channels)
    if not_subbed:
        text = "❌ <b>Siz hali barcha kanallarga obuna bo'lmagansiz.</b>\n\nIltimos, barcha kanallarga obuna bo'ling va qaytadan tekshiring."
        await callback.answer("❌ Hali to'liq obuna bo'lmadingiz!", show_alert=True)
        await callback.message.edit_text(
            text,
            reply_markup=subscription_keyboard(not_subbed),
            parse_mode="HTML",
        )
        return

    user = await get_user_by_telegram_id(session, tg_id)
    name = user.first_name if user else "Foydalanuvchi"
    await callback.message.edit_text("✅ Obuna tasdiqlandi!\n\nEndi botdan foydalanishingiz mumkin.")
    await callback.message.answer(
        f"Assalomu alaykum, <b>{name}</b>! 👋\n\nAsosiy menyu:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


async def _show_main_menu(message: Message, first_name: str) -> None:
    await message.answer(
        f"Assalomu alaykum, <b>{first_name}</b>! 👋\n\n"
        "Men <b>AI yordamchingizman</b>. Quyidagi menyudan foydalaning:",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
