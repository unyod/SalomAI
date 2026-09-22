"""
Force-subscription service.

Handles Telegram membership checks with a short-lived in-memory cache
to avoid hammering the API on every user message.
"""
from __future__ import annotations

import time
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config import settings
from database.models import RequiredChannel
from utils.logger import logger

# Simple in-memory cache: {(user_id, channel_id): (is_member, expires_at)}
_cache: dict[tuple[int, str], tuple[bool, float]] = {}
TTL = settings.subscription_cache_ttl


def _cache_get(user_id: int, channel_id: str) -> Optional[bool]:
    key = (user_id, channel_id)
    entry = _cache.get(key)
    if entry and time.monotonic() < entry[1]:
        return entry[0]
    _cache.pop(key, None)
    return None


def _cache_set(user_id: int, channel_id: str, is_member: bool) -> None:
    _cache[(user_id, channel_id)] = (is_member, time.monotonic() + TTL)


def invalidate_cache(user_id: int | None = None) -> None:
    """Call this when channel list changes."""
    if user_id is None:
        _cache.clear()
    else:
        keys = [k for k in _cache if k[0] == user_id]
        for k in keys:
            _cache.pop(k, None)


async def check_user_subscription(
    bot: Bot,
    user_id: int,
    channels: list[RequiredChannel],
) -> list[RequiredChannel]:
    """
    Returns a list of channels the user has NOT subscribed to.
    Results are cached per (user_id, channel_id).
    """
    not_subscribed: list[RequiredChannel] = []

    for channel in channels:
        cached = _cache_get(user_id, channel.channel_id)
        if cached is True:
            continue
        if cached is False:
            not_subscribed.append(channel)
            continue

        try:
            member = await bot.get_chat_member(channel.channel_id, user_id)
            is_member = member.status in ("member", "administrator", "creator")
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            logger.warning(f"Cannot check membership for channel {channel.channel_id}: {e}")
            is_member = True  # fail open — don't block user on bot error
        except Exception as e:
            logger.error(f"Unexpected error checking subscription: {e}")
            is_member = True

        _cache_set(user_id, channel.channel_id, is_member)
        if not is_member:
            not_subscribed.append(channel)

    return not_subscribed
