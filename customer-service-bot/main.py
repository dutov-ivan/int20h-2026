import asyncio
import os
import logging
from typing import Dict, Tuple, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyParameters, TextQuote
from aiogram.enums import ChatType
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)
from dotenv import load_dotenv

load_dotenv()

# Read configuration from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
FORUM_GROUP_ID_RAW = os.getenv("FORUM_GROUP_ID")

if not BOT_TOKEN:
    raise SystemExit("Environment variable BOT_TOKEN is required")

if not FORUM_GROUP_ID_RAW:
    raise SystemExit("Environment variable FORUM_GROUP_ID is required")

try:
    FORUM_GROUP_ID = int(FORUM_GROUP_ID_RAW)
except Exception:
    raise SystemExit("Environment variable FORUM_GROUP_ID must be an integer")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# In-memory mappings
# user_id -> thread_id
user_to_topic: Dict[int, int] = {}
# thread_id -> user_id
topic_to_user: Dict[int, int] = {}

# Message reply mappings to preserve reply context
# (thread_id, group_message_id) -> user_message_id
group_to_user_msg: Dict[Tuple[int, int], int] = {}
# (user_id, user_message_id) -> group_message_id
user_to_group_msg: Dict[Tuple[int, int], int] = {}


def _get_text_from_message(message: Message) -> str:
    return message.text or message.caption or ""


def _extract_quoted_message_id(message: Message) -> Optional[int]:
    # Prefer explicit reply_to_message
    if message.reply_to_message:
        return message.reply_to_message.message_id

    # Try to find t.me links or message id in text/caption
    import re

    text_src = message.text or message.caption or ""
    # match /<digits> at end or ?message= or &m=
    m = re.search(r"/(\d+)(?:$|\D)", text_src)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    m = re.search(r"[?&](?:message|msg|m)=(\d+)", text_src)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            pass
    return None


def map_quote_to_reply_parameters(
    quote: Optional[TextQuote],
    target_message_id: int,
    target_chat_id: Optional[int | str] = None,
) -> ReplyParameters:
    # Build and return an immutable ReplyParameters instance
    kwargs: dict = {"message_id": int(target_message_id)}
    if target_chat_id is not None:
        kwargs["chat_id"] = target_chat_id

    if quote:
        qtext = quote.text or ""
        if len(qtext) > 1024:
            qtext = qtext[:1024]
        kwargs["quote"] = qtext
        if quote.entities:
            kwargs["quote_entities"] = quote.entities
        if quote.position is not None:
            kwargs["quote_position"] = quote.position

    return ReplyParameters(**kwargs)


@dp.message(F.chat.type == ChatType.PRIVATE)
async def from_user(message: Message):
    user_id = message.from_user.id

    # Create topic if not exists; use full name + id as title
    if user_id not in user_to_topic:
        full_name = (
            message.from_user.full_name or message.from_user.username or f"{user_id}"
        )
        topic = await bot.create_forum_topic(
            chat_id=FORUM_GROUP_ID, name=f"{full_name} {user_id}"
        )
        thread_id = topic.message_thread_id
        user_to_topic[user_id] = thread_id
        topic_to_user[thread_id] = user_id
    else:
        thread_id = user_to_topic[user_id]

    # Determine if the user replied or quoted and map reply target
    reply_to_group_id: Optional[int] = None
    if message.reply_to_message:
        replied_id = message.reply_to_message.message_id
        reply_to_group_id = user_to_group_msg.get((user_id, replied_id))
    else:
        # try to extract quoted message id from text/caption
        quoted = _extract_quoted_message_id(message)
        if quoted is not None:
            mapped = user_to_group_msg.get((user_id, quoted))
            reply_to_group_id = mapped if mapped is not None else quoted

    # Prepare optional ReplyParameters only when we have a target message id
    reply_parameters = None
    if reply_to_group_id is not None:
        reply_parameters = map_quote_to_reply_parameters(
            message.quote, target_message_id=reply_to_group_id
        )
    else:
        # If there's a quote but no known target, log it and include the quote text in the forwarded message
        if message.quote:
            logging.info(
                "User sent a quote without resolvable target: %s", message.quote.text
            )
            if message.reply_to_message:
                logging.info(
                    "Quoted original message text: %s",
                    _get_text_from_message(message.reply_to_message),
                )

    # Copy the incoming message (text, media, files) into the forum topic thread
    copy_kwargs = dict(
        chat_id=FORUM_GROUP_ID,
        message_thread_id=thread_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        reply_to_message_id=reply_to_group_id,
    )
    if reply_parameters is not None:
        copy_kwargs["reply_parameters"] = reply_parameters

    sent = await bot.copy_message(**copy_kwargs)

    # Save mapping so future replies from support can reference the original user message
    group_to_user_msg[(thread_id, sent.message_id)] = message.message_id
    user_to_group_msg[(user_id, message.message_id)] = sent.message_id


@dp.message(F.chat.id == FORUM_GROUP_ID, F.message_thread_id.is_not(None))
async def from_group_topic(message: Message):
    thread_id = message.message_thread_id

    # Ignore messages not mapped to a user
    if thread_id not in topic_to_user:
        return

    user_id = topic_to_user[thread_id]

    # Prevent echo loops (bot forwarding itself)
    if message.from_user and message.from_user.is_bot:
        return

    # Determine if the support reply references an earlier group message or quoted link
    reply_to_user_msg_id: Optional[int] = None
    if message.reply_to_message:
        replied_group_id = message.reply_to_message.message_id
        reply_to_user_msg_id = group_to_user_msg.get((thread_id, replied_group_id))
    else:
        quoted = _extract_quoted_message_id(message)
        if quoted is not None:
            reply_to_user_msg_id = group_to_user_msg.get((thread_id, quoted))

    # Prepare ReplyParameters only when we have a target message id
    reply_parameters = None
    if reply_to_user_msg_id is not None:
        reply_parameters = map_quote_to_reply_parameters(
            message.quote, target_message_id=reply_to_user_msg_id
        )
    else:
        if message.quote:
            logging.info(
                "Support sent a quote without resolvable target: %s", message.quote.text
            )
            if message.reply_to_message:
                logging.info(
                    "Quoted original group message text: %s",
                    _get_text_from_message(message.reply_to_message),
                )

    copy_kwargs = dict(
        chat_id=user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        reply_to_message_id=reply_to_user_msg_id,
    )
    if reply_parameters is not None:
        copy_kwargs["reply_parameters"] = reply_parameters

    sent = await bot.copy_message(**copy_kwargs)

    # Save mapping so if the user replies to this private message, we can reply into the forum thread
    group_to_user_msg[(thread_id, message.message_id)] = sent.message_id
    user_to_group_msg[(user_id, sent.message_id)] = message.message_id


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
