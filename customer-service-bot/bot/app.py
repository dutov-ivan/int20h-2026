import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from .config import Settings
from .database import core as db_core
from .handlers.forum import create_forum_router
from .handlers.user import create_user_router
from .database.requests import ConversationRepo, MessageLinkRepo

logger = logging.getLogger(__name__)


async def run():
    load_dotenv()
    settings = Settings()

    if not settings.BOT_TOKEN:
        raise SystemExit("Environment variable BOT_TOKEN is required")

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Initialize DB & repositories using existing project modules
    engine = db_core.make_engine(settings.DATABASE_URL)
    session_factory = db_core.make_session_factory(engine)
    await db_core.init_db(engine)

    conv_repo = ConversationRepo(session_factory)
    msg_repo = MessageLinkRepo(session_factory)

    forum_router = create_forum_router(settings.FORUM_GROUP_ID, conv_repo, msg_repo)

    user_router = create_user_router(settings.FORUM_GROUP_ID, conv_repo, msg_repo)

    dp.include_router(forum_router)
    dp.include_router(user_router)

    await dp.start_polling(bot)

    logger.info("Starting bot polling")
    await dp.start_polling(bot)
