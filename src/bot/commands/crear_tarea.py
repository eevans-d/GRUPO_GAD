# -*- coding: utf-8 -*-
"""
Manejador para el comando /crear.
"""

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from src.bot.services.api import api_service
from src.schemas.tarea import TareaCreate
from src.shared.constants import TaskType # Added import for TaskType
from datetime import datetime # Added import for datetime


async def crear_tarea(update: Update, context: CallbackContext) -> None: # Added async
    """
    Crea una nueva tarea.
    Formato: /crear <código> <título> <tipo> <id_delegado> <id_asignado1> <id_asignado2> ...
    """
    if update.message is None: # Added None check
        return
    if update.message.from_user is None: # Added None check
        return
    if context.args is None: # Added None check
        await update.message.reply_text("Formato incorrecto. Uso: /crear <código> <título> <tipo> <id_delegado> <id_asignado1> [id_asignado2]...") # Added await
        return

    user_id = update.message.from_user.id
    args = context.args

    if len(args) < 5:
        await update.message.reply_text( # Added await
            "Formato incorrecto. Uso:\n"
            "/crear <código> <título> <tipo> <id_delegado> <id_asignado1> [id_asignado2]..."
        )
        return

    try:
        codigo, titulo, tipo_str, delegado_id_str, *asignados_ids_str = args # Renamed tipo to tipo_str, added _str suffix
        asignados_ids = [int(id_str) for id_str in asignados_ids_str]

        # Convert tipo_str to TaskType enum
        try:
            tipo = TaskType[tipo_str.upper()] # Convert string to enum
        except KeyError:
            await update.message.reply_text(f"Tipo de tarea inválido: {tipo_str}. Tipos válidos: {', '.join([t.value for t in TaskType])}") # Added await
            return

        task_in = TareaCreate(
            codigo=codigo,
            titulo=titulo,
            tipo=tipo, # Used TaskType enum
            inicio_programado=datetime.now(), # Added missing argument
            delegado_usuario_id=int(delegado_id_str),
            creado_por_usuario_id=user_id,  # Assuming the creator is the current user
            efectivos_asignados=asignados_ids, # Changed to efectivos_asignados
        )

        await api_service.create_task(task_in) # Added await
        await update.message.reply_text(f"Tarea '{codigo}' creada exitosamente.") # Added await

    except (ValueError, TypeError) as e:
        await update.message.reply_text(f"Error en los argumentos. Asegúrate de que los IDs sean números y el formato sea correcto: {e}") # Added await
    except Exception as e:
        await update.message.reply_text(f"Error al crear la tarea: {e}") # Added await


crear_tarea_handler = CommandHandler("crear", crear_tarea)
