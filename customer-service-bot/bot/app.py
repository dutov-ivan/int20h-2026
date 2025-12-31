import logging
import asyncio  # Needed for polling mode
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from .config import Settings
from .database import core as db_core
from .handlers.forum import create_forum_router
from .handlers.user import create_user_router
from .database.requests import ConversationRepo, MessageLinkRepo

logger = logging.getLogger(__name__)

# --- HOOKS ---


def startup_webhook(bot: Bot, settings: Settings):
    """Hook to set the webhook URL (Production)"""

    async def on_startup():
        full_webhook_url = f"{settings.BASE_WEBHOOK_URL}{settings.WEBHOOK_PATH}"
        logging.info(f"Setting webhook to: {full_webhook_url}")
        await bot.set_webhook(
            full_webhook_url, secret_token=settings.WEBHOOK_SECRET_TOKEN
        )

    return on_startup


def startup_polling(bot: Bot):
    """Hook to remove webhook so polling works (Dev)"""

    async def on_startup():
        logging.info("Deleting webhook to start polling...")
        await bot.delete_webhook()

    return on_startup


def startup_db(engine):
    """Hook to initialize DB"""

    async def on_startup():
        logging.info("Initializing Database...")
        await db_core.init_db(engine)

    return on_startup


def run():
    settings = Settings()

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # 1. Setup Database & Repos
    engine = db_core.make_engine(settings.DATABASE_URL)
    session_factory = db_core.make_session_factory(engine)

    conv_repo = ConversationRepo(session_factory)
    msg_repo = MessageLinkRepo(session_factory)

    # 2. Setup Routers
    forum_router = create_forum_router(settings.FORUM_GROUP_ID, conv_repo, msg_repo)
    user_router = create_user_router(settings.FORUM_GROUP_ID, conv_repo, msg_repo)

    dp.include_router(forum_router)
    dp.include_router(user_router)

    # Register DB hook (Common for both modes)
    dp.startup.register(startup_db(engine))

    if settings.ENVIRONMENT == "development":
        logger.info("🚀 Starting in DEV mode (Polling)")

        # Prepare for polling (Remove old webhook)
        dp.startup.register(startup_polling(bot))

        # Start Polling
        # We use asyncio.run here because we are in a sync function
        # and need to start the loop manually for polling.
        asyncio.run(dp.start_polling(bot))

    else:
        logger.info("🌍 Starting in PRODUCTION mode (Webhooks)")

        # Prepare for webhook
        dp.startup.register(startup_webhook(bot, settings))

        # Setup Web Server
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=settings.WEBHOOK_SECRET_TOKEN,
        )
        webhook_requests_handler.register(app, path=settings.WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)

        # Start Server
        # web.run_app manages its own loop, so no asyncio.run needed
        web.run_app(app, host=settings.WEB_SERVER_HOST, port=settings.WEBSITES_PORT)
