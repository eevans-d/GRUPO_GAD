# -*- coding: utf-8 -*-
"""
Sistema de confirmaciones consistentes con previsualización.

Este módulo implementa Quick Win #1: Confirmaciones consistentes
- Patrón estándar "Confirmar / Editar / Cancelar"
- Eliminar confirmaciones ciegas
- Previsualización clara antes de acciones críticas
"""

from typing import Optional, Dict, Any, List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.utils.emojis import StatusEmojis, ActionEmojis, TaskEmojis, UserEmojis
from src.bot.utils.validators import UnifiedCopy, CopyFormatter


class ConfirmationPattern:
    """
    Patrones de confirmación estandarizados.
    
    Quick Win #1: Patrón consistente en todos los flujos.
    """
    
    # Botones estándar
    BTN_CONFIRM = f"{StatusEmojis.SUCCESS} {UnifiedCopy.BUTTON_CONFIRMAR}"
    BTN_EDIT = f"{ActionEmojis.EDIT} {UnifiedCopy.BUTTON_EDITAR}"
    BTN_CANCEL = f"{ActionEmojis.CANCEL} {UnifiedCopy.BUTTON_CANCELAR}"
    BTN_BACK = f"{ActionEmojis.BACK} {UnifiedCopy.BUTTON_VOLVER}"
    
    @staticmethod
    def standard_confirmation(
        action: str,
        entity_id: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """
        Teclado de confirmación estándar: Confirmar / Editar / Cancelar.
        
        Quick Win #1: Patrón estandarizado en todo el sistema.
        
        Args:
            action: Acción a confirmar (crear, finalizar, etc.)
            entity_id: ID de entidad (opcional)
        
        Returns:
            Teclado inline con opciones estándar
        
        Example:
            >>> keyboard = ConfirmationPattern.standard_confirmation("crear")
        """
        entity_suffix = f":{entity_id}" if entity_id else ""
        
        keyboard = [
            [
                InlineKeyboardButton(
                    ConfirmationPattern.BTN_CONFIRM,
                    callback_data=f"{action}:confirm:yes{entity_suffix}"
                )
            ],
            [
                InlineKeyboardButton(
                    ConfirmationPattern.BTN_EDIT,
                    callback_data=f"{action}:confirm:edit{entity_suffix}"
                ),
                InlineKeyboardButton(
                    ConfirmationPattern.BTN_CANCEL,
                    callback_data=f"{action}:cancel{entity_suffix}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def simple_confirmation(
        action: str,
        entity_id: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """
        Confirmación simple: Sí / No.
        
        Args:
            action: Acción a confirmar
            entity_id: ID de entidad (opcional)
        
        Returns:
            Teclado inline simple
        """
        entity_suffix = f":{entity_id}" if entity_id else ""
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{StatusEmojis.SUCCESS} Sí",
                    callback_data=f"{action}:confirm:yes{entity_suffix}"
                ),
                InlineKeyboardButton(
                    f"{ActionEmojis.CANCEL} No",
                    callback_data=f"{action}:confirm:no{entity_suffix}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def destructive_confirmation(
        action: str,
        entity_id: Optional[str] = None
    ) -> InlineKeyboardMarkup:
        """
        Confirmación para acciones destructivas (eliminación).
        
        Args:
            action: Acción destructiva
            entity_id: ID de entidad
        
        Returns:
            Teclado con advertencia visual
        """
        entity_suffix = f":{entity_id}" if entity_id else ""
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{StatusEmojis.WARNING} Sí, Eliminar",
                    callback_data=f"{action}:confirm:delete{entity_suffix}"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{ActionEmojis.CANCEL} No, Mantener",
                    callback_data=f"{action}:cancel{entity_suffix}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)


class ConfirmationFormatter:
    """
    Formateadores de mensajes de confirmación con previsualización.
    
    Quick Win #1: Previsualización clara antes de confirmar.
    """
    
    @staticmethod
    def format_task_confirmation(task_data: Dict[str, Any]) -> str:
        """
        Formatea confirmación de tarea con previsualización completa.
        
        Quick Win #1: Eliminar confirmaciones ciegas con preview detallado.
        
        Args:
            task_data: Datos de la tarea a crear
        
        Returns:
            Mensaje formateado con preview completo
        
        Example:
            >>> msg = format_task_confirmation({
            ...     'codigo': 'OPE-2025-001',
            ...     'titulo': 'Reparar tubería',
            ...     'tipo': 'OPERATIVO',
            ...     'delegado_id': 101,
            ...     'asignados': [201, 202]
            ... })
        """
        # Extraer datos
        codigo = task_data.get('codigo', 'N/A')
        titulo = task_data.get('titulo', 'N/A')
        tipo = task_data.get('tipo', 'N/A')
        delegado_id = task_data.get('delegado_id')
        delegado_nombre = task_data.get('delegado_nombre', f'ID {delegado_id}')
        asignados = task_data.get('asignados', [])
        asignados_nombres = task_data.get('asignados_nombres', [])
        
        # Obtener emoji del tipo
        tipo_emoji = TaskEmojis.OPERATIONAL if tipo == "OPERATIVO" else \
                    TaskEmojis.ADMINISTRATIVE if tipo == "ADMINISTRATIVO" else \
                    TaskEmojis.EMERGENCY
        
        # Header con progreso
        message = (
            f"📋 *Crear Nueva Tarea* [Paso 6/6]\n"
            f"▰▰▰▰▰▰ 100%\n\n"
            f"{StatusEmojis.SUCCESS} *¡Casi listo! Revisa los detalles:*\n"
            f"{'━' * 35}\n\n"
        )
        
        # Datos de la tarea
        message += (
            f"🔤 *Código:* `{codigo}`\n"
            f"📝 *Título:* {titulo}\n"
            f"{tipo_emoji} *Tipo:* {tipo}\n\n"
        )
        
        # Delegado con terminología unificada
        message += f"{UserEmojis.SUPERVISOR} *{UnifiedCopy.DELEGADO_TERM}:* {delegado_nombre}\n"
        message += f"   _{UnifiedCopy.DELEGADO_DESC}_\n\n"
        
        # Asignados con terminología unificada
        if asignados_nombres:
            nombres_str = ', '.join(asignados_nombres[:3])
            if len(asignados_nombres) > 3:
                nombres_str += f" y {len(asignados_nombres) - 3} más"
            message += f"{UserEmojis.TEAM} *{UnifiedCopy.ASIGNADOS_TERM}:* {nombres_str}\n"
        elif asignados:
            message += f"{UserEmojis.TEAM} *{UnifiedCopy.ASIGNADOS_TERM}:* {len(asignados)} personas\n"
        else:
            message += f"{UserEmojis.TEAM} *{UnifiedCopy.ASIGNADOS_TERM}:* Sin asignar\n"
        
        message += f"   _{UnifiedCopy.ASIGNADOS_DESC}_\n\n"
        
        message += f"{'━' * 35}\n\n"
        
        # Advertencias y próximos pasos
        message += (
            f"{StatusEmojis.WARNING} *Importante:*\n"
            f"• Verifica que todos los datos sean correctos\n"
            f"• La tarea será notificada al equipo automáticamente\n"
            f"• Una vez creada, se registrará en el sistema\n\n"
            f"{StatusEmojis.INFO} *¿Todo correcto?*\n"
            f"• {ConfirmationPattern.BTN_CONFIRM} si los datos son correctos\n"
            f"• {ConfirmationPattern.BTN_EDIT} para modificar algo\n"
            f"• {ConfirmationPattern.BTN_CANCEL} para descartar\n"
        )
        
        return message
    
    @staticmethod
    def format_finalize_confirmation(task_data: Dict[str, Any]) -> str:
        """
        Formatea confirmación de finalización de tarea.
        
        Args:
            task_data: Datos de la tarea a finalizar
        
        Returns:
            Mensaje con previsualización
        """
        codigo = task_data.get('codigo', 'N/A')
        titulo = task_data.get('titulo', 'N/A')
        notas = task_data.get('notas', 'Sin notas adicionales')
        
        message = (
            f"{TaskEmojis.COMPLETE} *Finalizar Tarea*\n"
            f"{'━' * 35}\n\n"
            f"{StatusEmojis.INFO} *Estás por finalizar:*\n\n"
            f"🔤 *Código:* `{codigo}`\n"
            f"📝 *Título:* {titulo}\n"
            f"📋 *Notas:* {notas}\n\n"
            f"{'━' * 35}\n\n"
            f"{StatusEmojis.WARNING} *Confirmación requerida:*\n"
            f"Al finalizar esta tarea:\n"
            f"• Se marcará como completada en el sistema\n"
            f"• Se notificará al supervisor\n"
            f"• No podrá revertirse fácilmente\n\n"
            f"{StatusEmojis.INFO} *¿Confirmar finalización?*\n"
        )
        
        return message
    
    @staticmethod
    def format_delete_confirmation(
        item_type: str,
        item_id: str,
        item_name: Optional[str] = None
    ) -> str:
        """
        Formatea confirmación de eliminación (acción destructiva).
        
        Args:
            item_type: Tipo de ítem (Tarea, Usuario, etc.)
            item_id: ID del ítem
            item_name: Nombre del ítem (opcional)
        
        Returns:
            Mensaje con advertencia clara
        """
        display_name = item_name or item_id
        
        message = (
            f"{StatusEmojis.WARNING} *¡Acción Irreversible!*\n"
            f"{'━' * 35}\n\n"
            f"Estás por eliminar:\n\n"
            f"*{item_type}:* {display_name}\n"
            f"*ID:* `{item_id}`\n\n"
            f"{'━' * 35}\n\n"
            f"{StatusEmojis.ERROR} *Advertencia:*\n"
            f"• Esta acción NO puede revertirse\n"
            f"• Todos los datos asociados se perderán\n"
            f"• Las notificaciones se enviarán\n\n"
            f"{StatusEmojis.INFO} *¿Estás completamente seguro?*\n"
        )
        
        return message
    
    @staticmethod
    def format_edit_mode_message() -> str:
        """
        Mensaje cuando el usuario elige editar.
        
        Returns:
            Mensaje explicando modo edición
        """
        return (
            f"{ActionEmojis.EDIT} *Modo Edición Activado*\n\n"
            f"Puedes modificar los datos ingresados.\n\n"
            f"{StatusEmojis.INFO} *Opciones:*\n"
            f"• Usa los botones para navegar a cada paso\n"
            f"• Modifica solo lo necesario\n"
            f"• Regresa a confirmación cuando termines\n\n"
            f"{ActionEmojis.CANCEL} Cancelar: /cancelar"
        )
    
    @staticmethod
    def format_cancel_message() -> str:
        """
        Mensaje cuando el usuario cancela.
        
        Returns:
            Mensaje de cancelación amigable
        """
        return (
            f"{ActionEmojis.CANCEL} *Operación Cancelada*\n\n"
            f"No se realizaron cambios en el sistema.\n\n"
            f"{StatusEmojis.INFO} *¿Qué deseas hacer?*\n"
            f"• Usa /start para volver al menú principal\n"
            f"• Intenta la operación nuevamente cuando estés listo\n\n"
            f"Si necesitas ayuda, usa /ayuda"
        )


class ConfirmationHelper:
    """
    Helpers para manejo de confirmaciones en handlers.
    """
    
    @staticmethod
    def should_show_confirmation(action: str) -> bool:
        """
        Determina si una acción requiere confirmación.
        
        Quick Win #1: Lista centralizada de acciones que requieren confirmación.
        
        Args:
            action: Acción a verificar
        
        Returns:
            True si requiere confirmación
        """
        # Acciones que SIEMPRE requieren confirmación
        requires_confirmation = [
            'crear',
            'finalizar',
            'eliminar',
            'modificar',
            'asignar_masivo',
            'cancelar_masivo'
        ]
        
        return action in requires_confirmation
    
    @staticmethod
    def build_confirmation_message(
        action: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Construye mensaje de confirmación según el tipo de acción.
        
        Args:
            action: Tipo de acción
            data: Datos a confirmar
        
        Returns:
            Mensaje formateado
        """
        if action == 'crear':
            return ConfirmationFormatter.format_task_confirmation(data)
        elif action == 'finalizar':
            return ConfirmationFormatter.format_finalize_confirmation(data)
        elif action == 'eliminar':
            return ConfirmationFormatter.format_delete_confirmation(
                item_type=data.get('type', 'Item'),
                item_id=data.get('id', 'N/A'),
                item_name=data.get('name')
            )
        else:
            # Genérico
            return (
                f"{StatusEmojis.INFO} *Confirmación requerida*\n\n"
                f"¿Deseas continuar con esta acción?\n\n"
                f"Acción: {action}\n"
            )
    
    @staticmethod
    def build_confirmation_keyboard(
        action: str,
        entity_id: Optional[str] = None,
        is_destructive: bool = False
    ) -> InlineKeyboardMarkup:
        """
        Construye teclado de confirmación según el tipo de acción.
        
        Args:
            action: Tipo de acción
            entity_id: ID de entidad
            is_destructive: Si es acción destructiva
        
        Returns:
            Teclado apropiado
        """
        if is_destructive or action == 'eliminar':
            return ConfirmationPattern.destructive_confirmation(action, entity_id)
        elif action in ['crear', 'modificar']:
            return ConfirmationPattern.standard_confirmation(action, entity_id)
        else:
            return ConfirmationPattern.simple_confirmation(action, entity_id)


# Tests y ejemplos
if __name__ == "__main__":
    print("=== Tests de Sistema de Confirmaciones ===\n")
    
    # Test 1: Confirmación de tarea
    task_data = {
        'codigo': 'OPE-2025-001',
        'titulo': 'Reparar tubería principal edificio A',
        'tipo': 'OPERATIVO',
        'delegado_id': 101,
        'delegado_nombre': 'Juan Pérez',
        'asignados': [201, 202, 203],
        'asignados_nombres': ['María López', 'Pedro Gómez', 'Ana Martínez']
    }
    
    message = ConfirmationFormatter.format_task_confirmation(task_data)
    print(message)
    print("\n" + "="*50 + "\n")
    
    # Test 2: Teclado estándar
    keyboard = ConfirmationPattern.standard_confirmation("crear")
    print("Teclado estándar generado:")
    for row in keyboard.inline_keyboard:
        for button in row:
            print(f"  - {button.text} -> {button.callback_data}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Confirmación destructiva
    del_msg = ConfirmationFormatter.format_delete_confirmation(
        item_type="Tarea",
        item_id="OPE-2025-001",
        item_name="Reparar tubería"
    )
    print(del_msg)
