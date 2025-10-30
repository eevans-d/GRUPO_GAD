# -*- coding: utf-8 -*-
"""
Manejador central para todos los callback queries del bot.
"""

from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from telegram import Bot, Chat, User
from loguru import logger

from config.settings import settings
from src.bot.utils.keyboards import KeyboardFactory
from src.bot.handlers.wizard_text_handler import get_step_header, format_task_summary

# Quick Wins imports
from src.bot.utils.error_messages import ErrorMessages, log_error, ErrorCategory
from src.bot.utils.validators import TaskValidator, UnifiedCopy
from src.bot.utils.wizard_state import wizard_manager, WizardState
from src.bot.utils.ux_metrics import ux_metrics
from src.bot.utils.confirmations import ConfirmationFormatter, ConfirmationPattern
from src.bot.utils.emojis import StatusEmojis, ActionEmojis


async def handle_callback_query(
    update: Update, 
    context: CallbackContext[Bot, Update, Chat, User]
) -> None:
    """
    Procesa todos los callbacks del bot usando patrón {action}:{entity}:{id}.
    
    Args:
        update: Update de Telegram con callback_query
        context: Contexto de la conversación
    """
    query = update.callback_query
    
    if query is None:
        return
    
    # Acknowledge inmediato para evitar spinner infinito
    await query.answer()
    
    callback_data = query.data
    
    if not callback_data:
        await query.edit_message_text("❌ Error: callback inválido")
        return
    
    parts = callback_data.split(":")
    
    if len(parts) < 2:
        await query.edit_message_text("❌ Error: formato de callback inválido")
        return
    
    action = parts[0]
    entity = parts[1]
    
    # Log estructurado
    logger.bind(callback=True).info(
        f"Callback procesado: {callback_data}",
        user_id=update.effective_user.id if update.effective_user else None,
        action=action,
        entity=entity
    )
    
    # Quick Win #4: Verificar estado del wizard
    user_id = update.effective_user.id if update.effective_user else 0
    session = wizard_manager.get_session(user_id)
    if not session.allow_callback():
        await query.answer(
            f"{StatusEmojis.WARNING} Operación en proceso, espera...",
            show_alert=True
        )
        return
    
    # Router de acciones
    try:
        if action == "menu":
            await handle_menu_action(query, context, entity, parts[2:])
        elif action == "crear":
            await handle_crear_action(query, context, entity, parts[2:])
        elif action == "finalizar":
            await handle_finalizar_action(query, context, entity, parts[2:])
        elif action == "page":
            await handle_pagination_action(query, context, entity, parts[2:])
        else:
            # Quick Win #2: Mensaje de error específico
            error_msg = ErrorMessages.get_generic_error("acción")
            await query.edit_message_text(error_msg, parse_mode="Markdown")
    except Exception as e:
        logger.exception(f"Error procesando callback: {e}")
        # Quick Win #2: Error específico con contexto
        error_msg = ErrorMessages.format_api_error(
            operation="procesar callback",
            error_code="500",
            technical_details=str(e)[:100]
        )
        await query.edit_message_text(error_msg, parse_mode="Markdown")
        log_error(ErrorCategory.SYSTEM, f"Error en callback: {str(e)}", user_id=user_id)


