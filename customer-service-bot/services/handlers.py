import logging
import re
from typing import Optional

from aiogram import F
from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ChatType
from aiogram.types import Message, ReplyParameters, TextQuote
from repos import ConversationRepo as ConvRepo, MessageLinkRepo as MsgRepo

router = Router()


def _extract_target_message_id(message: Message) -> Optional[int]:
    """Tries to find a message ID from reply objects or text links."""
    if message.reply_to_message:
        return message.reply_to_message.message_id

    text_src = message.text or message.caption or ""

    # Combined regex for cleaner lookups
    patterns = [r"/(\d+)(?:$|\D)", r"[?&](?:message|msg|m)=(\d+)"]

    for pattern in patterns:
        if match := re.search(pattern, text_src):
            try:
                return int(match.group(1))
            except ValueError:
                continue
    return None


def _create_reply_params(
    quote: Optional[TextQuote], target_msg_id: int
) -> ReplyParameters:
    """Constructs ReplyParameters cleanly."""
    kwargs = {"message_id": target_msg_id}

    if quote:
        # Truncate text to API limits
        kwargs["quote"] = (quote.text or "")[:1024]
        if quote.entities:
            kwargs["quote_entities"] = quote.entities
        if quote.position is not None:
            kwargs["quote_position"] = quote.position

    return ReplyParameters(**kwargs)


async def _relay_message(
    bot: Bot,
    msg_repo: MsgRepo,
    source_message: Message,
    target_chat_id: int,
    target_thread_id: int,
    target_reply_msg_id: Optional[int],
    user_id_for_link: int,
):
    """
    Core logic: Copies a message from A to B and saves the link.
    Abstractions allow this to work for both User->Group and Group->User.
    """

    reply_params = None

    if target_reply_msg_id:
        reply_params = _create_reply_params(source_message.quote, target_reply_msg_id)
    elif source_message.quote:
        # Log orphaned quotes for debugging
        logging.info(
            "Quote detected without resolvable target in message %s",
            source_message.message_id,
        )

    try:
        sent_msg = await bot.copy_message(
            chat_id=target_chat_id,
            message_thread_id=target_thread_id,
            from_chat_id=source_message.chat.id,
            message_id=source_message.message_id,
            reply_parameters=reply_params,
        )

        # Always link: (User ID, Forum ID, Thread ID, User Msg ID, Group Msg ID)
        # We need to know which ID is which.
        is_from_user = source_message.chat.type == ChatType.PRIVATE

        u_msg_id = source_message.message_id if is_from_user else sent_msg.message_id
        g_msg_id = sent_msg.message_id if is_from_user else source_message.message_id

        await msg_repo.link(
            user_id=user_id_for_link,
            forum_chat_id=target_chat_id if is_from_user else source_message.chat.id,
            thread_id=target_thread_id,
            user_message_id=u_msg_id,
            group_message_id=g_msg_id,
        )
    except Exception as e:
        logging.error(f"Failed to relay message: {e}")


# --- Handlers ---


@router.message(F.chat.type == ChatType.PRIVATE)
async def on_user_message(
    message: Message,
    bot: Bot,
    conv_repo: ConvRepo,
    msg_repo: MsgRepo,
    forum_group_id: int,
):
    user_id = message.from_user.id
    conv = await conv_repo.get_by_user(user_id)

    if not conv:
        # First time interaction: Create Topic
        name = message.from_user.full_name or message.from_user.username or f"{user_id}"
        topic = await bot.create_forum_topic(
            chat_id=forum_group_id, name=f"{name} {user_id}"
        )
        thread_id = topic.message_thread_id
        await conv_repo.create(user_id, forum_group_id, thread_id)
    else:
        thread_id = conv.thread_id

    # Resolve Reply Target
    quoted_id = _extract_target_message_id(message)
    target_reply_id = None
    if quoted_id:
        target_reply_id = await msg_repo.get_group_id(user_id, quoted_id)
        # Fallback: if we can't find it in DB, maybe it's a raw ID (rare but possible)
        if not target_reply_id and not message.reply_to_message:
            target_reply_id = quoted_id

    await _relay_message(
        bot=bot,
        msg_repo=msg_repo,
        source_message=message,
        target_chat_id=forum_group_id,
        target_thread_id=thread_id,
        target_reply_msg_id=target_reply_id,
        user_id_for_link=user_id,
    )


