"""
AI Telegram Bot — main entry point.

Run:
    pip install -r requirements.txt
    python bot.py
"""
import asyncio
import sys

# Configure UTF-8 encoding for Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.database import init_db
from handlers import admin, chat, chats, help, memory, settings as settings_handler, start, statistics
from middlewares.db_session import DbSessionMiddleware
from middlewares.subscription import SubscriptionMiddleware
from utils.logger import logger


async def main() -> None:
    logger.info("Starting AI Telegram Bot...")

    # Initialize DB
    await init_db()

    # Validate BOT_TOKEN
    if not settings.bot_token or settings.bot_token == "your_telegram_bot_token_here":
        logger.error("BOT_TOKEN aniqlanmadi! Iltimos, .env faylida BOT_TOKEN ni kiriting.")
        print("\n" + "=" * 60)
        print("❌ XATOLIK: .env faylida BOT_TOKEN ko'rsatilmagan!")
        print("Iltimos, .env faylini oching va Telegram bot tokeningizni kiriting:")
        print("  BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        print("  GEMINI_API_KEY=sizning_gemini_api_kalitingiz")
        print("=" * 60 + "\n")
        return

    # Create bot and dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register middlewares (order matters)
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # Register routers
    dp.include_router(start.router)
    dp.include_router(admin.router)       # Admin before general chat
    dp.include_router(chat.router)
    dp.include_router(chats.router)
    dp.include_router(memory.router)
    dp.include_router(statistics.router)
    dp.include_router(settings_handler.router)
    dp.include_router(help.router)

    logger.info(f"Bot started. Admin IDs: {settings.admin_ids}")
    logger.info(f"AI Provider: {settings.ai_provider}")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
