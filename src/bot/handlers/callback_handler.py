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
        entity: Paso del wizard (tipo, cancel)
        params: Parámetros adicionales
    """
    if entity == "tipo":
        # Usuario seleccionó un tipo de tarea
        if not params:
            await query.edit_message_text("❌ Error: tipo de tarea no especificado")
            return
        
        tipo = params[0]
        
        # Guardar en contexto de usuario
        if 'wizard' not in context.user_data:
            context.user_data['wizard'] = {}
        
        context.user_data['wizard']['tipo'] = tipo
        
        # MVP: Mostrar mensaje de confirmación y volver al menú
        keyboard = KeyboardFactory.back_button()
        await query.edit_message_text(
            f"✅ *Tipo Seleccionado: {tipo}*\n\n"
            f"🚧 El wizard completo se implementará en la Fase 2.\n\n"
            f"Por ahora, usa el comando:\n"
            f"`/crear <codigo> <titulo> {tipo} <id_delegado> <id_asignado1> ...`",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif entity == "cancel":
        # Cancelar wizard
        if 'wizard' in context.user_data:
            del context.user_data['wizard']
        
        keyboard = KeyboardFactory.main_menu()
        await query.edit_message_text(
            "❌ *Creación Cancelada*\n\n"
            "Volviendo al menú principal...",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    else:
        await query.edit_message_text(f"❌ Acción de creación desconocida: {entity}")


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
