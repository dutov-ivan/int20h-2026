from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import Conversation, MessageLink


class ConversationRepo:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_by_user(self, user_id: int):
        async with self.session_factory() as s:
            return await s.get(Conversation, user_id)

    async def get_by_thread(self, forum_chat_id: int, thread_id: int):
        async with self.session_factory() as s:
            q = select(Conversation).where(
                Conversation.forum_chat_id == forum_chat_id,
                Conversation.thread_id == thread_id,
            )
            r = await s.execute(q)
            return r.scalar_one_or_none()

    async def create(self, user_id: int, forum_chat_id: int, thread_id: int):
        async with self.session_factory() as s:
            conv = Conversation(
                user_id=user_id, forum_chat_id=forum_chat_id, thread_id=thread_id
            )
            s.add(conv)
            try:
                await s.commit()
                return conv
            except IntegrityError:
                await s.rollback()
                return await self.get_by_user(user_id)


class MessageLinkRepo:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def link(
        self,
        user_id: int,
        forum_chat_id: int,
        thread_id: int,
        user_message_id: int,
        group_message_id: int,
    ):
        async with self.session_factory() as s:
            ml = MessageLink(
                user_id=user_id,
                forum_chat_id=forum_chat_id,
                thread_id=thread_id,
                user_message_id=user_message_id,
                group_message_id=group_message_id,
            )
            s.add(ml)
            try:
                await s.commit()
            except IntegrityError:
                await s.rollback()

    async def get_group_id(self, user_id: int, user_message_id: int):
        async with self.session_factory() as s:
            q = select(MessageLink.group_message_id).where(
                MessageLink.user_id == user_id,
                MessageLink.user_message_id == user_message_id,
            )
            r = await s.execute(q)
            res = r.scalar_one_or_none()
            return int(res) if res is not None else None

    async def get_user_id_by_group(
        self, forum_chat_id: int, thread_id: int, group_message_id: int
    ):
        async with self.session_factory() as s:
            q = select(MessageLink.user_message_id).where(
                MessageLink.forum_chat_id == forum_chat_id,
                MessageLink.thread_id == thread_id,
                MessageLink.group_message_id == group_message_id,
            )
            r = await s.execute(q)
            res = r.scalar_one_or_none()
            return int(res) if res is not None else None
