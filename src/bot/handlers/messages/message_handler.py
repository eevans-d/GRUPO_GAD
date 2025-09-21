# -*- coding: utf-8 -*-
"""
Manejador para mensajes de texto genéricos.
"""

import re

from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from typing import Any

from src.bot.services.api_service import ApiService


from telegram.ext import CallbackContext
from telegram import Bot, Chat, User
async def message_handler_func(update: Update, context: CallbackContext[Bot, Update, Chat, User]) -> None:
    """
    Procesa mensajes de texto para encontrar palabras clave.
    """
    if not update.message or not update.message.from_user or not update.message.text:
        return

    user_id = update.message.from_user.id
    msg_text = update.message.text

    # Check for "listo" keyword
    match = re.match(r"^(?i)listo\s+(\S+)", msg_text)
    if match:
        codigo_tarea = match.group(1)
        try:
            from config.settings import settings
            api_url = getattr(settings, "API_V1_STR", "/api/v1")
            token = None  # Si tienes un token, obténlo aquí
            api_service = ApiService(api_url, token)
            api_service.finalize_task(
                task_code=codigo_tarea, telegram_id=user_id
            )
            await update.message.reply_text(
                f"Tarea '{codigo_tarea}' finalizada exitosamente."
            )
        except Exception as e:
            await update.message.reply_text(f"Error al finalizar la tarea: {e}")


handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND, message_handler_func
)