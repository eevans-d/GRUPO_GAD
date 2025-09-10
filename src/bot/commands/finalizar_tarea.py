# -*- coding: utf-8 -*-
"""
Manejador para el comando /finalizar.
"""

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from typing import Any

from src.bot.services.api_service import ApiService


from telegram.ext import CallbackContext
from telegram import Bot, Chat, User
async def finalizar_tarea(update: Update, context: CallbackContext[Bot, Update, Chat, User]) -> None:
    """
    Finaliza una tarea.
    Formato: /finalizar <código_tarea>
    """
    if not update.message or not update.message.from_user or not context.args:
        if update.message:
            await update.message.reply_text(
                "Formato incorrecto. Uso: /finalizar <código_tarea>"
            )
        return

    user_id = update.message.from_user.id
    codigo_tarea = context.args[0]

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


finalizar_tarea_handler = CommandHandler("finalizar", finalizar_tarea)