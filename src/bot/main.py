# -*- coding: utf-8 -*-
"""
Punto de entrada principal para el bot de Telegram de GRUPO_GAD.
"""

import logging
import asyncio # Added asyncio

from telegram.ext import Application, ApplicationBuilder # Changed import

from config.settings import settings
from src.bot.handlers import register_handlers

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main() -> None: # Changed to async def
    """Inicia el bot."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.critical(
            "Error: La variable de entorno TELEGRAM_BOT_TOKEN debe estar definida."
        )
        return

    # Create the Application and pass it your bot's token.
    application = (
        ApplicationBuilder.builder() # type: ignore # Added type: ignore
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Register all handlers
    register_handlers(application.dispatcher)

    # Start the Bot
    logger.info("Bot iniciado y escuchando...")
    await application.run_polling() # Changed to await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main()) # Changed to run async main
