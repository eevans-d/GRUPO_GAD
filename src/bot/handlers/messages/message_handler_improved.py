# -*- coding: utf-8 -*-
"""
Manejador mejorado para mensajes de texto con control de atajos.

Quick Win #4: Control de atajos
- Deshabilita comandos texto libre durante wizard/confirmaciones
- Estados sensibles para prevenir acciones involuntarias
- Validación de entrada según contexto
"""

import re
from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from telegram import Bot, Chat, User
from loguru import logger

from config.settings import settings
from src.bot.services.api_service import ApiService
from src.bot.utils.wizard_state import (
    wizard_manager, can_process_text_input, is_wizard_active, WizardState
)
from src.bot.utils.validators import TaskValidator, UnifiedCopy
from src.bot.utils.error_messages import ErrorMessages, log_error, ErrorCategory
from src.bot.utils.ux_metrics import ux_metrics
from src.bot.utils.emojis import StatusEmojis, ActionEmojis
from src.bot.handlers.wizard_text_handler import get_step_header


async def message_handler_improved(
    update: Update, 
    context: CallbackContext[Bot, Update, Chat, User]
) -> None:
    """
    Procesa mensajes de texto con control de estado del wizard.
    
    Quick Win #4: Deshabilita atajos durante wizard/confirmaciones.
    
    Args:
        update: Update de Telegram
        context: Contexto de la conversación
    """
    if not update.message or not update.message.from_user or not update.message.text:
        return
    
    user_id = update.message.from_user.id
    msg_text = update.message.text.strip()
    
    # Quick Win #4: Verificar si hay wizard activo
    if is_wizard_active(user_id):
        await _handle_wizard_text_input(update, context, user_id, msg_text)
        return
    
    # Quick Win #4: Fuera del wizard, procesar atajos normales
    # Buscar patrón "listo + código"
    match = re.match(r"^(?i)listo\s+(\S+)", msg_text)
    if match:
        codigo_tarea = match.group(1)
        await _handle_listo_shortcut(update, context, user_id, codigo_tarea)
        return
    
    # Si no es un atajo conocido y no hay wizard, informar
    await update.message.reply_text(
        f"{StatusEmojis.INFO} *Mensaje no reconocido*\n\n"
        f"Para usar el bot, usa:\n"
        f"• /start - Menú principal\n"
        f"• /ayuda - Ver ayuda completa\n\n"
        f"💡 *Atajos disponibles:*\n"
        f"• `listo CÓDIGO` - Finalizar tarea\n"
        f"  Ejemplo: `listo OPE-2025-001`",
        parse_mode="Markdown"
    )


async def _handle_wizard_text_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    user_id: int,
    msg_text: str
) -> None:
    """
    Maneja entrada de texto durante wizard activo.
    
    Quick Win #3: Validaciones con copy unificado
    Quick Win #4: Control de entrada según estado
    Quick Win #5: Tracking de errores de validación
    
    Args:
        update: Update de Telegram
        context: Contexto
        user_id: ID de usuario
        msg_text: Texto ingresado
    """
    session = wizard_manager.get_session(user_id)
    state = session.state
    
    # Quick Win #4: Verificar si se permite entrada de texto
    if not can_process_text_input(user_id):
        # Estado no permite texto libre
        await update.message.reply_text(
            f"{StatusEmojis.WARNING} *Entrada no permitida en este momento*\n\n"
            f"Por favor usa los botones para continuar.\n\n"
            f"💡 Si necesitas cancelar, usa: /cancelar",
            parse_mode="Markdown"
        )
        return
    
    # Procesar según el paso del wizard
    if state == WizardState.ENTERING_CODE:
        await _process_codigo_input(update, context, user_id, msg_text)
    
    elif state == WizardState.ENTERING_TITLE:
        await _process_titulo_input(update, context, user_id, msg_text)
    
    elif state == WizardState.SELECTING_DELEGADO:
        await _process_delegado_input(update, context, user_id, msg_text)
    
    elif state == WizardState.SELECTING_ASIGNADOS:
        await _process_asignados_input(update, context, user_id, msg_text)
    
    else:
        # Estado inesperado
        await update.message.reply_text(
            f"{StatusEmojis.WARNING} *Estado inesperado del wizard*\n\n"
            f"Por favor usa /cancelar para reiniciar o /start para volver al menú.",
            parse_mode="Markdown"
        )


