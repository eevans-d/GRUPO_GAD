# -*- coding: utf-8 -*-
"""
Manejador para el comando /crear.
"""

from datetime import datetime

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from src.bot.services.api import api_service
from src.schemas.tarea import TareaCreate
from src.shared.constants import TaskType


async def crear_tarea(update: Update, context: CallbackContext) -> None:
    """
    Crea una nueva tarea.
    Formato: /crear <código> <título> <tipo> <id_delegado> <id_asignado1> ...
    """
    if not update.message or not update.message.from_user or not context.args:
        if update.message:
            await update.message.reply_text(
                "Formato incorrecto. Uso: /crear <código> <título> <tipo> "
                "<id_delegado> <id_asignado1> [id_asignado2]..."
            )
        return

    user_id = update.message.from_user.id
    args = context.args

    if len(args) < 5:
        await update.message.reply_text(
            "Formato incorrecto. Uso:\n"
            "/crear <código> <título> <tipo> <id_delegado> <id_asignado1> "
            "[id_asignado2]..."
        )
        return

    try:
        codigo, titulo, tipo_str, delegado_id_str, *asignados_ids_str = args
        asignados_ids = [int(id_str) for id_str in asignados_ids_str]

        try:
            tipo = TaskType[tipo_str.upper()]
        except KeyError:
            valid_types = ", ".join([t.value for t in TaskType])
            await update.message.reply_text(
                f"Tipo de tarea inválido: {tipo_str}. "
                f"Tipos válidos: {valid_types}"
            )
            return

        task_in = TareaCreate(
            codigo=codigo,
            titulo=titulo,
            tipo=tipo,
            inicio_programado=datetime.now(),
            delegado_usuario_id=int(delegado_id_str),
            creado_por_usuario_id=user_id,
            efectivos_asignados=asignados_ids,
        )

        await api_service.create_task(task_in)
        await update.message.reply_text(f"Tarea '{codigo}' creada exitosamente.")

    except (ValueError, TypeError) as e:
        await update.message.reply_text(
            f"Error en los argumentos. Asegúrate de que los IDs sean números y "
            f"el formato sea correcto: {e}"
        )
    except Exception as e:
        await update.message.reply_text(f"Error al crear la tarea: {e}")


crear_tarea_handler = CommandHandler("crear", crear_tarea)