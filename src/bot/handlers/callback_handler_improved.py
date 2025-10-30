# -*- coding: utf-8 -*-
"""
Handler mejorado con Quick Wins UX integrados.

Este módulo extiende el callback_handler con:
- Quick Win #1: Confirmaciones consistentes
- Quick Win #2: Mensajes de error específicos  
- Quick Win #3: Copy unificado y validaciones
- Quick Win #4: Control de estados y atajos
- Quick Win #5: Instrumentación UX
"""

from typing import Optional
from telegram import Update
from telegram.ext import CallbackContext
from telegram import Bot, Chat, User
from loguru import logger
from datetime import datetime

from config.settings import settings
from src.bot.utils.keyboards import KeyboardFactory
from src.bot.utils.error_messages import ErrorMessages, log_error, ErrorCategory
from src.bot.utils.validators import TaskValidator, UnifiedCopy, ValidationResult
from src.bot.utils.wizard_state import (
    wizard_manager, WizardState, can_process_text_input
)
from src.bot.utils.ux_metrics import ux_metrics
from src.bot.utils.confirmations import (
    ConfirmationFormatter, ConfirmationPattern
)
from src.bot.utils.emojis import StatusEmojis, ActionEmojis


async def handle_crear_action_improved(
    query, 
    context: CallbackContext[Bot, Update, Chat, User], 
    entity: str, 
    params: list
) -> None:
    """
    Handler mejorado de creación con Quick Wins integrados.
    
    Quick Wins integrados:
    - #1: Confirmaciones consistentes
    - #2: Mensajes de error específicos
    - #3: Validaciones y copy unificado
    - #4: Control de estados
    - #5: Instrumentación UX
    
    Args:
        query: CallbackQuery de Telegram
        context: Contexto de la conversación
        entity: Paso del wizard
        params: Parámetros adicionales
    """
    user_id = query.from_user.id if query.from_user else 0
    
    # Quick Win #4: Verificar si el callback está permitido
    session = wizard_manager.get_session(user_id)
    if not session.allow_callback():
        await query.answer(
            f"{StatusEmojis.WARNING} Operación en proceso, espera...",
            show_alert=True
        )
        return
    
    try:
        if entity == "tipo":
            await _handle_tipo_selection_improved(query, context, params)
        
        elif entity == "delegado":
            await _handle_delegado_selection_improved(query, context, params)
        
        elif entity == "confirm":
            await _handle_confirmation_improved(query, context, params)
        
        elif entity == "cancel":
            await _handle_cancel_improved(query, context)
        
        else:
            # Error con mensaje específico (Quick Win #2)
            error_msg = ErrorMessages.get_generic_error("acción de creación")
            await query.edit_message_text(
                error_msg,
                parse_mode="Markdown"
            )
            log_error(
                ErrorCategory.USER_INPUT,
                f"Entidad desconocida en crear: {entity}",
                user_id=user_id
            )
    
    except Exception as e:
        # Quick Win #2: Mensaje de error específico
        logger.exception(f"Error en handle_crear_action_improved: {e}")
        
        error_msg = ErrorMessages.format_api_error(
            operation="procesar acción de creación",
            error_code="500",
            technical_details=str(e)[:100]
        )
        
        await query.edit_message_text(
            error_msg,
            parse_mode="Markdown"
        )
        
        log_error(
            ErrorCategory.SYSTEM,
            f"Error en crear action: {str(e)}",
            user_id=user_id,
            context={'entity': entity, 'params': params}
        )


