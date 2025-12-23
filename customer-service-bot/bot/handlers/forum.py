from typing import Optional
from aiogram import Bot, Dispatcher
import logging
from aiogram import F
from aiogram.types import Message
from ..database.requests import ConversationRepo, MessageLinkRepo

from ..utils.text import (
    get_text_from_message,
    extract_quoted_message_id,
    map_quote_to_reply_parameters,
)

logger = logging.getLogger(__name__)


def register_forum_handlers(
    dp: Dispatcher,
    bot: Bot,
    conv_repo: ConversationRepo,
    msg_repo: MessageLinkRepo,
    FORUM_GROUP_ID: int,
):
    @dp.message.register(F.chat.id == FORUM_GROUP_ID, F.message_thread_id.is_not(None))
    async def from_group_topic(message: Message):
        thread_id = message.message_thread_id
        conv = await conv_repo.get_by_thread(message.chat.id, thread_id)
        if not conv:
            return
        user_id = conv.user_id
        if message.from_user and message.from_user.is_bot:
            return

        reply_to_user_msg_id: Optional[int] = None
        if message.reply_to_message:
            replied_group_id = message.reply_to_message.message_id
            reply_to_user_msg_id = await msg_repo.get_user_id_by_group(
                message.chat.id, thread_id, replied_group_id
            )
        else:
            quoted = extract_quoted_message_id(message)
            if quoted is not None:
                reply_to_user_msg_id = await msg_repo.get_user_id_by_group(
                    message.chat.id, thread_id, quoted
                )

        reply_parameters = None
        if reply_to_user_msg_id is not None:
            reply_parameters = map_quote_to_reply_parameters(
                message.quote, target_message_id=reply_to_user_msg_id
            )
        else:
            if message.quote:
                logger.info(
                    "Support sent a quote without resolvable target: %s",
                    message.quote.text,
                )
                if message.reply_to_message:
                    logger.info(
                        "Quoted original group message text: %s",
                        get_text_from_message(message.reply_to_message),
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
        await msg_repo.link(
            user_id=user_id,
            forum_chat_id=message.chat.id,
            thread_id=thread_id,
            user_message_id=sent.message_id,
            group_message_id=message.message_id,
        )

    @dp.edited_message.register(
        F.chat.id == FORUM_GROUP_ID, F.message_thread_id.is_not(None)
    )
    async def group_message_edited(message: Message):
        conv = await conv_repo.get_by_thread(message.chat.id, message.message_thread_id)
        if not conv:
            return
        user_id = conv.user_id
        if message.from_user and message.from_user.is_bot:
            return
        user_msg_id = await msg_repo.get_user_id_by_group(
            message.chat.id, message.message_thread_id, message.message_id
        )
        if user_msg_id is None:
            return
        new_text = get_text_from_message(message)
        update_text = f"<b>UPDATE</b>\n\n{new_text}"
        try:
            await bot.send_message(
                chat_id=user_id, text=update_text, reply_to_message_id=user_msg_id
            )
        except Exception:
            logging.exception("Failed to send update notice to user")
