# -*- coding: utf-8 -*-
"""
Comando /historial - Muestra el historial de tareas del usuario.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler
from telegram import Bot, Chat, User
from loguru import logger

from src.bot.services.api_service import ApiService
from config.settings import get_settings


async def historial(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User]
) -> None:
    """
    Muestra el historial de tareas del usuario con paginación.
    
    Args:
        update: Update de Telegram
        context: Contexto de la conversación
        
    Usage:
        /historial - Ver todas las tareas
        /historial activas - Ver solo tareas activas
        /historial finalizadas - Ver solo tareas finalizadas
    """
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    
    # Obtener filtro de argumentos
    args = context.args if context.args else []
    filtro = args[0].lower() if args else "todas"
    
    if filtro not in ["todas", "activas", "finalizadas"]:
        await update.message.reply_text(
            "⚠️ *Filtro inválido*\n\n"
            "Filtros disponibles:\n"
            "• `/historial todas` - Todas las tareas\n"
            "• `/historial activas` - Solo activas\n"
            "• `/historial finalizadas` - Solo finalizadas\n\n"
            "Por defecto se muestran todas.",
            parse_mode="Markdown"
        )
        return
    
    try:
        # Obtener tareas del usuario desde la API
        settings = get_settings()
        api_service = ApiService(
            base_url=settings.API_BASE_URL,
            timeout=settings.HTTP_TIMEOUT
        )
        
        # Mostrar mensaje de loading
        loading_msg = await update.message.reply_text(
            "🔍 Buscando tu historial de tareas..."
        )
        
        # Llamar a API (simulamos endpoint de historial)
        # En producción: tareas = await api_service.get_user_history(user_id, filtro)
        # Para este ejemplo, usamos get_user_pending_tasks y simulamos
        tareas = await api_service.get_user_pending_tasks(user_id)
        
        # Eliminar mensaje de loading
        await loading_msg.delete()
        
        if not tareas:
            emoji_map = {
                "todas": "📋",
                "activas": "⚡",
                "finalizadas": "✅"
            }
            await update.message.reply_text(
                f"{emoji_map[filtro]} *Historial de Tareas - {filtro.capitalize()}*\n\n"
                f"No tienes tareas {filtro} en este momento.\n\n"
                f"💡 *Tip:* Usa /start para crear una nueva tarea.",
                parse_mode="Markdown"
            )
            return
        
        # Formatear historial
        historial_text = _format_historial(tareas, filtro, page=1)
        
        # Crear teclado de paginación si hay más de 10 tareas
        keyboard = None
        if len(tareas) > 10:
            keyboard = _create_pagination_keyboard(page=1, total_pages=(len(tareas) // 10) + 1)
        
        await update.message.reply_text(
            historial_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(
            f"Usuario {user_id} consultó historial (filtro: {filtro})",
            user_id=user_id,
            filtro=filtro,
            total_tareas=len(tareas)
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo historial: {str(e)}", user_id=user_id)
        await update.message.reply_text(
            "❌ *Error al obtener historial*\n\n"
            "No pudimos cargar tu historial de tareas.\n\n"
            "💡 Intenta nuevamente en unos momentos.\n"
            "Si el problema persiste, contacta al soporte.\n\n"
            "🔙 Volver al menú: /start",
            parse_mode="Markdown"
        )


def _format_historial(tareas: list, filtro: str, page: int = 1) -> str:
    """
    Formatea el historial de tareas en texto bonito.
    
    Args:
        tareas: Lista de tareas del usuario
        filtro: Filtro aplicado (todas/activas/finalizadas)
        page: Página actual (para paginación)
        
    Returns:
        str: Texto formateado para Telegram
    """
    # Paginación: 10 tareas por página
    items_per_page = 10
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    tareas_pagina = tareas[start_idx:end_idx]
    
    total_tareas = len(tareas)
    total_pages = (total_tareas // items_per_page) + (1 if total_tareas % items_per_page else 0)
    
    # Header
    emoji_map = {
        "todas": "📋",
        "activas": "⚡",
        "finalizadas": "✅"
    }
    
    text = (
        f"{emoji_map[filtro]} *Historial de Tareas - {filtro.capitalize()}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Total: {total_tareas} tarea(s) | Página {page}/{total_pages}\n\n"
    )
    
    # Listar tareas
    for i, tarea in enumerate(tareas_pagina, start=start_idx + 1):
        # Estado con emoji
        estado = tarea.get('estado', 'activa')
        estado_emoji = "✅" if estado == "finalizada" else "⚡"
        
        # Fecha de creación
        fecha_creacion = tarea.get('fecha_creacion', 'N/A')
        if fecha_creacion != 'N/A':
            # Formatear fecha (asumimos ISO format)
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                fecha_str = dt.strftime("%d/%m/%Y")
            except:
                fecha_str = fecha_creacion[:10]
        else:
            fecha_str = "N/A"
        
        # Información de la tarea
        codigo = tarea.get('codigo', 'N/A')
        titulo = tarea.get('titulo', 'Sin título')
        tipo = tarea.get('tipo', 'Otro')
        
        # Truncar título si es muy largo
        if len(titulo) > 50:
            titulo = titulo[:47] + "..."
        
        text += (
            f"{i}. {estado_emoji} *{codigo}*\n"
            f"   📝 {titulo}\n"
            f"   📂 {tipo} • 📅 {fecha_str}\n\n"
        )
    
    # Footer
    text += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if total_pages > 1:
        text += f"📄 Mostrando {start_idx + 1}-{min(end_idx, total_tareas)} de {total_tareas}\n\n"
    
    text += (
        "💡 *Comandos útiles:*\n"
        "• `/historial todas` - Ver todas\n"
        "• `/historial activas` - Solo activas\n"
        "• `/historial finalizadas` - Solo finalizadas\n"
        "• `/estadisticas` - Ver tus estadísticas\n\n"
        "🔙 Volver al menú: /start"
    )
    
    return text


def _create_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """
    Crea teclado de paginación para navegación.
    
    Args:
        page: Página actual
        total_pages: Total de páginas
        
    Returns:
        InlineKeyboardMarkup: Teclado inline con botones de navegación
    """
    buttons = []
    
    # Botón anterior (si no es primera página)
    if page > 1:
        buttons.append(
            InlineKeyboardButton("◀️ Anterior", callback_data=f"hist_page_{page-1}")
        )
    
    # Indicador de página actual
    buttons.append(
        InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="hist_noop")
    )
    
    # Botón siguiente (si no es última página)
    if page < total_pages:
        buttons.append(
            InlineKeyboardButton("Siguiente ▶️", callback_data=f"hist_page_{page+1}")
        )
    
    # Botón de cerrar
    close_button = [
        InlineKeyboardButton("❌ Cerrar", callback_data="hist_close")
    ]
    
    return InlineKeyboardMarkup([buttons, close_button])


# Handler para el comando
historial_handler = CommandHandler("historial", historial)
