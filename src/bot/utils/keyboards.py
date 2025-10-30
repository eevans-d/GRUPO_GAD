# -*- coding: utf-8 -*-
"""
Factory para construir teclados inline reutilizables con emojis semánticos.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Tuple, Dict, Any

from src.bot.utils.emojis import (
    TaskEmojis, ActionEmojis, NavigationEmojis, StatusEmojis
)


class KeyboardFactory:
    """Genera teclados inline estándar para el bot."""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Menú principal del bot con emojis mejorados."""
        keyboard = [
            [InlineKeyboardButton(
                f"{TaskEmojis.CREATE} Crear Nueva Tarea", 
                callback_data="menu:crear:start"
            )],
            [InlineKeyboardButton(
                f"{TaskEmojis.COMPLETE} Completar Tarea", 
                callback_data="menu:finalizar:start"
            )],
            [InlineKeyboardButton(
                f"{TaskEmojis.LIST} Ver Mis Tareas", 
                callback_data="menu:tareas:list:mis"
            )],
            [InlineKeyboardButton(
                f"{TaskEmojis.SEARCH} Buscar Tareas", 
                callback_data="menu:tareas:search"
            )],
            [InlineKeyboardButton(
                f"{StatusEmojis.INFO} Centro de Ayuda", 
                callback_data="menu:ayuda:general"
            )]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def task_types() -> InlineKeyboardMarkup:
        """Selector de tipos de tarea con emojis y descripciones."""
        keyboard = [
            [InlineKeyboardButton(
                f"{TaskEmojis.OPERATIONAL} Operativo - Tareas de campo", 
                callback_data="crear:tipo:OPERATIVO"
            )],
            [InlineKeyboardButton(
                f"{TaskEmojis.ADMINISTRATIVE} Administrativo - Gestión y oficina", 
                callback_data="crear:tipo:ADMINISTRATIVO"
            )],
            [InlineKeyboardButton(
                f"{TaskEmojis.EMERGENCY} Emergencia - Prioridad alta", 
                callback_data="crear:tipo:EMERGENCIA"
            )],
            [InlineKeyboardButton(
                f"{ActionEmojis.CANCEL} Cancelar Operación", 
                callback_data="crear:cancel"
            )]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirmation(action: str, entity_id: str) -> InlineKeyboardMarkup:
        """Teclado de confirmación genérico con emojis claros."""
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{StatusEmojis.SUCCESS} Sí, Confirmar", 
                    callback_data=f"{action}:confirm:{entity_id}:yes"
                ),
                InlineKeyboardButton(
                    f"{ActionEmojis.CANCEL} No, Cancelar", 
                    callback_data=f"{action}:confirm:{entity_id}:no"
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def task_confirmation() -> InlineKeyboardMarkup:
        """Teclado de confirmación específico para creación de tarea."""
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{StatusEmojis.SUCCESS} Sí, Crear Tarea", 
                    callback_data="crear:confirm:yes"
                ),
                InlineKeyboardButton(
                    f"{ActionEmojis.EDIT} Revisar y Editar", 
                    callback_data="crear:confirm:edit"
                )
            ],
            [InlineKeyboardButton(
                f"{ActionEmojis.CANCEL} Cancelar Todo", 
                callback_data="crear:cancel"
            )]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_button(callback_data: str = "menu:main") -> InlineKeyboardMarkup:
        """Botón de regreso al menú con emoji."""
        keyboard = [[InlineKeyboardButton(
            f"{NavigationEmojis.BACK} Volver al Menú", 
            callback_data=callback_data
        )]]
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
            nav_buttons.append(InlineKeyboardButton(
                f"{NavigationEmojis.LEFT} Anterior", 
                callback_data=f"page:{page-1}"
            ))
        if end < len(items):
            nav_buttons.append(InlineKeyboardButton(
                f"{NavigationEmojis.RIGHT} Siguiente", 
                callback_data=f"page:{page+1}"
            ))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton(
            f"{NavigationEmojis.BACK} Volver al Menú", 
            callback_data="menu:main"
        )])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def user_selector(
        users: List[Dict[str, Any]],
        action_prefix: str = "select:user"
    ) -> InlineKeyboardMarkup:
        """
        Selector de usuario (delegado o similar) con emojis.
        
        Args:
            users: Lista de usuarios con 'id' y 'nombre'
            action_prefix: Prefijo para callbacks (ej: 'crear:delegado')
        
        Returns:
            InlineKeyboardMarkup con lista de usuarios
        """
        from src.bot.utils.emojis import UserEmojis
        
        keyboard = []
        
        for user in users:
            user_id = user.get('id', 0)
            nombre = user.get('nombre', 'Usuario')
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{UserEmojis.AGENT} {nombre} (ID: {user_id})",
                    callback_data=f"{action_prefix}:{user_id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton(
            f"{ActionEmojis.CANCEL} Cancelar Operación", 
            callback_data="crear:cancel"
        )])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def multi_select_users(
        users: List[Dict[str, Any]],
        selected_ids: List[int],
        action_prefix: str = "crear:asignado"
    ) -> InlineKeyboardMarkup:
        """
        Selector multi-select de usuarios con checkboxes visuales.
        
        Args:
            users: Lista de usuarios con 'id' y 'nombre'
            selected_ids: Lista de IDs ya seleccionados
            action_prefix: Prefijo para callbacks
        
        Returns:
            InlineKeyboardMarkup con checkboxes
        """
        from src.bot.utils.emojis import ValidationEmojis
        
        keyboard = []
        
        for user in users:
            user_id = user.get('id', 0)
            nombre = user.get('nombre', 'Usuario')
            
            # Checkbox visual mejorado
            checkbox = ValidationEmojis.VALID if user_id in selected_ids else ValidationEmojis.OPTIONAL
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{checkbox} {nombre} (ID: {user_id})",
                    callback_data=f"{action_prefix}:toggle:{user_id}"
                )
            ])
        
        # Botón "Continuar" solo si hay al menos 1 seleccionado
        if selected_ids:
            keyboard.append([
                InlineKeyboardButton(
                    f"{NavigationEmojis.FORWARD} Continuar al Siguiente Paso",
                    callback_data=f"{action_prefix}:done"
                )
            ])
        
        keyboard.append([InlineKeyboardButton(
            f"{ActionEmojis.CANCEL} Cancelar Operación", 
            callback_data="crear:cancel"
        )])
        
        return InlineKeyboardMarkup(keyboard)
