"""
Active AI chat handler.

State machine:
  ChatStates.in_chat — user is chatting; every text message goes to AI.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.queries import (
    add_message,
    create_chat,
    get_chat_by_id,
    get_chat_messages,
    get_user_by_telegram_id,
    touch_chat,
    update_chat_title,
)
from keyboards.chats import stop_chat_keyboard
from keyboards.main import main_menu_keyboard
from services.ai import get_provider
from services.memory import build_memory_context, extract_memory_from_message
from database.queries import upsert_memory
from utils.logger import logger

router = Router()


class ChatStates(StatesGroup):
    in_chat = State()


# ─────────────────────────── New chat ───────────────────────────

@router.message(F.text == "💬 Yangi chat")
async def new_chat(message: Message, session: AsyncSession, state: FSMContext) -> None:
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        return

    chat = await create_chat(session, user.id)
    await state.set_state(ChatStates.in_chat)
    await state.update_data(chat_id=chat.id, user_db_id=user.id, title_set=False)

    await message.answer(
        "💬 <b>Yangi chat boshlandi!</b>\n\n"
        "Savolingizni yozing. Men javob beraman 🤖\n\n"
        "Chatni tugatish uchun tugmani bosing yoki /start yozing.",
        reply_markup=stop_chat_keyboard(),
        parse_mode="HTML",
    )


# Continue existing chat
@router.callback_query(F.data.startswith("continue_chat:"))
async def continue_chat(callback: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    chat_id = int(callback.data.split(":")[1])
    user = await get_user_by_telegram_id(session, callback.from_user.id)
    if not user:
        return

    chat = await get_chat_by_id(session, chat_id, user.id)
    if not chat:
        await callback.answer("❌ Chat topilmadi.", show_alert=True)
        return

    await state.set_state(ChatStates.in_chat)
    await state.update_data(chat_id=chat.id, user_db_id=user.id, title_set=True)
    await callback.message.answer(
        f"💬 <b>{chat.title}</b> chatini davom ettiryapsiz.\n\nSavolingizni yozing 🤖",
        reply_markup=stop_chat_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# Stop chat
@router.callback_query(F.data == "stop_chat")
async def stop_chat(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "🛑 Chat tugatildi. Asosiy menyuga qaytdingiz.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


# Cancel misc actions
@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Bekor qilindi.")


# ─────────────────────────── In-chat message ───────────────────────────

@router.message(ChatStates.in_chat, F.text)
async def handle_chat_message(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    chat_id: int = data["chat_id"]
    user_db_id: int = data["user_db_id"]
    title_set: bool = data.get("title_set", False)

    user_text = message.text.strip()

    # Save user message
    await add_message(session, chat_id, "user", user_text)
    await touch_chat(session, chat_id)

    # Show typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Build message history for AI
    history = await get_chat_messages(session, chat_id, limit=40)

    # Get user settings
    from sqlalchemy import select
    from database.models import User as UserModel
    result = await session.execute(
        select(UserModel).where(UserModel.id == user_db_id)
    )
    user: User = result.scalar_one_or_none()

    # Build system prompt
    system_parts = [
        "Sen professional va do'stona AI yordamchisan. "
        "O'zbek, rus yoki ingliz tilida javob ber — foydalanuvchi qaysi tilda yozsa, "
        "shu tilda javob ber. Qisqa va aniq javob ber."
    ]

    if user and user.memory_enabled:
        mem_context = await build_memory_context(session, user_db_id)
        if mem_context:
            system_parts.append(mem_context)

    messages_for_ai = [{"role": "system", "content": "\n\n".join(system_parts)}]
    for msg in history:
        if msg.role in ("user", "assistant"):
            messages_for_ai.append({"role": msg.role, "content": msg.content})

    # Call AI
    ai_model = user.ai_model if user else "gemini"
    provider = get_provider(ai_model)

    try:
        logger.info(f"AI request: user_id={user_db_id}, chat_id={chat_id}, model={ai_model}")
        ai_response = await provider.chat(messages_for_ai)
        logger.info(f"AI response received: chat_id={chat_id}")
    except Exception as e:
        logger.error(f"AI error: {e}")
        err_text = str(e)
        if "503" in err_text or "barcha model" in err_text.lower() or "overload" in err_text.lower():
            await message.answer(
                "⏳ <b>Gemini AI hozir juda band.</b>\n\n"
                "Bir nechta model sinab ko'rildi, lekin barchasi vaqtincha yuklanishda.\n"
                "📌 Iltimos <b>30-60 soniya</b> kuting va xabaringizni qayta yuboring."
            )
        else:
            await message.answer(
                "⚠️ AI xizmatida xatolik yuz berdi.\n"
                "Iltimos, biroz kutib qayta urinib ko'ring."
            )
        return

    # Save AI response
    await add_message(session, chat_id, "assistant", ai_response)

    # Auto-generate chat title from first message
    if not title_set:
        try:
            title = await provider.generate_title(user_text)
            await update_chat_title(session, chat_id, user_db_id, title)
            await state.update_data(title_set=True)
        except Exception:
            pass

    # Extract and save memory
    if user and user.memory_enabled:
        mem_data = await extract_memory_from_message(user_text)
        if mem_data:
            for key, value in mem_data.items():
                await upsert_memory(session, user_db_id, key, value)

    await message.answer(ai_response, reply_markup=stop_chat_keyboard())