async def _process_codigo_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    user_id: int,
    codigo: str
) -> None:
    """
    Procesa entrada de código con validación.
    
    Quick Win #3: Validación de código con límite de 20 caracteres
    """
    # Quick Win #3: Validar código
    validation = TaskValidator.validate_codigo(codigo)
    
    if not validation.is_valid:
        # Quick Win #2: Mensaje de error específico
        error_msg = ErrorMessages.format_validation_error(
            field=validation.field_name or "Código",
            value=codigo,
            issue=validation.error_message or "Código inválido",
            suggestion=validation.suggestion or "",
            max_length=UnifiedCopy.MAX_CODIGO_LENGTH
        )
        
        await update.message.reply_text(
            error_msg,
            parse_mode="Markdown"
        )
        
        # Quick Win #5: Track error de validación
        ux_metrics.track_validation_error(
            user_id=user_id,
            field="codigo",
            error_type="format_error",
            step=2
        )
        
        log_error(
            ErrorCategory.VALIDATION,
            f"Código inválido: {codigo}",
            user_id=user_id
        )
        return
    
    # Código válido - guardar y avanzar
    if 'wizard' not in context.user_data:
        context.user_data['wizard'] = {'command': 'crear', 'data': {}}
    
    context.user_data['wizard']['data']['codigo'] = codigo
    context.user_data['wizard']['current_step'] = 3
    
    # Quick Win #4: Actualizar estado
    wizard_manager.advance_state(
        user_id,
        WizardState.ENTERING_TITLE,
        data={'codigo': codigo}
    )
    
    # Quick Win #5: Completar paso 2, iniciar paso 3
    ux_metrics.track_step_complete(user_id, 2)
    ux_metrics.track_step_start(user_id, 3)
    
    logger.bind(wizard=True).info(
        f"Código ingresado: {codigo}",
        user_id=user_id
    )
    
    # Solicitar título
    header = get_step_header(3, "Crear Nueva Tarea")
    
    await update.message.reply_text(
        f"{header}\n"
        f"✅ Código: `{codigo}`\n\n"
        f"✏️ *Ingresa el título descriptivo de la tarea:*\n\n"
        f"📝 *Consejos para un buen título:*\n"
        f"• Sé específico y claro\n"
        f"• Menciona la ubicación si aplica\n"
        f"• Máximo {UnifiedCopy.MAX_TITULO_LENGTH} caracteres\n"
        f"• Mínimo {UnifiedCopy.MIN_TITULO_LENGTH} caracteres\n\n"
        f"💬 *Ejemplo:* \"Reparar tubería principal edificio A\"\n\n"
        f"📊 Caracteres disponibles: {UnifiedCopy.MAX_TITULO_LENGTH}\n\n"
        f"{ActionEmojis.CANCEL} Cancelar: /cancelar",
        parse_mode="Markdown"
    )


async def _process_titulo_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    user_id: int,
    titulo: str
) -> None:
    """
    Procesa entrada de título con validación.
    
    Quick Win #3: Límite consistente de 100 caracteres
    """
    # Quick Win #3: Validar título
    validation = TaskValidator.validate_titulo(titulo)
    
    if not validation.is_valid:
        # Quick Win #2: Mensaje de error específico
        error_msg = ErrorMessages.format_validation_error(
            field=validation.field_name or "Título",
            value=titulo,
            issue=validation.error_message or "Título inválido",
            suggestion=validation.suggestion or "",
            max_length=UnifiedCopy.MAX_TITULO_LENGTH
        )
        
        await update.message.reply_text(
            error_msg,
            parse_mode="Markdown"
        )
        
        # Quick Win #5: Track error
        ux_metrics.track_validation_error(
            user_id=user_id,
            field="titulo",
            error_type="length_error",
            step=3
        )
        return
    
    # Título válido - guardar y avanzar
    context.user_data['wizard']['data']['titulo'] = titulo
    context.user_data['wizard']['current_step'] = 4
    
    wizard_manager.advance_state(
        user_id,
        WizardState.SELECTING_DELEGADO,
        data={'titulo': titulo}
    )
    
    ux_metrics.track_step_complete(user_id, 3)
    ux_metrics.track_step_start(user_id, 4)
    
    logger.bind(wizard=True).info(
        f"Título ingresado: {titulo}",
        user_id=user_id
    )
    
    # Quick Win #3: Solicitar delegado con terminología unificada
    header = get_step_header(4, "Crear Nueva Tarea")
    
    await update.message.reply_text(
        f"{header}\n"
        f"✅ Título: {titulo}\n\n"
        f"👤 *Selecciona el {UnifiedCopy.DELEGADO_TERM}:*\n\n"
        f"{StatusEmojis.INFO} *{UnifiedCopy.HELP_DELEGADO}*\n\n"
        f"📝 *Instrucción:*\n"
        f"Envía el ID del {UnifiedCopy.DELEGADO_TERM.lower()}\n"
        f"Ejemplo: `101`\n\n"
        f"{ActionEmojis.CANCEL} Cancelar: /cancelar",
        parse_mode="Markdown"
    )


