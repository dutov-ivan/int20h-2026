import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from services.handlers import setup_bot
from db import make_engine, make_session_factory, init_db
from repos import ConversationRepo, MessageLinkRepo

# 1. Config & Setup
logging.basicConfig(level=logging.INFO)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
FORUM_GROUP_ID_RAW = os.getenv("FORUM_GROUP_ID")

if not BOT_TOKEN:
    raise SystemExit("Environment variable BOT_TOKEN is required")

if not FORUM_GROUP_ID_RAW:
    raise SystemExit("Environment variable FORUM_GROUP_ID is required")

try:
    FORUM_GROUP_ID = int(FORUM_GROUP_ID_RAW)
except ValueError:
    raise SystemExit("Environment variable FORUM_GROUP_ID must be an integer")


async def main():
    # 2. Initialize Bot & Dispatcher
    # It is often cleaner to instantiate these inside main, but module-level is fine for simple scripts.
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # 3. Database Initialization
    # Use generic env var or default to local sqlite
    DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")

    engine = make_engine(DB_URL)
    session_factory = make_session_factory(engine)
    await init_db(engine)

    # 4. Instantiate Repositories
    conv_repo = ConversationRepo(session_factory)
    msg_repo = MessageLinkRepo(session_factory)

    # 5. Register Handlers & Inject Dependencies
    # This replaces the old 'register(...)' call.
    # We pass the repos and ID here, and they become available in every handler.
    setup_bot(
        dp=dp, conv_repo=conv_repo, msg_repo=msg_repo, forum_group_id=FORUM_GROUP_ID
    )

    # 6. Start Polling
    # 'allowed_updates' is optional but good practice to filter traffic
    logging.info("Starting bot...")
    await dp.start_polling(bot, allowed_updates=["message", "edited_message"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
