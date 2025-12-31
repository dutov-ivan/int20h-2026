"""Thin entrypoint that runs the packaged bot application.

This file delegates startup to `bot.app.run()` so all logic lives under
the `bot` package.
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv

load_dotenv()


if __name__ == "__main__":
    try:
        from bot.app import run

        run()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
