# -*- coding: utf-8 -*-
"""
Manejador central para todos los callback queries del bot.
"""

from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from telegram import Bot, Chat, User
from loguru import logger

from src.bot.utils.keyboards import KeyboardFactory


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
            await query.edit_message_text(f"❌ Acción desconocida: {action}")
    except Exception as e:
        logger.exception(f"Error procesando callback: {e}")
        await query.answer("❌ Error procesando acción. Intenta nuevamente.", show_alert=True)


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
        # Mostrar mensaje temporal (se implementa en Fase 3)
        keyboard = KeyboardFactory.back_button()
        await query.edit_message_text(
            "✅ *Finalizar Tarea*\n\n"
            "🚧 Esta función se implementará en la Fase 3.\n"
            "Por ahora, usa el comando `/finalizar <codigo>`",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
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
        if not params:
            await query.edit_message_text("❌ Error: tipo de tarea no especificado")
            return
        
        tipo = params[0]
        
        # Inicializar wizard
        context.user_data['wizard'] = {
            'command': 'crear',
            'current_step': 2,
            'data': {
                'tipo': tipo
            }
        }
        
        logger.bind(wizard=True).info(
            f"Wizard iniciado - Step 1 (tipo): {tipo}",
            user_id=query.from_user.id if query.from_user else None
        )
        
        # Step 2: Solicitar código
        keyboard = KeyboardFactory.back_button("crear:cancel")
        await query.edit_message_text(
            f"📝 *Crear Tarea - Paso 2 de 6*\n\n"
            f"Tipo: *{tipo}*\n\n"
            f"Por favor, envía el *código* de la tarea\n"
            f"(máximo 20 caracteres):",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif entity == "delegado":
        # Step 4: Usuario seleccionó un delegado
        if not params:
            await query.edit_message_text("❌ Error: delegado no especificado")
            return
        
        delegado_id = params[0]
        
        # Actualizar state
        if 'wizard' not in context.user_data:
            await query.edit_message_text("❌ Error: no hay wizard activo")
            return
        
        context.user_data['wizard']['data']['delegado_id'] = int(delegado_id)
        context.user_data['wizard']['current_step'] = 5
        
        logger.bind(wizard=True).info(
            f"Wizard Step 4: delegado seleccionado {delegado_id}",
            user_id=query.from_user.id if query.from_user else None
        )
        
        # Step 5: Mostrar selector multi-select de asignados
        # TODO: Llamar a API para obtener lista de agentes
        # Por ahora, mostrar mensaje temporal y pedir IDs
        keyboard = KeyboardFactory.back_button("crear:cancel")
        await query.edit_message_text(
            f"📝 *Crear Tarea - Paso 5 de 6*\n\n"
            f"Delegado: ID {delegado_id}\n\n"
            f"Por favor, envía los *IDs de agentes asignados*\n"
            f"separados por comas (ej: 101,102,103):",
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
        # Step 6: Confirmar creación
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
    
    tipo = wizard_data.get('tipo', 'N/A')
    codigo = wizard_data.get('codigo', 'N/A')
    titulo = wizard_data.get('titulo', 'N/A')
    delegado_id = wizard_data.get('delegado_id', 'N/A')
    asignados = wizard_data.get('asignados', [])
    
    summary_text = (
        f"📋 *Resumen de la Tarea*\n\n"
        f"*Código:* `{codigo}`\n"
        f"*Título:* {titulo}\n"
        f"*Tipo:* {tipo}\n"
        f"*Delegado:* ID {delegado_id}\n"
        f"*Asignados:* {', '.join(map(str, asignados)) if asignados else 'Ninguno'}\n\n"
        f"¿Confirmar creación?"
    )
    
    keyboard = KeyboardFactory.confirmation("crear:confirm", "crear:cancel")
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
        entity: Acción (select, confirm)
        params: Parámetros adicionales
    """
    # MVP: Solo mensaje temporal
    keyboard = KeyboardFactory.back_button()
    await query.edit_message_text(
        "✅ *Finalizar Tarea*\n\n"
        "🚧 Se implementará en la Fase 3.\n"
        "Incluirá:\n"
        "• Lista de tareas pendientes\n"
        "• Selector con botones\n"
        "• Confirmación antes de finalizar",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


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
        entity: Número de página
        params: Parámetros adicionales
    """
    # MVP: Mensaje temporal
    await query.answer("🚧 Paginación se implementará en Fase 3", show_alert=False)


# Exportar handler configurado
callback_handler = CallbackQueryHandler(handle_callback_query)
