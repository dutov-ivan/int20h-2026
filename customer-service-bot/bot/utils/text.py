from typing import Optional
import re
from aiogram.types import Message, ReplyParameters, TextQuote


def get_text_from_message(message: Message) -> str:
    return message.text or message.caption or ""


def extract_quoted_message_id(message: Message) -> Optional[int]:
    # Prefer explicit reply_to_message
    if message.reply_to_message:
        return message.reply_to_message.message_id

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
