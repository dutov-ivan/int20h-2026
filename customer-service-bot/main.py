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

# Repositories (set up in main)
conv_repo = None
msg_repo = None
session_factory = None


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
    # Create or find conversation (persisted)
    conv = await conv_repo.get_by_user(user_id)
    if not conv:
        full_name = (
            message.from_user.full_name or message.from_user.username or f"{user_id}"
        )
        topic = await bot.create_forum_topic(
            chat_id=FORUM_GROUP_ID, name=f"{full_name} {user_id}"
        )
        thread_id = topic.message_thread_id
        # persist mapping
        await conv_repo.create(user_id, FORUM_GROUP_ID, thread_id)
    else:
        thread_id = conv.thread_id

    # Determine if the user replied or quoted and map reply target
    reply_to_group_id: Optional[int] = None
    if message.reply_to_message:
        replied_id = message.reply_to_message.message_id
        reply_to_group_id = await msg_repo.get_group_id(user_id, replied_id)
    else:
        # try to extract quoted message id from text/caption
        quoted = _extract_quoted_message_id(message)
        if quoted is not None:
            mapped = await msg_repo.get_group_id(user_id, quoted)
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
    # Persist mapping for this copied message pair
    await msg_repo.link(
        user_id=user_id,
        forum_chat_id=FORUM_GROUP_ID,
        thread_id=thread_id,
        user_message_id=message.message_id,
        group_message_id=sent.message_id,
    )


@dp.message(F.chat.id == FORUM_GROUP_ID, F.message_thread_id.is_not(None))
async def from_group_topic(message: Message):
    thread_id = message.message_thread_id

    # Resolve conversation -> user
    conv = await conv_repo.get_by_thread(message.chat.id, thread_id)
    if not conv:
        return
    user_id = conv.user_id

    # Prevent echo loops (bot forwarding itself)
    if message.from_user and message.from_user.is_bot:
        return

    # Determine if the support reply references an earlier group message or quoted link
    reply_to_user_msg_id: Optional[int] = None
    if message.reply_to_message:
        replied_group_id = message.reply_to_message.message_id
        reply_to_user_msg_id = await msg_repo.get_user_id_by_group(
            message.chat.id, thread_id, replied_group_id
        )
    else:
        quoted = _extract_quoted_message_id(message)
        if quoted is not None:
            reply_to_user_msg_id = await msg_repo.get_user_id_by_group(
                message.chat.id, thread_id, quoted
            )

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
    # Persist mapping for this copied message pair
    await msg_repo.link(
        user_id=user_id,
        forum_chat_id=message.chat.id,
        thread_id=thread_id,
        user_message_id=sent.message_id,
        group_message_id=message.message_id,
    )


# Handle edited messages from users in private chats: notify support thread
@dp.edited_message(F.chat.type == ChatType.PRIVATE)
async def user_message_edited(message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id

    # Find conversation mapping
    conv = await conv_repo.get_by_user(user_id)
    if not conv:
        return

    # Find the linked group message for this user message
    group_msg_id = await msg_repo.get_group_id(user_id, message.message_id)
    if group_msg_id is None:
        return

    # Build update notice
    new_text = _get_text_from_message(message)
    update_text = f"<b>UPDATE</b>\n\n{new_text}"

    try:
        await bot.send_message(
            chat_id=conv.forum_chat_id,
            message_thread_id=conv.thread_id,
            text=update_text,
            reply_to_message_id=group_msg_id,
        )
    except Exception:
        logging.exception("Failed to send update notice to support thread")


# Handle edited messages in the forum topic: notify the user
@dp.edited_message(F.chat.id == FORUM_GROUP_ID, F.message_thread_id.is_not(None))
async def group_message_edited(message: Message):
    # Resolve conversation -> user
    conv = await conv_repo.get_by_thread(message.chat.id, message.message_thread_id)
    if not conv:
        return
    user_id = conv.user_id

    # Prevent bot edits being forwarded
    if message.from_user and message.from_user.is_bot:
        return

    # Find the linked user message id for this group message
    user_msg_id = await msg_repo.get_user_id_by_group(
        message.chat.id, message.message_thread_id, message.message_id
    )
    if user_msg_id is None:
        return

    new_text = _get_text_from_message(message)
    update_text = f"<b>UPDATE</b>\n\n{new_text}"

    try:
        await bot.send_message(chat_id=user_id, text=update_text, reply_to_message_id=user_msg_id)
    except Exception:
        logging.exception("Failed to send update notice to user")


async def main():
    # Initialize DB and repositories
    global conv_repo, msg_repo, session_factory
    from db import make_engine, make_session_factory, init_db
    from repos import ConversationRepo, MessageLinkRepo

    DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
    engine = make_engine(DB_URL)
    session_factory = make_session_factory(engine)
    await init_db(engine)

    conv_repo = ConversationRepo(session_factory)
    msg_repo = MessageLinkRepo(session_factory)

    try:
        await dp.start_polling(bot)
    finally:
        logging.info("Shutting down: stopping dispatcher and closing bot session")
        # Attempt to gracefully shutdown the dispatcher (if available)
        try:
            await dp.shutdown()
        except Exception:
            pass

        # Close the bot's HTTP session / client
        try:
            # aiogram Bot exposes either `session` or a `close()` coroutine
            if hasattr(bot, "session") and bot.session is not None:
                await bot.session.close()
            else:
                await bot.close()
        except Exception:
            try:
                await bot.close()
            except Exception:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Interrupted by user, exiting")
    except Exception:
        logging.exception("Unhandled exception during runtime")
