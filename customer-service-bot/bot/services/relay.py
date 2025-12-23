"""Relay logic (business logic that is independent from aiogram wiring).

Keep relay/copy helpers here so unit tests can target them easily.
"""

from typing import Optional
from aiogram.types import Message, ReplyParameters


def build_copy_kwargs_for_user(
    message: Message,
    forum_chat_id: int,
    thread_id: int,
    reply_to_group_id: Optional[int],
) -> dict:
    kwargs = dict(
        chat_id=forum_chat_id,
        message_thread_id=thread_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        reply_to_message_id=reply_to_group_id,
    )
    return kwargs


def build_copy_kwargs_for_group(
    message: Message, user_id: int, reply_to_user_msg_id: Optional[int]
) -> dict:
    return dict(
        chat_id=user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
        reply_to_message_id=reply_to_user_msg_id,
    )
