
from telegram import Bot
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN, CHAT_ID
import asyncio


def _ensure_chat():
    # CHAT_ID must be configured externally; do not attempt to prompt or create it
    if not CHAT_ID:
        raise RuntimeError("CHAT_ID must be set in config. Automatic creation or resolution is not supported.")

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required to validate the configured CHAT_ID")

    bot = Bot(BOT_TOKEN)
    from setup_chat import validate_chat
    res = asyncio.run(validate_chat(bot, CHAT_ID))
    print(res)
    if not res.get("ok"):
        raise RuntimeError(f"Chat validation failed: {res.get('error')}")
    if not res.get("has_forum"):
        raise RuntimeError("Configured chat does not appear to have topics/forums enabled. Enable topics in the chat settings.")

    return CHAT_ID


def main():
	chat_id = _ensure_chat()

	app = ApplicationBuilder().token(BOT_TOKEN).build()
     
     

	# TODO: add handlers that use chat_id if needed

	app.run_polling()


if __name__ == "__main__":
	main()
