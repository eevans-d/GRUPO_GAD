# -*- coding: utf-8 -*-
"""
Registra todos los manejadores de comandos y mensajes para el bot.
"""

from telegram.ext import Dispatcher  # type: ignore # Added type: ignore

from .commands import (  # type: ignore # Added type: ignore
    crear_tarea,
    finalizar_tarea,
    start,
)
from .messages import message_handler


def register_handlers(dp: Dispatcher) -> None:
    """
    Registra todos los manejadores en el dispatcher.
    """
    dp.add_handler(start.start_handler)
    dp.add_handler(crear_tarea.crear_tarea_handler)
    dp.add_handler(finalizar_tarea.finalizar_tarea_handler)
    dp.add_handler(message_handler.handler)