async def _process_delegado_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    user_id: int,
    delegado_id_str: str
) -> None:
    """
    Procesa ID de delegado con validación.
    """
    validation = TaskValidator.validate_user_id(delegado_id_str)
    
    if not validation.is_valid:
        error_msg = ErrorMessages.format_validation_error(
            field=UnifiedCopy.DELEGADO_TERM,
            value=delegado_id_str,
            issue=validation.error_message or "ID inválido",
            suggestion=validation.suggestion or ""
        )
        
        await update.message.reply_text(
            error_msg,
            parse_mode="Markdown"
        )
        
        ux_metrics.track_validation_error(
            user_id=user_id,
            field="delegado_id",
            error_type="format_error",
            step=4
        )
        return
    
    delegado_id = int(delegado_id_str)
    
    context.user_data['wizard']['data']['delegado_id'] = delegado_id
    context.user_data['wizard']['current_step'] = 5
    
    wizard_manager.advance_state(
        user_id,
        WizardState.SELECTING_ASIGNADOS,
        data={'delegado_id': delegado_id}
    )
    
    ux_metrics.track_step_complete(user_id, 4)
    ux_metrics.track_step_start(user_id, 5)
    
    # Solicitar asignados
    header = get_step_header(5, "Crear Nueva Tarea")
    
    await update.message.reply_text(
        f"{header}\n"
        f"✅ {UnifiedCopy.DELEGADO_TERM}: ID {delegado_id}\n\n"
        f"👥 *Selecciona los {UnifiedCopy.ASIGNADOS_TERM}:*\n\n"
        f"{StatusEmojis.INFO} *{UnifiedCopy.HELP_ASIGNADOS}*\n\n"
        f"📝 *Instrucción:*\n"
        f"Envía IDs separados por comas o deja vacío\n"
        f"Ejemplos:\n"
        f"• `201, 202, 203`\n"
        f"• `/continuar` (sin asignados)\n\n"
        f"{ActionEmojis.CANCEL} Cancelar: /cancelar",
        parse_mode="Markdown"
    )


async def _process_asignados_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    user_id: int,
    asignados_str: str
) -> None:
    """
    Procesa lista de IDs de asignados.
    """
    validation, asignados_ids = TaskValidator.validate_user_ids_list(asignados_str)
    
    if not validation.is_valid:
        error_msg = ErrorMessages.format_validation_error(
            field=UnifiedCopy.ASIGNADOS_TERM,
            value=asignados_str,
            issue=validation.error_message or "IDs inválidos",
            suggestion=validation.suggestion or ""
        )
        
        await update.message.reply_text(
            error_msg,
            parse_mode="Markdown"
        )
        
        ux_metrics.track_validation_error(
            user_id=user_id,
            field="asignados",
            error_type="format_error",
            step=5
        )
        return
    
    context.user_data['wizard']['data']['asignados'] = asignados_ids
    context.user_data['wizard']['current_step'] = 6
    
    wizard_manager.advance_state(
        user_id,
        WizardState.CONFIRMING,
        data={'asignados': asignados_ids}
    )
    
    ux_metrics.track_step_complete(user_id, 5)
    ux_metrics.track_step_start(user_id, 6)
    
    # Quick Win #1: Mostrar confirmación con previsualización
    from src.bot.utils.confirmations import ConfirmationFormatter, ConfirmationPattern
    
    task_data = context.user_data['wizard']['data']
    confirmation_msg = ConfirmationFormatter.format_task_confirmation(task_data)
    keyboard = ConfirmationPattern.standard_confirmation("crear")
    
    await update.message.reply_text(
        confirmation_msg,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def _handle_listo_shortcut(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    user_id: int,
    codigo_tarea: str
) -> None:
    """
    Maneja atajo "listo + código" para finalizar tarea.
    
    Quick Win #4: Solo funciona si NO hay wizard activo.
    """
    try:
        api_service = ApiService(settings.API_V1_STR)
        api_service.finalize_task(
            task_code=codigo_tarea,
            telegram_id=user_id
        )
        
        await update.message.reply_text(
            f"{StatusEmojis.SUCCESS} *¡Tarea Finalizada!*\n\n"
            f"Tarea `{codigo_tarea}` finalizada exitosamente.\n\n"
            f"💡 Usa /start para volver al menú principal",
            parse_mode="Markdown"
        )
        
        logger.bind(shortcut=True).info(
            f"Tarea finalizada vía atajo: {codigo_tarea}",
            user_id=user_id
        )
        
    except Exception as e:
        error_msg = ErrorMessages.format_api_error(
            operation="finalizar la tarea",
            error_code="API_ERROR",
            technical_details=str(e)[:100]
        )
        
        await update.message.reply_text(
            error_msg,
            parse_mode="Markdown"
        )
        
        log_error(
            ErrorCategory.API_ERROR,
            f"Error en atajo listo: {str(e)}",
            user_id=user_id,
            context={'codigo': codigo_tarea}
        )


# Exportar handler configurado
handler_improved = MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    message_handler_improved
)
