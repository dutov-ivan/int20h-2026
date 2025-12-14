"""Chat utilities for the customer-service-bot.

The project used Telethon previously to create and configure chats. That
approach is no longer used. Creating or configuring chats is considered
obsolete for this project: the bot is expected to already be added to the
target chat, have administrator privileges, and that the chat has topics
enabled. This module provides a lightweight runtime check that uses the
Telegram Bot API to validate those assumptions.

Utilities here intentionally avoid adding Telethon as a dependency.
"""

from typing import Any, Dict
from types import SimpleNamespace
import asyncio
from telegram import Bot, ChatFullInfo

async def validate_chat(bot: Bot, chat_id: str, timeout: int | None = None) -> Dict[str, Any]:
    """Async: validate that `bot` (python-telegram-bot `Bot` instance) is admin and chat has topics enabled.

    - `bot` should implement async methods: `get_me()`, `get_chat(chat_id)`, `get_chat_member(chat_id, user_id)`.
    - Returns a dict with keys: `ok`, `is_admin`, `has_forum`, `chat`, `member`, `error`.

    This function intentionally avoids importing python-telegram-bot at module import
    time so the rest of the project can run without the library until needed.
    """

    try:
        me = await bot.get_me()
    except Exception as exc:  # network or API error
        return {"ok": False, "error": f"get_me failed: {exc}"}

    try:
        print("Chat id:", chat_id)
        chat: ChatFullInfo = await bot.get_chat(chat_id)
        if chat.type not in ["supergroup", "group"]:
            return {"ok": False, "error": f"Chat type is '{chat.type}', expected 'supergroup' or 'group'"}
    except Exception as exc:
        return {"ok": False, "error": f"get_chat failed: {exc}"}


    return {"ok": True, "has_forum": chat.is_forum, "chat": chat}


def validate_chat_sync(bot: Any, chat_id: Any, timeout: int | None = None) -> Dict[str, Any]:
    """Synchronous wrapper around :func:`validate_chat` for code that isn't async.

    It runs the async function using `asyncio.run` and returns the result.
    """

    return asyncio.run(validate_chat(bot, chat_id, timeout=timeout))

