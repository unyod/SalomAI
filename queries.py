"""
Database queries — all DB interactions go through this module.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Chat, Memory, Message, RequiredChannel, User
from utils.logger import logger


# ─────────────────────────── USER ───────────────────────────

async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str],
    first_name: str,
) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.username = username
        user.first_name = first_name
        await session.commit()
        return user
    user = User(telegram_id=telegram_id, username=username, first_name=first_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info(f"New user registered: {telegram_id} (@{username})")
    return user


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def update_user_field(session: AsyncSession, user_id: int, **kwargs) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(**kwargs)
    )
    await session.commit()


async def get_all_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return list(result.scalars().all())


async def get_active_users_today(session: AsyncSession) -> int:
    today = datetime.now(timezone.utc).date()
    result = await session.execute(
        select(func.count()).select_from(User)
        .where(func.date(User.updated_at) == today)
    )
    return result.scalar_one()


async def get_new_users_today(session: AsyncSession) -> int:
    today = datetime.now(timezone.utc).date()
    result = await session.execute(
        select(func.count()).select_from(User)
        .where(func.date(User.created_at) == today)
    )
    return result.scalar_one()


# ─────────────────────────── CHAT ───────────────────────────

async def create_chat(session: AsyncSession, user_id: int, title: str = "Yangi chat") -> Chat:
    chat = Chat(user_id=user_id, title=title)
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    logger.info(f"Chat created: id={chat.id} user_id={user_id}")
    return chat


async def get_user_chats(session: AsyncSession, user_id: int) -> list[Chat]:
    result = await session.execute(
        select(Chat)
        .where(Chat.user_id == user_id)
        .order_by(Chat.is_pinned.desc(), Chat.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_chat_by_id(session: AsyncSession, chat_id: int, user_id: int) -> Optional[Chat]:
    result = await session.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_chat_title(session: AsyncSession, chat_id: int, user_id: int, title: str) -> bool:
    result = await session.execute(
        update(Chat)
        .where(Chat.id == chat_id, Chat.user_id == user_id)
        .values(title=title)
    )
    await session.commit()
    return result.rowcount > 0


async def toggle_pin_chat(session: AsyncSession, chat_id: int, user_id: int) -> bool:
    chat = await get_chat_by_id(session, chat_id, user_id)
    if not chat:
        return False
    chat.is_pinned = not chat.is_pinned
    await session.commit()
    return chat.is_pinned


async def delete_chat(session: AsyncSession, chat_id: int, user_id: int) -> bool:
    result = await session.execute(
        delete(Chat).where(Chat.id == chat_id, Chat.user_id == user_id)
    )
    await session.commit()
    return result.rowcount > 0


async def delete_all_user_chats(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        delete(Chat).where(Chat.user_id == user_id)
    )
    await session.commit()
    return result.rowcount


async def touch_chat(session: AsyncSession, chat_id: int) -> None:
    await session.execute(
        update(Chat).where(Chat.id == chat_id)
        .values(updated_at=datetime.now(timezone.utc))
    )
    await session.commit()


# ─────────────────────────── MESSAGE ───────────────────────────

async def add_message(session: AsyncSession, chat_id: int, role: str, content: str) -> Message:
    msg = Message(chat_id=chat_id, role=role, content=content)
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def get_chat_messages(
    session: AsyncSession, chat_id: int, limit: int = 40
) -> list[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_total_messages_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Message))
    return result.scalar_one()


async def get_user_messages_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count()).select_from(Message)
        .join(Chat, Chat.id == Message.chat_id)
        .where(Chat.user_id == user_id)
    )
    return result.scalar_one()


# ─────────────────────────── MEMORY ───────────────────────────

async def get_user_memories(session: AsyncSession, user_id: int) -> list[Memory]:
    result = await session.execute(
        select(Memory).where(Memory.user_id == user_id).order_by(Memory.created_at.asc())
    )
    return list(result.scalars().all())


async def upsert_memory(session: AsyncSession, user_id: int, key: str, value: str) -> Memory:
    result = await session.execute(
        select(Memory).where(Memory.user_id == user_id, Memory.key == key)
    )
    mem = result.scalar_one_or_none()
    if mem:
        mem.value = value
        mem.updated_at = datetime.now(timezone.utc)
        await session.commit()
        return mem
    mem = Memory(user_id=user_id, key=key, value=value)
    session.add(mem)
    await session.commit()
    await session.refresh(mem)
    return mem


async def clear_user_memories(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        delete(Memory).where(Memory.user_id == user_id)
    )
    await session.commit()
    return result.rowcount


# ─────────────────────────── REQUIRED CHANNELS ───────────────────────────

async def get_active_channels(session: AsyncSession) -> list[RequiredChannel]:
    result = await session.execute(
        select(RequiredChannel).where(RequiredChannel.is_active == True)
    )
    return list(result.scalars().all())


async def get_all_channels(session: AsyncSession) -> list[RequiredChannel]:
    result = await session.execute(select(RequiredChannel))
    return list(result.scalars().all())


async def add_channel(
    session: AsyncSession,
    channel_id: str,
    username: Optional[str],
    title: str,
    invite_link: Optional[str] = None,
) -> RequiredChannel:
    ch = RequiredChannel(
        channel_id=channel_id,
        username=username,
        title=title,
        invite_link=invite_link,
    )
    session.add(ch)
    await session.commit()
    await session.refresh(ch)
    return ch


async def delete_channel(session: AsyncSession, channel_id: str) -> bool:
    result = await session.execute(
        delete(RequiredChannel).where(RequiredChannel.channel_id == channel_id)
    )
    await session.commit()
    return result.rowcount > 0


async def toggle_channel_status(session: AsyncSession, channel_db_id: int) -> Optional[bool]:
    result = await session.execute(
        select(RequiredChannel).where(RequiredChannel.id == channel_db_id)
    )
    ch = result.scalar_one_or_none()
    if not ch:
        return None
    ch.is_active = not ch.is_active
    await session.commit()
    return ch.is_active


# ─────────────────────────── STATISTICS ───────────────────────────

async def get_total_users_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(User))
    return result.scalar_one()


async def get_total_chats_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(Chat))
    return result.scalar_one()


async def get_user_chats_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count()).select_from(Chat).where(Chat.user_id == user_id)
    )
    return result.scalar_one()
