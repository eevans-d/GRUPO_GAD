# -*- coding: utf-8 -*-
"""
Manejador para el comando /finalizar.
"""

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from src.bot.services.api import api_service

def finalizar_tarea(update: Update, context: CallbackContext) -> None:
    """
    Finaliza una tarea.
    Formato: /finalizar <código_tarea>
    """
    user_id = update.message.from_user.id
    
    if not context.args:
        update.message.reply_text("Formato incorrecto. Uso: /finalizar <código_tarea>")
        return

    codigo_tarea = context.args[0]

    try:
        api_service.finalize_task(task_code=codigo_tarea, telegram_id=user_id)
        update.message.reply_text(f"Tarea '{codigo_tarea}' finalizada exitosamente.")

    except Exception as e:
        update.message.reply_text(f"Error al finalizar la tarea: {e}")


finalizar_tarea_handler = CommandHandler('finalizar', finalizar_tarea)
