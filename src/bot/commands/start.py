# -*- coding: utf-8 -*-
"""
Manejador para el comando /start.
"""

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from telegram import Bot, Chat, User
from typing import Any

from src.bot.utils.keyboards import KeyboardFactory


async def start(update: Update, context: CallbackContext[Bot, Update, Chat, User]) -> None:
    """
    Envía un mensaje de bienvenida con menú interactivo.
    
    Args:
        update: Update de Telegram con el mensaje del usuario
        context: Contexto de la conversación
    """
    if update.message is None:  # Added None check
        return
    
    # Obtener información del usuario
    user = update.effective_user
    user_name = user.first_name if user else "Usuario"
    user_id = user.id if user else "N/A"
    
    # Obtener teclado del menú principal
    keyboard = KeyboardFactory.main_menu()
    
    # Mensaje de bienvenida personalizado
    welcome_text = (
        f"👋 *¡Hola, {user_name}!*\n\n"
        f"Bienvenido al *Sistema GAD*\n"
        f"Gestión de Agentes y Tareas\n\n"
        f"🆔 Usuario ID: `{user_id}`\n\n"
        f"📌 *¿Qué deseas hacer hoy?*\n"
        f"Selecciona una opción del menú:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


start_handler = CommandHandler("start", start)
