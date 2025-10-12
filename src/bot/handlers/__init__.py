# -*- coding: utf-8 -*-
"""
Registra todos los manejadores de comandos y mensajes para el bot.
"""

from telegram.ext import Application

from ..commands import (  # Import commands from parent bot module
    crear_tarea,
    finalizar_tarea,
    start,
    historial,
    estadisticas,
)
from .messages import message_handler
from . import callback_handler
from . import wizard_text_handler


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
    
    # Comandos bonus
    app.add_handler(historial.historial_handler)
    app.add_handler(estadisticas.estadisticas_handler)
    
    # Callback query handler (botones interactivos)
    app.add_handler(callback_handler.callback_handler)
    
    # Wizard text handler (inputs de texto durante wizard)
    # IMPORTANTE: Debe ir DESPUÉS de callback_handler pero ANTES de message_handler
    app.add_handler(wizard_text_handler.wizard_text_handler)
    
    # Message handler (debe ir al final para no interceptar comandos)
    app.add_handler(message_handler.handler)
