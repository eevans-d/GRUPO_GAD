# -*- coding: utf-8 -*-
"""
Manejador para el comando /start.
"""

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from telegram import Bot, Chat, User
from typing import Any


async def start(update: Update, context: CallbackContext[Bot, Update, Chat, User]) -> None:
    """Envia un mensaje de bienvenida."""
    if update.message is None: # Added None check
        return
    await update.message.reply_text("Bienvenido al Bot de Gestión de Agentes (GAD).")


start_handler = CommandHandler("start", start)
