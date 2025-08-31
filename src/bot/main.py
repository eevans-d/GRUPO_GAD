# -*- coding: utf-8 -*-
"""
Punto de entrada principal para el bot de Telegram de GRUPO_GAD.
"""

import sys
import asyncio
from loguru import logger

from telegram.ext import ApplicationBuilder

from config.settings import settings
from src.bot.handlers import register_handlers

# --- Configuración de Loguru ---
# Eliminar el handler por defecto para evitar duplicados
logger.remove()
# Añadir un handler para la consola
logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
# Añadir un handler para el archivo de log del bot
logger.add(
    "logs/bot.log",
    rotation="10 MB",
    retention="7 days",
    enqueue=True,
    backtrace=True,
    diagnose=True,
    format="{time} {level} {message}"
)


async def main() -> None:
    """Inicia el bot."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.critical(
            "Error: La variable de entorno TELEGRAM_BOT_TOKEN debe estar definida."
        )
        return

    # Crear la aplicación y pasarle el token del bot.
    application = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Registrar todos los handlers
    register_handlers(application)

    # Iniciar el Bot
    logger.info("Bot iniciado y escuchando...")
    await application.run_polling()


if __name__ == "__main__":
    logger.info("Iniciando el bot...")
    asyncio.run(main())