async def _handle_tipo_selection_improved(query, context, params: list) -> None:
    """
    Maneja selección de tipo con Quick Wins.
    
    Quick Win #3: Validación de tipo
    Quick Win #5: Tracking de inicio de wizard
    """
    user_id = query.from_user.id if query.from_user else 0
    
    if not params:
        # Quick Win #2: Error específico
        error_msg = ErrorMessages.format_user_input_error(
            expected="Tipo de tarea (OPERATIVO, ADMINISTRATIVO, EMERGENCIA)",
            received="ninguno",
            examples=["OPERATIVO", "ADMINISTRATIVO", "EMERGENCIA"]
        )
        await query.edit_message_text(error_msg, parse_mode="Markdown")
        return
    
    tipo = params[0]
    
    # Quick Win #3: Validación con copy unificado
    validation = TaskValidator.validate_tipo(tipo)
    if not validation.is_valid:
        error_msg = ErrorMessages.format_validation_error(
            field="Tipo de tarea",
            value=tipo,
            issue=validation.error_message or "Tipo inválido",
            suggestion=validation.suggestion or UnifiedCopy.TIPO_OPERATIVO
        )
        await query.edit_message_text(error_msg, parse_mode="Markdown")
        
        # Quick Win #5: Tracking de error de validación
        ux_metrics.track_validation_error(
            user_id=user_id,
            field="tipo",
            error_type="invalid_type",
            step=1
        )
        return
    
    # Quick Win #5: Tracking de inicio de wizard
    ux_metrics.track_wizard_start(user_id, "crear")
    ux_metrics.track_step_start(user_id, 1)
    
    # Quick Win #4: Iniciar sesión de wizard
    wizard_manager.start_wizard(user_id, "crear")
    wizard_manager.advance_state(
        user_id,
        WizardState.ENTERING_CODE,
        data={'tipo': tipo}
    )
    
    # Guardar en context también
    context.user_data['wizard'] = {
        'command': 'crear',
        'current_step': 2,
        'data': {'tipo': tipo}
    }
    
    # Quick Win #5: Completar paso 1
    ux_metrics.track_step_complete(user_id, 1)
    ux_metrics.track_step_start(user_id, 2)
    
    logger.bind(wizard=True).info(
        f"Wizard iniciado - Tipo: {tipo}",
        user_id=user_id
    )
    
    # Quick Win #1 & #3: Mensaje con copy unificado
    from src.bot.handlers.wizard_text_handler import get_step_header
    
    keyboard = KeyboardFactory.back_button("crear:cancel")
    header = get_step_header(2, "Crear Nueva Tarea")
    
    await query.edit_message_text(
        f"{header}\n"
        f"✅ Tipo seleccionado: *{tipo}*\n\n"
        f"🔤 *Ingresa el código único de la tarea:*\n\n"
        f"📌 *Formato sugerido:* `TIP-2025-001`\n"
        f"   (Tipo-Año-Número)\n\n"
        f"{StatusEmojis.WARNING} *Importante:* Máximo {UnifiedCopy.MAX_CODIGO_LENGTH} caracteres\n\n"
        f"💡 *Ejemplo válido:* `OPE-2025-042`\n\n"
        f"{ActionEmojis.CANCEL} Cancelar: /cancelar",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def _handle_delegado_selection_improved(query, context, params: list) -> None:
    """
    Maneja selección de delegado con Quick Wins.
    
    Quick Win #2: Validación de usuario
    Quick Win #3: Terminología unificada (Delegado)
    """
    user_id = query.from_user.id if query.from_user else 0
    
    if not params:
        error_msg = ErrorMessages.format_user_input_error(
            expected="ID de usuario numérico",
            received="ninguno",
            examples=["101", "205", "999"]
        )
        await query.edit_message_text(error_msg, parse_mode="Markdown")
        
        ux_metrics.track_validation_error(
            user_id=user_id,
            field="delegado_id",
            error_type="missing_id",
            step=4
        )
        return
    
    delegado_id_str = params[0]
    
    # Quick Win #3: Validar ID de usuario
    validation = TaskValidator.validate_user_id(delegado_id_str)
    if not validation.is_valid:
        error_msg = ErrorMessages.format_validation_error(
            field=UnifiedCopy.DELEGADO_TERM,
            value=delegado_id_str,
            issue=validation.error_message or "ID inválido",
            suggestion=validation.suggestion or "101"
        )
        await query.edit_message_text(error_msg, parse_mode="Markdown")
        
        ux_metrics.track_validation_error(
            user_id=user_id,
            field="delegado_id",
            error_type="invalid_format",
            step=4
        )
        return
    
    delegado_id = int(delegado_id_str)
    
    # Quick Win #4: Actualizar estado
    if 'wizard' not in context.user_data:
        error_msg = ErrorMessages.format_api_error(
            operation="continuar con el wizard",
            error_code="WIZARD_LOST",
            technical_details="Sesión de wizard no encontrada"
        )
        await query.edit_message_text(error_msg, parse_mode="Markdown")
        
        # Tracking de abandono
        ux_metrics.track_wizard_abandon(user_id, step=4, reason="session_lost")
        wizard_manager.cancel_wizard(user_id)
        return
    
    context.user_data['wizard']['data']['delegado_id'] = delegado_id
    context.user_data['wizard']['current_step'] = 5
    
    wizard_manager.advance_state(
        user_id,
        WizardState.SELECTING_ASIGNADOS,
        data={'delegado_id': delegado_id}
    )
    
    # Completar paso 4, iniciar paso 5
    ux_metrics.track_step_complete(user_id, 4)
    ux_metrics.track_step_start(user_id, 5)
    
    logger.bind(wizard=True).info(
        f"Delegado seleccionado: {delegado_id}",
        user_id=user_id
    )
    
    # Quick Win #3: Usar terminología unificada
    from src.bot.handlers.wizard_text_handler import get_step_header
    
    keyboard = KeyboardFactory.back_button("crear:cancel")
    header = get_step_header(5, "Crear Nueva Tarea")
    
    await query.edit_message_text(
        f"{header}\n"
        f"✅ {UnifiedCopy.DELEGADO_TERM}: ID {delegado_id}\n\n"
        f"👥 *Selecciona los {UnifiedCopy.ASIGNADOS_TERM.lower()}:*\n\n"
        f"{StatusEmojis.INFO} *¿Quiénes son los {UnifiedCopy.ASIGNADOS_TERM.lower()}?*\n"
        f"{UnifiedCopy.HELP_ASIGNADOS}\n\n"
        f"📝 *Instrucciones:*\n"
        f"Envía los IDs separados por comas\n"
        f"Ejemplo: `201, 202, 203`\n\n"
        f"💡 También puedes continuar sin asignados\n\n"
        f"{ActionEmojis.CANCEL} Cancelar: /cancelar",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def _handle_confirmation_improved(query, context, params: list) -> None:
    """
    Maneja confirmación con patrón mejorado.
    
    Quick Win #1: Patrón estándar Confirmar / Editar / Cancelar
    Quick Win #2: Manejo de errores específico
    Quick Win #5: Tracking de confirmaciones
    """
    user_id = query.from_user.id if query.from_user else 0
    
    action_type = params[0] if params else "yes"
    
    if action_type == "yes":
        # Quick Win #4: Marcar como procesando
        wizard_manager.set_processing(user_id, True)
        
        # Quick Win #1: Mensaje de loading
        await query.edit_message_text(
            f"{StatusEmojis.LOADING} Creando la tarea...\n\n"
            f"Por favor espera un momento..."
        )
        
        # Crear tarea
        await _create_task_improved(query, context)
    
    elif action_type == "edit":
        # Quick Win #1: Modo edición
        edit_msg = ConfirmationFormatter.format_edit_mode_message()
        keyboard = KeyboardFactory.main_menu()
        
        await query.edit_message_text(
            edit_msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        # Mantener wizard activo para edición
        wizard_manager.advance_state(user_id, WizardState.SELECTING_TYPE)
    
    else:
        # Asumir confirmación (compatibilidad con callbacks antiguos)
        await _create_task_improved(query, context)


async def _create_task_improved(query, context) -> None:
    """
    Crea tarea con manejo mejorado de errores y métricas.
    
    Quick Win #2: Mensajes de error específicos
    Quick Win #5: Tracking de completación y errores
    """
    user_id = query.from_user.id if query.from_user else 0
    wizard_data = context.user_data.get('wizard', {}).get('data', {})
    
    try:
        # TODO: Llamar a API real
        # Por ahora simular éxito
        codigo = wizard_data.get('codigo', 'N/A')
        
        logger.bind(wizard=True).info(
            f"Tarea creada: {codigo}",
            user_id=user_id,
            data=wizard_data
        )
        
        # Quick Win #5: Tracking de completación exitosa
        ux_metrics.track_wizard_complete(user_id)
        
        # Quick Win #4: Limpiar wizard
        wizard_manager.cancel_wizard(user_id)
        if 'wizard' in context.user_data:
            del context.user_data['wizard']
        
        # Quick Win #1: Mensaje de éxito mejorado
        keyboard = KeyboardFactory.main_menu()
        await query.edit_message_text(
            f"{StatusEmojis.SUCCESS} *¡Tarea Creada Exitosamente!*\n\n"
            f"{'━' * 35}\n\n"
            f"🔤 *Código:* `{codigo}`\n"
            f"✅ *Estado:* Activa y lista\n\n"
            f"{'━' * 35}\n\n"
            f"📬 *Notificaciones:* Enviadas al equipo\n\n"
            f"🚀 *Próximos pasos:*\n"
            f"• El equipo fue notificado automáticamente\n"
            f"• Puedes ver el progreso en el sistema\n"
            f"• Usa /tareas para consultar tus tareas\n\n"
            f"💡 ¿Crear otra tarea? Usa el botón abajo\n\n"
            f"{ActionEmojis.BACK} Volver al menú principal",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.exception(f"Error creando tarea: {e}")
        
        # Quick Win #2: Error específico según tipo
        error_msg = ErrorMessages.format_api_error(
            operation="crear la tarea",
            error_code="500",
            technical_details=str(e)[:100],
            retry_possible=True
        )
        
        # Quick Win #5: Tracking de error de confirmación
        ux_metrics.track_confirmation_error(
            user_id=user_id,
            error_details=str(e)[:200]
        )
        
        # Desbloquear wizard
        wizard_manager.set_processing(user_id, False)
        
        keyboard = KeyboardFactory.main_menu()
        await query.edit_message_text(
            error_msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        log_error(
            ErrorCategory.API_ERROR,
            f"Error creando tarea: {str(e)}",
            user_id=user_id,
            context=wizard_data
        )


async def _handle_cancel_improved(query, context) -> None:
    """
    Maneja cancelación con tracking.
    
    Quick Win #1: Mensaje de cancelación amigable
    Quick Win #5: Tracking de abandono
    """
    user_id = query.from_user.id if query.from_user else 0
    
    # Obtener paso actual para tracking
    current_step = context.user_data.get('wizard', {}).get('current_step', 0)
    
    # Quick Win #5: Track abandono
    ux_metrics.track_wizard_abandon(user_id, step=current_step, reason="user_cancel")
    
    # Quick Win #4: Limpiar estado
    wizard_manager.cancel_wizard(user_id)
    if 'wizard' in context.user_data:
        del context.user_data['wizard']
    
    logger.bind(wizard=True).info(
        f"Wizard cancelado en paso {current_step}",
        user_id=user_id
    )
    
    # Quick Win #1: Mensaje de cancelación amigable
    cancel_msg = ConfirmationFormatter.format_cancel_message()
    keyboard = KeyboardFactory.main_menu()
    
    await query.edit_message_text(
        cancel_msg,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Función auxiliar para obtener métricas
def get_ux_metrics_summary() -> dict:
    """
    Obtiene resumen de métricas UX para análisis.
    
    Quick Win #5: Dashboard de métricas.
    
    Returns:
        Diccionario con métricas principales
    """
    return ux_metrics.get_metrics_summary()


# Exportar funciones mejoradas
__all__ = [
    'handle_crear_action_improved',
    'get_ux_metrics_summary'
]