@router.message(F.message_thread_id)
async def on_group_message(
    message: Message, bot: Bot, conv_repo: ConvRepo, msg_repo: MsgRepo
):
    # Ignore bot's own messages to prevent loops
    if message.from_user and message.from_user.is_bot:
        return

    thread_id = message.message_thread_id
    conv = await conv_repo.get_by_thread(message.chat.id, thread_id)
    if not conv:
        return

    # Resolve Reply Target
    quoted_id = _extract_target_message_id(message)
    target_reply_id = None
    if quoted_id:
        target_reply_id = await msg_repo.get_user_id_by_group(
            message.chat.id, thread_id, quoted_id
        )

    await _relay_message(
        bot=bot,
        msg_repo=msg_repo,
        source_message=message,
        target_chat_id=conv.user_id,
        target_thread_id=None,  # Private chats don't have threads
        target_reply_msg_id=target_reply_id,
        user_id_for_link=conv.user_id,
    )


async def _send_edit_notification(
    bot: Bot,
    target_chat_id: int | str,
    target_thread_id: Optional[int],
    reply_to_message_id: int,
    text_content: str,
):
    """
    Formats and sends the 'UPDATE' notification to the target.
    """
    update_text = f"<b>UPDATE</b>\n\n{text_content}"

    try:
        await bot.send_message(
            chat_id=target_chat_id,
            message_thread_id=target_thread_id,
            text=update_text,
            reply_to_message_id=reply_to_message_id,
        )
    except Exception as e:
        # We log the specific error but don't crash the handler
        logging.error(f"Failed to send edit notification to {target_chat_id}: {e}")


# --- Edit Handlers ---


@router.edited_message(F.chat.type == ChatType.PRIVATE)
async def on_user_message_edited(
    message: Message, bot: Bot, conv_repo: ConvRepo, msg_repo: MsgRepo
):
    # 1. Validate User
    if not message.from_user:
        return
    user_id = message.from_user.id

    # 2. Check if conversation exists (optimization: fast fail)
    conv = await conv_repo.get_by_user(user_id)
    if not conv:
        return

    # 3. Find the specific message in the group to reply to
    group_msg_id = await msg_repo.get_group_id(user_id, message.message_id)
    if not group_msg_id:
        return

    # 4. Relay the update
    await _send_edit_notification(
        bot=bot,
        target_chat_id=conv.forum_chat_id,
        target_thread_id=conv.thread_id,
        reply_to_message_id=group_msg_id,
        text_content=message.text or message.caption or "",
    )


@router.edited_message(F.message_thread_id)
async def on_group_message_edited(
    message: Message, bot: Bot, conv_repo: ConvRepo, msg_repo: MsgRepo
):
    # 1. Ignore bot edits
    if message.from_user and message.from_user.is_bot:
        return

    # 2. Resolve Thread -> User
    conv = await conv_repo.get_by_thread(message.chat.id, message.message_thread_id)
    if not conv:
        return

    # 3. Find the specific message in the user chat to reply to
    user_msg_id = await msg_repo.get_user_id_by_group(
        group_id=message.chat.id,
        thread_id=message.message_thread_id,
        group_msg_id=message.message_id,
    )
    if not user_msg_id:
        return

    # 4. Relay the update
    await _send_edit_notification(
        bot=bot,
        target_chat_id=conv.user_id,
        target_thread_id=None,  # User chats (private) don't have threads
        reply_to_message_id=user_msg_id,
        text_content=message.text or message.caption or "",
    )


def setup_bot(dp: Dispatcher, **kwargs):
    dp.include_router(router)
    dp.workflow_data.update(kwargs)
