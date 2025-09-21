# -*- coding: utf-8 -*-
"""
Punto de entrada principal para el bot de Telegram de GRUPO_GAD.
"""

import asyncio
import sys

from loguru import logger
from telegram.ext import ApplicationBuilder

from config.settings import settings
from src.bot.handlers import register_handlers

# --- Configuración de Loguru ---
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
)
logger.add(
    "logs/bot.log",
    rotation="10 MB",
    retention="7 days",
    enqueue=True,
    backtrace=True,
    diagnose=True,
    format="{time} {level} {message}",
)


async def main() -> None:
    """Inicia el bot."""
    if not settings.TELEGRAM_TOKEN:
        logger.critical(
            "Error: La variable de entorno TELEGRAM_TOKEN debe estar definida."
        )
        return

    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

    register_handlers(application)

    logger.info("Bot iniciado y escuchando...")
    await application.run_polling()  # type: ignore[func-returns-value]


if __name__ == "__main__":
    logger.info("Iniciando el bot...")
    asyncio.run(main())
