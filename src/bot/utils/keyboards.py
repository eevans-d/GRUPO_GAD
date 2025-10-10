# -*- coding: utf-8 -*-
"""
Factory para construir teclados inline reutilizables.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Tuple


class KeyboardFactory:
    """Genera teclados inline estándar para el bot."""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Menú principal del bot."""
        keyboard = [
            [InlineKeyboardButton("📋 Crear Tarea", callback_data="menu:crear:start")],
            [InlineKeyboardButton("✅ Finalizar Tarea", callback_data="menu:finalizar:start")],
            [InlineKeyboardButton("📊 Mis Tareas", callback_data="menu:tareas:list:mis")],
            [InlineKeyboardButton("🔍 Buscar", callback_data="menu:tareas:search")],
            [InlineKeyboardButton("ℹ️ Ayuda", callback_data="menu:ayuda:general")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def task_types() -> InlineKeyboardMarkup:
        """Selector de tipos de tarea."""
        keyboard = [
            [InlineKeyboardButton("🔧 OPERATIVO", callback_data="crear:tipo:OPERATIVO")],
            [InlineKeyboardButton("📄 ADMINISTRATIVO", callback_data="crear:tipo:ADMINISTRATIVO")],
            [InlineKeyboardButton("🚨 EMERGENCIA", callback_data="crear:tipo:EMERGENCIA")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="crear:cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirmation(action: str, entity_id: str) -> InlineKeyboardMarkup:
        """Teclado de confirmación genérico."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data=f"{action}:confirm:{entity_id}:yes"),
                InlineKeyboardButton("❌ Cancelar", callback_data=f"{action}:confirm:{entity_id}:no")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_button(callback_data: str = "menu:main") -> InlineKeyboardMarkup:
        """Botón de regreso al menú."""
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data=callback_data)]]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def paginated_list(
        items: List[Tuple[str, str]], 
        page: int = 0, 
        page_size: int = 5,
        action_prefix: str = "select"
    ) -> InlineKeyboardMarkup:
        """
        Lista paginada de items.
        
        Args:
            items: Lista de tuplas (label, callback_value)
            page: Número de página actual (0-indexed)
            page_size: Cantidad de items por página
            action_prefix: Prefijo para el callback_data de cada item
        
        Returns:
            InlineKeyboardMarkup con items paginados y navegación
        """
        start = page * page_size
        end = start + page_size
        page_items = items[start:end]
        
        keyboard = []
        for label, callback_value in page_items:
            keyboard.append([InlineKeyboardButton(label, callback_data=f"{action_prefix}:{callback_value}")])
        
        # Navegación
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"page:{page-1}"))
        if end < len(items):
            nav_buttons.append(InlineKeyboardButton("➡️ Siguiente", callback_data=f"page:{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="menu:main")])
        
        return InlineKeyboardMarkup(keyboard)
