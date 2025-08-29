# -*- coding: utf-8 -*-
"""
Manejador para el comando /start.
"""

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext


def start(update: Update, context: CallbackContext) -> None:
    """Envia un mensaje de bienvenida."""
    update.message.reply_text("Bienvenido al Bot de Gestión de Agentes (GAD).")


start_handler = CommandHandler("start", start)
