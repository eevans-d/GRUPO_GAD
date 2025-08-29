# -*- coding: utf-8 -*-
"""
Manejador para el comando /finalizar.
"""

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from src.bot.services.api import api_service


async def finalizar_tarea(update: Update, context: CallbackContext) -> None: # Added async
    """
    Finaliza una tarea.
    Formato: /finalizar <código_tarea>
    """
    if update.message is None: # Added None check
        return
    if update.message.from_user is None: # Added None check
        return

    user_id = update.message.from_user.id

    if not context.args:
        update.message.reply_text("Formato incorrecto. Uso: /finalizar <código_tarea>")
        return

    codigo_tarea = context.args[0]

    try:
        await api_service.finalize_task(task_code=codigo_tarea, telegram_id=user_id) # Added await
        update.message.reply_text(f"Tarea '{codigo_tarea}' finalizada exitosamente.")

    except Exception as e:
        update.message.reply_text(f"Error al finalizar la tarea: {e}")


finalizar_tarea_handler = CommandHandler("finalizar", finalizar_tarea)
