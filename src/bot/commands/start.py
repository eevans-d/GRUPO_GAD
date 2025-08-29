# -*- coding: utf-8 -*-
"""
Manejador para el comando /start.
"""

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext


async def start(update: Update, context: CallbackContext) -> None: # Added async
    """Envia un mensaje de bienvenida."""
    if update.message is None: # Added None check
        return
    update.message.reply_text("Bienvenido al Bot de Gestión de Agentes (GAD).")


start_handler = CommandHandler("start", start)
