# -*- coding: utf-8 -*-
"""
Manejador para el comando /crear.
"""

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from src.bot.services.api import api_service
from src.schemas.tarea import TareaCreate

def crear_tarea(update: Update, context: CallbackContext) -> None:
    """
    Crea una nueva tarea.
    Formato: /crear <código> <título> <tipo> <id_delegado> <id_asignado1> <id_asignado2> ...
    """
    user_id = update.message.from_user.id
    
    # This is a simplified version. In a real application, we would get the user's auth level
    # and perform more robust validation.
    
    args = context.args
    if len(args) < 5:
        update.message.reply_text(
            "Formato incorrecto. Uso:\n"
            "/crear <código> <título> <tipo> <id_delegado> <id_asignado1> [id_asignado2]..."
        )
        return

    try:
        codigo, titulo, tipo, delegado_id, *asignados_ids_str = args
        asignados_ids = [int(id_str) for id_str in asignados_ids_str]
        
        task_in = TareaCreate(
            codigo=codigo,
            titulo=titulo,
            tipo=tipo,
            delegado_usuario_id=int(delegado_id),
            creado_por_usuario_id=user_id, # Assuming the creator is the current user
            asignados_ids=asignados_ids,
        )

        api_service.create_task(task_in)
        update.message.reply_text(f"Tarea '{codigo}' creada exitosamente.")

    except (ValueError, TypeError):
        update.message.reply_text("Error en los argumentos. Asegúrate de que los IDs sean números.")
    except Exception as e:
        update.message.reply_text(f"Error al crear la tarea: {e}")


crear_tarea_handler = CommandHandler('crear', crear_tarea)
