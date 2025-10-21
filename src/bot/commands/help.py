# -*- coding: utf-8 -*-
"""
Manejador para el comando /ayuda y /help.
"""

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from telegram import Bot, Chat, User

from src.bot.utils.keyboards import KeyboardFactory
from src.bot.utils.emojis import StatusEmojis, ActionEmojis, TaskEmojis
from src.bot.handlers.wizard_text_handler import get_step_help


async def help_command(update: Update, context: CallbackContext[Bot, Update, Chat, User]) -> None:
    """
    Muestra ayuda general o ayuda contextual según el estado del wizard.
    
    Args:
        update: Update de Telegram con el mensaje del usuario
        context: Contexto de la conversación
    """
    if update.message is None:
        return
    
    # Verificar si hay un wizard activo
    wizard_data = context.user_data.get('wizard', {}) if context.user_data else {}
    current_step = wizard_data.get('current_step')
    
    if current_step:
        # Ayuda contextual para el paso actual del wizard
        help_text = get_step_help(current_step)
        keyboard = KeyboardFactory.back_button("crear:cancel")
    else:
        # Ayuda general
        help_text = (
            f"{StatusEmojis.INFO} *Sistema de Ayuda GAD*\n"
            f"{'─' * 35}\n\n"
            f"*COMANDOS DISPONIBLES:*\n\n"
            f"{ActionEmojis.START} `/start` - Menú principal\n"
            f"{TaskEmojis.CREATE} `/crear` - Crear tarea (texto)\n"
            f"{TaskEmojis.COMPLETE} `/finalizar` - Finalizar tarea\n"
            f"{TaskEmojis.LIST} `/historial` - Ver historial\n"
            f"{StatusEmojis.INFO} `/ayuda` - Mostrar esta ayuda\n\n"
            f"*BOTONES INTERACTIVOS:*\n\n"
            f"{TaskEmojis.CREATE} *Crear Tarea* - Wizard guiado paso a paso\n"
            f"{TaskEmojis.COMPLETE} *Finalizar Tarea* - Selector interactivo\n"
            f"{TaskEmojis.LIST} *Mis Tareas* - Lista de tareas asignadas\n"
            f"{TaskEmojis.SEARCH} *Buscar* - Búsqueda avanzada\n\n"
            f"*CONSEJOS:*\n\n"
            f"💡 Usa los botones del menú para acceso rápido\n"
            f"💡 Escribe `/ayuda` en cualquier momento\n"
            f"💡 Durante un wizard, recibirás ayuda contextual\n"
            f"💡 Puedes cancelar operaciones con el botón {ActionEmojis.CANCEL}\n\n"
            f"{'─' * 35}\n"
            f"¿Necesitas más ayuda? Contacta al administrador."
        )
        keyboard = KeyboardFactory.main_menu()
    
    await update.message.reply_text(
        help_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Crear handlers para ambos comandos /ayuda y /help
help_handler = CommandHandler("ayuda", help_command)
help_handler_alt = CommandHandler("help", help_command)
