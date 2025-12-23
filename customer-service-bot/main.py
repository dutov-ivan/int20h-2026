import asyncio
import os
import logging
from typing import Dict, Tuple, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
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

    # Determine if the user replied to one of our messages and map reply target
    reply_to_group_id: Optional[int] = None
    if getattr(message, "reply_to_message", None):
        replied_id = message.reply_to_message.message_id
        reply_to_group_id = user_to_group_msg.get((user_id, replied_id))

    text = _get_text_from_message(message)

    # Send text-only messages and preserve reply mapping
    sent = await bot.send_message(
        chat_id=FORUM_GROUP_ID,
        message_thread_id=thread_id,
        text=text,
        reply_to_message_id=reply_to_group_id,
    )

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

    # Determine if the support reply references an earlier group message
    reply_to_user_msg_id: Optional[int] = None
    if getattr(message, "reply_to_message", None):
        replied_group_id = message.reply_to_message.message_id
        reply_to_user_msg_id = group_to_user_msg.get((thread_id, replied_group_id))

    text = _get_text_from_message(message)

    sent = await bot.send_message(
        chat_id=user_id, text=text, reply_to_message_id=reply_to_user_msg_id
    )

    # Save mapping so if the user replies to this private message, we can reply into the forum thread
    group_to_user_msg[(thread_id, message.message_id)] = sent.message_id
    user_to_group_msg[(user_id, sent.message_id)] = message.message_id


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