async def handle_menu_action(
    query, 
    context: CallbackContext[Bot, Update, Chat, User], 
    entity: str, 
    params: list
) -> None:
    """
    Maneja acciones del menú principal.
    
    Args:
        query: CallbackQuery de Telegram
        context: Contexto de la conversación
        entity: Entidad del menú (crear, finalizar, tareas, ayuda)
        params: Parámetros adicionales del callback
    """
    if entity == "main":
        # Volver al menú principal
        keyboard = KeyboardFactory.main_menu()
        await query.edit_message_text(
            "🤖 *Menú Principal*\n\nSelecciona una opción:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif entity == "crear":
        # Iniciar wizard de creación (MVP: solo mostrar tipos)
        keyboard = KeyboardFactory.task_types()
        await query.edit_message_text(
            "📝 *Crear Nueva Tarea*\n\n"
            "Paso 1: Selecciona el tipo de tarea:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif entity == "finalizar":
        # Iniciar flujo de finalización (Fase 3)
        # Llamar directamente a la lista de tareas pendientes
        await handle_finalizar_action(query, context, "list", [])
    
    elif entity == "tareas":
        # Mostrar lista de tareas (MVP: mensaje temporal)
        keyboard = KeyboardFactory.back_button()
        await query.edit_message_text(
            "📊 *Mis Tareas*\n\n"
            "🚧 Lista de tareas en desarrollo.\n"
            "Próximamente: visualización completa.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif entity == "ayuda":
        # Mostrar ayuda
        keyboard = KeyboardFactory.back_button()
        help_text = (
            "ℹ️ *Ayuda - GAD Bot*\n\n"
            "*Comandos disponibles:*\n"
            "• `/start` - Menú principal\n"
            "• `/crear` - Crear tarea (texto)\n"
            "• `/finalizar` - Finalizar tarea (texto)\n\n"
            "*Botones interactivos:*\n"
            "• 📋 Crear Tarea - Wizard guiado\n"
            "• ✅ Finalizar - Selector de tareas\n"
            "• 📊 Mis Tareas - Lista personal\n\n"
            "*Estado:*\n"
            "✅ Menú principal - Funcional\n"
            "🚧 Wizard de creación - En desarrollo\n"
            "🚧 Finalizar con botones - En desarrollo"
        )
        await query.edit_message_text(
            help_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    else:
        await query.edit_message_text(f"❌ Opción de menú desconocida: {entity}")


async def handle_crear_action(
    query, 
    context: CallbackContext[Bot, Update, Chat, User], 
    entity: str, 
    params: list
) -> None:
    """
    Maneja wizard de creación de tareas.
    
    Args:
        query: CallbackQuery de Telegram
        context: Contexto de la conversación
        entity: Paso del wizard (tipo, delegado, asignado, confirm, cancel)
        params: Parámetros adicionales
    """
    if entity == "tipo":
        # Step 1: Usuario seleccionó un tipo de tarea
        user_id = query.from_user.id if query.from_user else 0
        
        if not params:
            error_msg = ErrorMessages.format_user_input_error(
                expected="Tipo de tarea",
                examples=["OPERATIVO", "ADMINISTRATIVO", "EMERGENCIA"]
            )
            await query.edit_message_text(error_msg, parse_mode="Markdown")
            return
        
        tipo = params[0]
        
        # Quick Win #3: Validar tipo
        validation = TaskValidator.validate_tipo(tipo)
        if not validation.is_valid:
            error_msg = ErrorMessages.format_validation_error(
                field="Tipo",
                value=tipo,
                issue=validation.error_message or "Tipo inválido",
                suggestion=validation.suggestion
            )
            await query.edit_message_text(error_msg, parse_mode="Markdown")
            ux_metrics.track_validation_error(user_id, "tipo", "invalid_type", 1)
            return
        
        # Quick Win #5: Track inicio de wizard
        ux_metrics.track_wizard_start(user_id, "crear")
        ux_metrics.track_step_start(user_id, 1)
        ux_metrics.track_step_complete(user_id, 1)
        ux_metrics.track_step_start(user_id, 2)
        
        # Quick Win #4: Inicializar wizard state
        wizard_manager.start_wizard(user_id, "crear")
        wizard_manager.advance_state(user_id, WizardState.ENTERING_CODE, data={'tipo': tipo})
        
        # Inicializar wizard en context
        context.user_data['wizard'] = {
            'command': 'crear',
            'current_step': 2,
            'data': {'tipo': tipo}
        }
        
        logger.bind(wizard=True).info(
            f"Wizard iniciado - Step 1 (tipo): {tipo}",
            user_id=user_id
        )
        
        # Step 2: Solicitar código
        keyboard = KeyboardFactory.back_button("crear:cancel")
        header = get_step_header(2, "Crear Nueva Tarea")
        await query.edit_message_text(
            f"{header}\n"
            f"✅ Tipo: *{tipo}*\n\n"
            f"🔤 *Ingresa el código único de la tarea:*\n\n"
            f"📌 *Formato sugerido:* `TIP-2025-001`\n"
            f"⚠️ *Importante:* Máximo {UnifiedCopy.MAX_CODIGO_LENGTH} caracteres\n\n"
            f"{ActionEmojis.CANCEL} Cancelar: /cancelar",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif entity == "delegado":
        # Step 4: Usuario seleccionó un delegado
        user_id = query.from_user.id if query.from_user else 0
        
        if not params:
            error_msg = ErrorMessages.format_user_input_error(
                expected="ID de usuario",
                examples=["101", "205"]
            )
            await query.edit_message_text(error_msg, parse_mode="Markdown")
            return
        
        delegado_id_str = params[0]
        
        # Quick Win #3: Validar ID
        validation = TaskValidator.validate_user_id(delegado_id_str)
        if not validation.is_valid:
            error_msg = ErrorMessages.format_validation_error(
                field=UnifiedCopy.DELEGADO_TERM,
                value=delegado_id_str,
                issue=validation.error_message or "ID inválido",
                suggestion=validation.suggestion
            )
            await query.edit_message_text(error_msg, parse_mode="Markdown")
            ux_metrics.track_validation_error(user_id, "delegado_id", "invalid_format", 4)
            return
        
        # Actualizar state
        if 'wizard' not in context.user_data:
            error_msg = ErrorMessages.format_api_error(
                operation="continuar con el wizard",
                error_code="WIZARD_LOST"
            )
            await query.edit_message_text(error_msg, parse_mode="Markdown")
            ux_metrics.track_wizard_abandon(user_id, step=4, reason="session_lost")
            wizard_manager.cancel_wizard(user_id)
            return
        
        delegado_id = int(delegado_id_str)
        context.user_data['wizard']['data']['delegado_id'] = delegado_id
        context.user_data['wizard']['current_step'] = 5
        
        wizard_manager.advance_state(user_id, WizardState.SELECTING_ASIGNADOS, data={'delegado_id': delegado_id})
        ux_metrics.track_step_complete(user_id, 4)
        ux_metrics.track_step_start(user_id, 5)
        
        logger.bind(wizard=True).info(
            f"Delegado seleccionado: {delegado_id}",
            user_id=user_id
        )
        
        # Step 5: Solicitar asignados con terminología unificada
        keyboard = KeyboardFactory.back_button("crear:cancel")
        header = get_step_header(5, "Crear Nueva Tarea")
        await query.edit_message_text(
            f"{header}\n"
            f"✅ {UnifiedCopy.DELEGADO_TERM}: ID {delegado_id}\n\n"
            f"👥 *Selecciona los {UnifiedCopy.ASIGNADOS_TERM}:*\n\n"
            f"{StatusEmojis.INFO} {UnifiedCopy.HELP_ASIGNADOS}\n\n"
            f"📝 Envía IDs separados por comas\n"
            f"Ejemplo: `201, 202, 203`\n\n"
            f"{ActionEmojis.CANCEL} Cancelar: /cancelar",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif entity == "asignado":
        # Step 5: Toggle de asignado (multi-select)
        if not params or len(params) < 2:
            await query.answer("❌ Error: parámetros inválidos")
            return
        
        action_type = params[0]  # 'toggle' o 'done'
        
        if action_type == "toggle":
            user_id_str = params[1]
            
            # Obtener o inicializar lista de asignados
            if 'asignados' not in context.user_data['wizard']['data']:
                context.user_data['wizard']['data']['asignados'] = []
            
            asignados = context.user_data['wizard']['data']['asignados']
            user_id = int(user_id_str)
            
            # Toggle: añadir o quitar
            if user_id in asignados:
                asignados.remove(user_id)
            else:
                asignados.append(user_id)
            
            # TODO: Regenerar keyboard con checkboxes actualizados
            await query.answer(f"{'✅ Añadido' if user_id in asignados else '⬜ Quitado'}")
        
        elif action_type == "done":
            # Finalizar selección y continuar al resumen
            await _show_wizard_summary(query, context)
    
    elif entity == "confirm":
        # Step 6: Confirmar creación o editar
        action_type = params[0] if params else None
        
        if action_type == "yes":
            # Crear tarea
            await _create_task_from_wizard(query, context)
        elif action_type == "edit":
            # Volver al inicio del wizard para editar
            keyboard = KeyboardFactory.main_menu()
            await query.edit_message_text(
                "✏️ *Edición de Tarea*\n\n"
                "Función de edición en desarrollo.\n"
                "Por ahora, cancela y vuelve a crear la tarea.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            # Callback antiguo sin tipo específico, asumir confirmación
            await _create_task_from_wizard(query, context)
    
    elif entity == "cancel":
        # Cancelar wizard
        if 'wizard' in context.user_data:
            del context.user_data['wizard']
        
        logger.bind(wizard=True).info(
            "Wizard cancelado por usuario",
            user_id=query.from_user.id if query.from_user else None
        )
        
        keyboard = KeyboardFactory.main_menu()
        await query.edit_message_text(
            "❌ *Creación Cancelada*\n\n"
            "Volviendo al menú principal...",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    else:
        await query.edit_message_text(f"❌ Acción de creación desconocida: {entity}")


async def _show_wizard_summary(query, context: CallbackContext[Bot, Update, Chat, User]) -> None:
    """
    Muestra resumen del wizard antes de crear la tarea.
    
    Args:
        query: CallbackQuery de Telegram
        context: Contexto con datos del wizard
    """
    wizard_data = context.user_data.get('wizard', {}).get('data', {})
    
    # Usar función de formato mejorada
    summary_text = format_task_summary(wizard_data)
    
    keyboard = KeyboardFactory.task_confirmation()
    
    await query.edit_message_text(
        summary_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await query.edit_message_text(
        summary_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def _create_task_from_wizard(query, context: CallbackContext[Bot, Update, Chat, User]) -> None:
    """
    Crea la tarea en la API con los datos del wizard.
    
    Args:
        query: CallbackQuery de Telegram
        context: Contexto con datos del wizard
    """
    wizard_data = context.user_data.get('wizard', {}).get('data', {})
    
    # TODO: Llamar a API para crear tarea
    # from src.bot.services.api_service import ApiService
    # from src.schemas.tarea import TareaCreate
    # api_service = ApiService(settings.API_V1_STR)
    # task_create = TareaCreate(**wizard_data)
    # new_task = api_service.create_task(task_create)
    
    logger.bind(wizard=True).info(
        "Tarea creada desde wizard",
        user_id=query.from_user.id if query.from_user else None,
        data=wizard_data
    )
    
    # Limpiar wizard
    if 'wizard' in context.user_data:
        del context.user_data['wizard']
    
    # Mostrar éxito
    keyboard = KeyboardFactory.main_menu()
    await query.edit_message_text(
        f"✅ *¡Tarea Creada!*\n\n"
        f"Código: `{wizard_data.get('codigo', 'N/A')}`\n"
        f"Título: {wizard_data.get('titulo', 'N/A')}\n\n"
        f"La tarea ha sido registrada exitosamente.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def handle_finalizar_action(
    query, 
    context: CallbackContext[Bot, Update, Chat, User], 
    entity: str, 
    params: list
) -> None:
    """
    Maneja finalización de tareas.
    
    Args:
        query: CallbackQuery de Telegram
        context: Contexto de la conversación
        entity: Acción (list, select, confirm, cancel)
        params: Parámetros adicionales
    """
    from src.bot.services.api_service import ApiService
    
    if entity == "list":
        # Mostrar lista de tareas pendientes con paginación
        page = int(params[0]) if params else 0
        await _show_pending_tasks_list(query, context, page)
    
    elif entity == "select":
        # Usuario seleccionó una tarea para finalizar
        if not params:
            await query.answer("❌ Error: tarea no especificada", show_alert=True)
            return
        
        task_code = params[0]
        
        # Obtener detalles de la tarea desde API
        api_service = ApiService(settings.API_V1_STR)
        user_id = query.from_user.id if query.from_user else 0
        
        # Obtener todas las tareas del usuario
        tareas = api_service.get_user_pending_tasks(user_id)
        
        # Buscar la tarea seleccionada
        tarea_seleccionada = next((t for t in tareas if t.codigo == task_code), None)
        
        if not tarea_seleccionada:
            await query.answer("❌ Tarea no encontrada", show_alert=True)
            return
        
        # Guardar en contexto para confirmación
        context.user_data['finalizar_task'] = {
            'codigo': task_code,
            'titulo': tarea_seleccionada.titulo,
            'tipo': tarea_seleccionada.tipo
        }
        
        # Mostrar confirmación
        await _show_finalize_confirmation(query, context)
    
    elif entity == "confirm":
        # Usuario confirmó finalización
        await _finalize_task(query, context)
    
    elif entity == "cancel":
        # Usuario canceló finalización
        if 'finalizar_task' in context.user_data:
            del context.user_data['finalizar_task']
        
        # Volver a la lista
        await _show_pending_tasks_list(query, context, page=0)


async def handle_pagination_action(
    query, 
    context: CallbackContext[Bot, Update, Chat, User], 
    entity: str, 
    params: list
) -> None:
    """
    Maneja navegación de páginas en listas paginadas.
    
    Args:
        query: CallbackQuery de Telegram
        context: Contexto de la conversación
        entity: Acción de paginación (next, prev, o número de página)
        params: Parámetros adicionales (lista a paginar)
    """
    # El entity contiene la página de destino
    try:
        page = int(entity)
    except ValueError:
        await query.answer("❌ Página inválida", show_alert=True)
        return
    
    # Determinar qué lista mostrar basado en el contexto
    # Por ahora solo soportamos finalizar
    if 'finalizar_context' in context.user_data:
        await _show_pending_tasks_list(query, context, page)
    else:
        await query.answer("❌ Contexto de paginación perdido", show_alert=True)


async def _show_pending_tasks_list(
    query, 
    context: CallbackContext[Bot, Update, Chat, User], 
    page: int = 0
) -> None:
    """
    Muestra lista paginada de tareas pendientes del usuario.
    
    Args:
        query: CallbackQuery de Telegram
        context: Contexto de la conversación
        page: Número de página (0-indexed)
    """
    from src.bot.services.api_service import ApiService
    
    # Obtener user_id
    user_id = query.from_user.id if query.from_user else 0
    
    # Obtener tareas desde API
    api_service = ApiService(settings.API_V1_STR)
    tareas = api_service.get_user_pending_tasks(user_id)
    
    # Guardar contexto de finalización para paginación
    context.user_data['finalizar_context'] = True
    
    logger.bind(finalizar=True).info(
        f"Mostrando lista de tareas pendientes, página {page}",
        user_id=user_id,
        total_tareas=len(tareas)
    )
    
    # Si no hay tareas
    if not tareas:
        keyboard = KeyboardFactory.main_menu()
        await query.edit_message_text(
            "📭 *No tienes tareas pendientes*\n\n"
            "¡Buen trabajo! No hay tareas asignadas a ti en este momento.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return
    
    # Preparar items para el teclado paginado
    items = [
        (f"📋 {t.codigo} - {t.titulo[:30]}{'...' if len(t.titulo) > 30 else ''}", t.codigo)
        for t in tareas
    ]
    
    # Generar teclado paginado
    keyboard = KeyboardFactory.paginated_list(
        items=items,
        page=page,
        page_size=5,
        action_prefix="finalizar:select"
    )
    
    # Calcular estadísticas de página
    total_tareas = len(tareas)
    start_idx = page * 5
    end_idx = min(start_idx + 5, total_tareas)
    
    text = (
        f"✅ *Finalizar Tarea*\n\n"
        f"📊 Tienes *{total_tareas}* tarea{'s' if total_tareas > 1 else ''} pendiente{'s' if total_tareas > 1 else ''}.\n"
        f"Mostrando {start_idx + 1}-{end_idx} de {total_tareas}.\n\n"
        f"Selecciona la tarea que deseas finalizar:"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def _show_finalize_confirmation(
    query, 
    context: CallbackContext[Bot, Update, Chat, User]
) -> None:
    """
    Muestra pantalla de confirmación antes de finalizar tarea.
    
    Args:
        query: CallbackQuery de Telegram
        context: Contexto con datos de la tarea a finalizar
    """
    task_data = context.user_data.get('finalizar_task', {})
    
    if not task_data:
        await query.answer("❌ Error: datos de tarea no encontrados", show_alert=True)
        return
    
    codigo = task_data.get('codigo', 'N/A')
    titulo = task_data.get('titulo', 'N/A')
    tipo = task_data.get('tipo', 'N/A')
    
    confirmation_text = (
        f"⚠️ *Confirmar Finalización*\n\n"
        f"*Código:* `{codigo}`\n"
        f"*Título:* {titulo}\n"
        f"*Tipo:* {tipo}\n\n"
        f"¿Deseas marcar esta tarea como finalizada?"
    )
    
    keyboard = KeyboardFactory.confirmation("finalizar:confirm", "finalizar:cancel")
    
    await query.edit_message_text(
        confirmation_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def _finalize_task(
    query, 
    context: CallbackContext[Bot, Update, Chat, User]
) -> None:
    """
    Finaliza la tarea llamando a la API.
    
    Args:
        query: CallbackQuery de Telegram
        context: Contexto con datos de la tarea
    """
    from src.bot.services.api_service import ApiService
    
    task_data = context.user_data.get('finalizar_task', {})
    
    if not task_data:
        await query.answer("❌ Error: datos de tarea no encontrados", show_alert=True)
        return
    
    codigo = task_data.get('codigo')
    user_id = query.from_user.id if query.from_user else 0
    
    # Llamar a API
    api_service = ApiService(settings.API_V1_STR)
    
    try:
        tarea_finalizada = api_service.finalize_task(codigo, user_id)
        
        logger.bind(finalizar=True).info(
            f"Tarea finalizada exitosamente: {codigo}",
            user_id=user_id
        )
        
        # Limpiar contexto
        if 'finalizar_task' in context.user_data:
            del context.user_data['finalizar_task']
        if 'finalizar_context' in context.user_data:
            del context.user_data['finalizar_context']
        
        # Mostrar éxito
        keyboard = KeyboardFactory.main_menu()
        await query.edit_message_text(
            f"✅ *¡Tarea Finalizada!*\n\n"
            f"*Código:* `{tarea_finalizada.codigo}`\n"
            f"*Título:* {tarea_finalizada.titulo}\n\n"
            f"La tarea ha sido marcada como completada exitosamente.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.exception(f"Error finalizando tarea {codigo}: {e}")
        
        # Determinar mensaje de error
        error_msg = "❌ *Error al Finalizar*\n\n"
        
        if "404" in str(e) or "not found" in str(e).lower():
            error_msg += "La tarea no fue encontrada o ya fue finalizada."
        elif "403" in str(e) or "forbidden" in str(e).lower():
            error_msg += "No tienes permisos para finalizar esta tarea."
        else:
            error_msg += "Ocurrió un error al procesar la solicitud.\nIntenta nuevamente más tarde."
        
        keyboard = KeyboardFactory.main_menu()
        await query.edit_message_text(
            error_msg,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


# Exportar handler configurado
callback_handler = CallbackQueryHandler(handle_callback_query)
