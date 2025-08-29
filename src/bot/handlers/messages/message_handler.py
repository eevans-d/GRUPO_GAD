# -*- coding: utf-8 -*-
"""
Manejador para mensajes de texto genéricos.
"""

import re
from telegram import Update
from telegram.ext import MessageHandler, filters, CallbackContext # Changed Filters to filters

from src.bot.services.api import api_service


async def message_handler_func(update: Update, context: CallbackContext) -> None: # Added async
    """
    Procesa mensajes de texto para encontrar palabras clave.
    """
    if update.message is None: # Added None check
        return
    if update.message.from_user is None: # Added None check
        return
    if update.message.text is None: # Added None check
        return

    user_id = update.message.from_user.id
    msg_text = update.message.text

    # Check for "listo" keyword
    match = re.match(r"^(?i)listo\s+(\S+)", msg_text)
    if match:
        codigo_tarea = match.group(1)
        try:
            await api_service.finalize_task(task_code=codigo_tarea, telegram_id=user_id) # Added await
            await update.message.reply_text( # Added await
                f"Tarea '{codigo_tarea}' finalizada exitosamente."
            )
        except Exception as e:
            await update.message.reply_text(f"Error al finalizar la tarea: {e}") # Added await


handler = MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler_func) # Changed to TEXT and COMMAND
