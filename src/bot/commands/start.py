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
    
    # Obtener teclado del menú principal
    keyboard = KeyboardFactory.main_menu()
    
    # Mensaje de bienvenida
    welcome_text = (
        "🤖 *Bienvenido a GAD Bot*\n\n"
        "Sistema de Gestión de Agentes y Tareas.\n\n"
        "Selecciona una opción del menú:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


start_handler = CommandHandler("start", start)
