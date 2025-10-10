# -*- coding: utf-8 -*-
"""
Registra todos los manejadores de comandos y mensajes para el bot.
"""

from telegram.ext import Application

from .commands import (  # type: ignore # Added type: ignore
    crear_tarea,
    finalizar_tarea,
    start,
)
from .messages import message_handler
from . import callback_handler


def register_handlers(app: Application) -> None:
    """
    Registra todos los manejadores en la aplicación del bot.
    
    Args:
        app: Instancia de Application de python-telegram-bot v20.x
    """
    # Comandos básicos
    app.add_handler(start.start_handler)
    app.add_handler(crear_tarea.crear_tarea_handler)
    app.add_handler(finalizar_tarea.finalizar_tarea_handler)
    
    # Callback query handler (botones interactivos)
    app.add_handler(callback_handler.callback_handler)
    
    # Message handler (debe ir al final para no interceptar comandos)
    app.add_handler(message_handler.handler)
