from typing import Optional
import logging
from aiogram import Bot, Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

from ..database.requests import ConversationRepo, MessageLinkRepo
from ..utils.text import (
    get_text_from_message,
    extract_quoted_message_id,
    map_quote_to_reply_parameters,
)

logger = logging.getLogger(__name__)


def create_user_router(
    forum_group_id: int, conv_repo: ConversationRepo, msg_repo: MessageLinkRepo
) -> Router:
    """
    Creates a Router specifically for handling Private Messages from users.
    """
    router = Router()

    # Apply filter to the whole router: Only Private Chats
    router.message.filter(F.chat.type == ChatType.PRIVATE)
    router.edited_message.filter(F.chat.type == ChatType.PRIVATE)

    @router.message()
    async def from_user(message: Message, bot: Bot):
        user_id = message.from_user.id

        # Access 'conv_repo' from closure
        conv = await conv_repo.get_by_user(user_id)

        # 1. Create Topic if it doesn't exist
        if not conv:
            full_name = (
                message.from_user.full_name
                or message.from_user.username
                or f"{user_id}"
            )
            # Access 'forum_group_id' from closure
            try:
                topic = await bot.create_forum_topic(
                    chat_id=forum_group_id, name=f"{full_name} {user_id}"
                )
                thread_id = topic.message_thread_id
                await conv_repo.create(user_id, forum_group_id, thread_id)
            except Exception as e:
                logger.error(f"Failed to create forum topic: {e}")
                return
        else:
            thread_id = conv.thread_id

        # 2. Logic to determine if user is replying to a specific message
        reply_to_group_id: Optional[int] = None
        if message.reply_to_message:
            replied_id = message.reply_to_message.message_id
            reply_to_group_id = await msg_repo.get_group_id(user_id, replied_id)
        else:
            quoted = extract_quoted_message_id(message)
            if quoted is not None:
                mapped = await msg_repo.get_group_id(user_id, quoted)
                reply_to_group_id = mapped if mapped is not None else quoted

        reply_parameters = None
        if reply_to_group_id is not None:
            reply_parameters = map_quote_to_reply_parameters(
                message.quote, target_message_id=reply_to_group_id
            )
        else:
            if message.quote:
                logger.info(
                    "User sent a quote without resolvable target: %s",
                    message.quote.text,
                )
                if message.reply_to_message:
                    logger.info(
                        "Quoted original message text: %s",
                        get_text_from_message(message.reply_to_message),
                    )

        # 3. Copy the message to the Forum
        copy_kwargs = dict(
            chat_id=forum_group_id,
            message_thread_id=thread_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_to_message_id=reply_to_group_id,
        )
        if reply_parameters is not None:
            copy_kwargs["reply_parameters"] = reply_parameters

        sent = await bot.copy_message(**copy_kwargs)

        # 4. Link the two messages in DB
        await msg_repo.link(
            user_id=user_id,
            forum_chat_id=forum_group_id,
            thread_id=thread_id,
            user_message_id=message.message_id,
            group_message_id=sent.message_id,
        )

    @router.edited_message()
    async def user_message_edited(message: Message, bot: Bot):
        if not message.from_user:
            return

        user_id = message.from_user.id
        conv = await conv_repo.get_by_user(user_id)
        if not conv:
            return

        group_msg_id = await msg_repo.get_group_id(user_id, message.message_id)
        if group_msg_id is None:
            return

        new_text = get_text_from_message(message)
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

    return router
