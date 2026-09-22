"""
AI Service — provider-agnostic interface.

Add new providers by subclassing BaseAIProvider and registering in get_provider().
"""
from __future__ import annotations

import abc
import asyncio
import json
from typing import Any

import aiohttp

from config import settings
from utils.logger import logger

# Fallback model chain — tried in order if primary is overloaded (503)
GEMINI_FALLBACK_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-pro-latest",
]


class BaseAIProvider(abc.ABC):
    """Abstract base for AI providers."""

    @abc.abstractmethod
    async def chat(self, messages: list[dict], model: str | None = None) -> str:
        ...

    @abc.abstractmethod
    async def generate_title(self, first_message: str) -> str:
        ...


# ─────────────────────────── GEMINI ───────────────────────────

class GeminiProvider(BaseAIProvider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    async def _call_model(
        self,
        model: str,
        payload: dict,
        session: aiohttp.ClientSession,
    ) -> str | None:
        """Try a single model. Returns text or None if unavailable (503/429)."""
        url = f"{self.BASE_URL}/{model}:generateContent?key={settings.gemini_api_key}"
        try:
            async with session.post(
                url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    try:
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError) as e:
                        logger.error(f"Gemini response parse error ({model}): {e}")
                        return None
                elif resp.status in (503, 429, 502):
                    # Overloaded or rate limited — try next model
                    body = await resp.text()
                    logger.warning(f"Gemini {model} overloaded ({resp.status}): {body[:120]}")
                    return None
                else:
                    body = await resp.text()
                    logger.error(f"Gemini API error {resp.status} ({model}): {body[:200]}")
                    raise RuntimeError(f"Gemini API error: {resp.status}")
        except asyncio.TimeoutError:
            logger.warning(f"Gemini {model} timed out, trying next...")
            return None
        except aiohttp.ClientConnectionError as e:
            logger.warning(f"Gemini {model} connection error: {e}")
            return None

    async def chat(self, messages: list[dict], model: str | None = None) -> str:
        # Build model list: preferred first, then fallbacks
        primary = model or settings.gemini_model
        models_to_try = [primary] + [m for m in GEMINI_FALLBACK_MODELS if m != primary]

        # Convert OpenAI-style messages to Gemini format
        contents = []
        system_prompt = None
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_prompt = content
                continue
            gemini_role = "user" if role == "user" else "model"
            contents.append({"role": gemini_role, "parts": [{"text": content}]})

        payload: dict[str, Any] = {"contents": contents}
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async with aiohttp.ClientSession() as session:
            for attempt_model in models_to_try:
                result = await self._call_model(attempt_model, payload, session)
                if result is not None:
                    if attempt_model != primary:
                        logger.info(f"Used fallback model: {attempt_model}")
                    return result
                # Small delay before trying next model
                await asyncio.sleep(0.5)

        raise RuntimeError(
            "Gemini: barcha modellar vaqtincha yuklanishda. "
            "Iltimos, bir daqiqadan so'ng qayta urinib ko'ring."
        )

    async def generate_title(self, first_message: str) -> str:
        prompt = (
            f"Create a very short chat title (2-4 words, no quotes) "
            f"from this message: {first_message[:200]}"
        )
        try:
            result = await self.chat([{"role": "user", "content": prompt}])
            return result.strip().strip('"').strip("'")[:50]
        except Exception:
            return "Yangi chat"


# ─────────────────────────── OPENAI ───────────────────────────

class OpenAIProvider(BaseAIProvider):
    BASE_URL = "https://api.openai.com/v1/chat/completions"

    async def chat(self, messages: list[dict], model: str | None = None) -> str:
        model = model or settings.openai_model
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model, "messages": messages}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.BASE_URL, json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.error(f"OpenAI API error {resp.status}: {text[:200]}")
                    raise RuntimeError(f"OpenAI API error: {resp.status}")
                data = await resp.json()

        return data["choices"][0]["message"]["content"]

    async def generate_title(self, first_message: str) -> str:
        prompt = (
            f"Create a very short chat title (2-4 words, no quotes) "
            f"from this message: {first_message[:200]}"
        )
        try:
            result = await self.chat([{"role": "user", "content": prompt}])
            return result.strip().strip('"').strip("'")[:50]
        except Exception:
            return "Yangi chat"


# ─────────────────────────── REGISTRY ───────────────────────────

_PROVIDERS: dict[str, type[BaseAIProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
}


def get_provider(name: str | None = None) -> BaseAIProvider:
    name = (name or settings.ai_provider).lower()
    cls = _PROVIDERS.get(name, GeminiProvider)
    return cls()


def list_available_models() -> list[str]:
    return list(_PROVIDERS.keys())
