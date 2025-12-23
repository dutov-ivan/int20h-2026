from typing import Optional
from aiogram import Bot, Dispatcher
import logging
from aiogram import F, Dispatcher
from aiogram.types import Message
from aiogram.enums import ChatType

from ..database.requests import ConversationRepo, MessageLinkRepo

from ..utils.text import (
    get_text_from_message,
    extract_quoted_message_id,
    map_quote_to_reply_parameters,
)

logger = logging.getLogger(__name__)


def register_user_handlers(
    dp: Dispatcher,
    bot: Bot,
    conv_repo: ConversationRepo,
    msg_repo: MessageLinkRepo,
    FORUM_GROUP_ID: int,
):
    @dp.message.register(F.chat.type == ChatType.PRIVATE)
    async def from_user(message: Message):
        user_id = message.from_user.id
        conv = await conv_repo.get_by_user(user_id)
        if not conv:
            full_name = (
                message.from_user.full_name
                or message.from_user.username
                or f"{user_id}"
            )
            topic = await bot.create_forum_topic(
                chat_id=FORUM_GROUP_ID, name=f"{full_name} {user_id}"
            )
            thread_id = topic.message_thread_id
            await conv_repo.create(user_id, FORUM_GROUP_ID, thread_id)
        else:
            thread_id = conv.thread_id

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
        await msg_repo.link(
            user_id=user_id,
            forum_chat_id=FORUM_GROUP_ID,
            thread_id=thread_id,
            user_message_id=message.message_id,
            group_message_id=sent.message_id,
        )

    @dp.edited_message.register(F.chat.type == ChatType.PRIVATE)
    async def user_message_edited(message: Message):
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
