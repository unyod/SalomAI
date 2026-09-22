"""
Memory service — extract and format long-term user memory for AI context.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from database.queries import get_user_memories


async def build_memory_context(session: AsyncSession, user_id: int) -> str | None:
    """Return a formatted memory block to inject into the system prompt."""
    memories = await get_user_memories(session, user_id)
    if not memories:
        return None
    lines = [f"- {m.key}: {m.value}" for m in memories]
    return "User memory (use when relevant):\n" + "\n".join(lines)


async def extract_memory_from_message(text: str) -> dict[str, str] | None:
    """
    Simple rule-based extraction for demo.
    In production, delegate to AI for smarter extraction.
    """
    keywords = {
        "o'rganayapman": "learning",
        "o'rganyapman": "learning",
        "ismim": "name",
        "yashayapman": "location",
        "ishlayman": "work",
    }
    text_lower = text.lower()
    for kw, key in keywords.items():
        if kw in text_lower:
            return {key: text[:100]}
    return None
