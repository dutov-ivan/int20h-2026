from sqlalchemy import BigInteger, Column, TIMESTAMP, UniqueConstraint, String
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"

    user_id = Column(BigInteger, primary_key=True, nullable=False)
    forum_chat_id = Column(BigInteger, nullable=False)
    thread_id = Column(BigInteger, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("forum_chat_id", "thread_id", name="idx_conversations_thread"),
    )


class MessageLink(Base):
    __tablename__ = "message_links"

    user_id = Column(BigInteger, nullable=False)
    user_message_id = Column(BigInteger, primary_key=True, nullable=False)

    forum_chat_id = Column(BigInteger, nullable=False)
    thread_id = Column(BigInteger, nullable=False)
    group_message_id = Column(BigInteger, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "forum_chat_id", "thread_id", "group_message_id", name="uq_group_msg"
        ),
    )


class BotMeta(Base):
    __tablename__ = "bot_meta"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
