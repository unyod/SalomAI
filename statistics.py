"""
Statistics service — aggregate stats for users and admins.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from database.queries import (
    get_total_users_count,
    get_total_chats_count,
    get_total_messages_count,
    get_user_chats_count,
    get_user_messages_count,
    get_active_users_today,
    get_new_users_today,
)
from utils.helpers import days_since
from database.models import User


async def get_user_stats(session: AsyncSession, user: User) -> dict:
    chats = await get_user_chats_count(session, user.id)
    messages = await get_user_messages_count(session, user.id)
    age = days_since(user.created_at)
    return {
        "chats": chats,
        "messages": messages,
        "ai_responses": messages // 2,  # rough estimate
        "account_age": age,
    }


async def get_admin_stats(session: AsyncSession) -> dict:
    total_users = await get_total_users_count(session)
    new_today = await get_new_users_today(session)
    active_today = await get_active_users_today(session)
    total_chats = await get_total_chats_count(session)
    total_messages = await get_total_messages_count(session)
    return {
        "total_users": total_users,
        "new_today": new_today,
        "active_today": active_today,
        "total_chats": total_chats,
        "total_messages": total_messages,
    }
