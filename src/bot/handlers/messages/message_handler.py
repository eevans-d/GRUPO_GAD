# -*- coding: utf-8 -*-
"""
Manejador para mensajes de texto genéricos.
"""

import re
from telegram import Update
from telegram.ext import MessageHandler, Filters, CallbackContext

from src.bot.services.api import api_service

def message_handler_func(update: Update, context: CallbackContext) -> None:
    """
    Procesa mensajes de texto para encontrar palabras clave.
    """
    user_id = update.message.from_user.id
    msg_text = update.message.text

    # Check for "listo" keyword
    match = re.match(r'^(?i)listo\s+(\S+)', msg_text)
    if match:
        codigo_tarea = match.group(1)
        try:
            api_service.finalize_task(task_code=codigo_tarea, telegram_id=user_id)
            update.message.reply_text(f"Tarea '{codigo_tarea}' finalizada exitosamente.")
        except Exception as e:
            update.message.reply_text(f"Error al finalizar la tarea: {e}")

handler = MessageHandler(Filters.text & ~Filters.command, message_handler_func)
