from typing import Optional
import logging
from aiogram import Bot, Router, F
from aiogram.types import Message
from ..database.requests import ConversationRepo, MessageLinkRepo
from ..utils.text import (
    get_text_from_message,
    extract_quoted_message_id,
    map_quote_to_reply_parameters,
)

logger = logging.getLogger(__name__)


def create_forum_router(
    forum_group_id: int, conv_repo: ConversationRepo, msg_repo: MessageLinkRepo
) -> Router:
    """
    Creates a Router configured specifically for the support forum group.
    Dependencies are injected via closure (captured from arguments).
    """
    router = Router()

    # Apply a filter to the ENTIRE router.
    # Any handler attached to this router will only trigger if:
    # 1. The chat ID matches the forum group
    # 2. It is a topic thread (message_thread_id is not None)
    router.message.filter(F.chat.id == forum_group_id, F.message_thread_id.is_not(None))
    router.edited_message.filter(
        F.chat.id == forum_group_id, F.message_thread_id.is_not(None)
    )

    # --- HANDLER 1: New Messages ---
    # We don't need to ask for conv_repo/msg_repo in arguments;
    # we use the ones passed to create_forum_router
    @router.message()
    async def from_group_topic(message: Message, bot: Bot):
        thread_id = message.message_thread_id

        # Access 'conv_repo' from outer scope
        conv = await conv_repo.get_by_thread(message.chat.id, thread_id)

        if not conv:
            return
        user_id = conv.user_id
        if message.from_user and message.from_user.is_bot:
            return

        reply_to_user_msg_id: Optional[int] = None

        # Access 'msg_repo' from outer scope
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

    # --- HANDLER 2: Edited Messages ---
    @router.edited_message()
    async def group_message_edited(message: Message, bot: Bot):
        # Access 'conv_repo' from outer scope
        conv = await conv_repo.get_by_thread(message.chat.id, message.message_thread_id)

        if not conv:
            return
        user_id = conv.user_id
        if message.from_user and message.from_user.is_bot:
            return

        # Access 'msg_repo' from outer scope
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

    return router
