import asyncio
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from .config import Settings
from .database import core as db_core

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

    # Repos now live in the package
    from .database.requests import ConversationRepo, MessageLinkRepo

    conv_repo = ConversationRepo(session_factory)
    msg_repo = MessageLinkRepo(session_factory)

    # Register handlers (deferred imports to avoid circulars)
    from .handlers.user import register_user_handlers
    from .handlers.forum import register_forum_handlers

    register_user_handlers(dp, bot, conv_repo, msg_repo, settings.FORUM_GROUP_ID)
    register_forum_handlers(dp, bot, conv_repo, msg_repo, settings.FORUM_GROUP_ID)

    logger.info("Starting bot polling")
    await dp.start_polling(bot)
