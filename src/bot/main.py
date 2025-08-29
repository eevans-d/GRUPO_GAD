# -*- coding: utf-8 -*-
"""
Punto de entrada principal para el bot de Telegram de GRUPO_GAD.
"""

import logging

from telegram.ext import Updater

from config.settings import settings
from src.bot.handlers import register_handlers

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Inicia el bot."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.critical(
            "Error: La variable de entorno TELEGRAM_BOT_TOKEN debe estar definida."
        )
        return

    # Create the Updater and pass it your bot's token.
    updater = Updater(settings.TELEGRAM_BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register all handlers
    register_handlers(dispatcher)

    # Start the Bot
    updater.start_polling()
    logger.info("Bot iniciado y escuchando...")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
