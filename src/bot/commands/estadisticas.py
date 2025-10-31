# -*- coding: utf-8 -*-
"""
Comando /estadisticas - Muestra estadísticas personales del usuario.
"""

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from telegram import Bot, Chat, User
from loguru import logger
from datetime import datetime, timedelta
from typing import Any

from src.bot.services.api_service import ApiService
from config.settings import get_settings


async def estadisticas(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User]
) -> None:
    """
    Muestra estadísticas personales de tareas del usuario.
    
    Métricas incluidas:
    - Tareas creadas, activas, finalizadas
    - Tiempo promedio de finalización
    - Tareas por tipo
    - Productividad (tareas/día)
    - Racha de tareas completadas
    
    Args:
        update: Update de Telegram
        context: Contexto de la conversación
    """
    if not update.message or not update.effective_user:
        return
    
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Usuario"
    
    try:
        # Mostrar mensaje de loading
        loading_msg = await update.message.reply_text(
            "📊 Calculando tus estadísticas..."
        )
        
        # Obtener datos de la API
        settings = get_settings()
        api_service = ApiService(
            base_url=settings.API_BASE_URL,
            timeout=settings.HTTP_TIMEOUT
        )
        
        # Obtener tareas del usuario
        # En producción: stats = await api_service.get_user_statistics(user_id)
        # Para este ejemplo, simulamos con datos de tareas pendientes
        tareas = await api_service.get_user_pending_tasks(user_id)
        
        # Calcular estadísticas
        stats = _calculate_statistics(tareas, user_id)
        
        # Eliminar mensaje de loading
        await loading_msg.delete()
        
        # Formatear mensaje de estadísticas
        stats_text = _format_statistics(stats, user_name)
        
        await update.message.reply_text(
            stats_text,
            parse_mode="Markdown"
        )
        
        logger.info(
            f"Usuario {user_id} consultó estadísticas",
            user_id=user_id,
            total_tareas=stats['total_tareas']
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}", user_id=user_id)
        await update.message.reply_text(
            "❌ *Error al calcular estadísticas*\n\n"
            "No pudimos generar tus estadísticas en este momento.\n\n"
            "💡 Intenta nuevamente más tarde.\n"
            "Si el problema persiste, contacta al soporte.\n\n"
            "🔙 Volver al menú: /start",
            parse_mode="Markdown"
        )


def _calculate_statistics(tareas: list[Any], user_id: int) -> dict[str, Any]:
    """
    Calcula estadísticas a partir de las tareas del usuario.
    
    Args:
        tareas: Lista de tareas del usuario
        user_id: ID del usuario
        
    Returns:
        dict: Diccionario con todas las estadísticas calculadas
    """
    total_tareas = len(tareas)
    
    # Contar por estado
    activas = sum(1 for t in tareas if t.get('estado') == 'activa')
    finalizadas = sum(1 for t in tareas if t.get('estado') == 'finalizada')
    
    # Contar por tipo
    tipos = {}
    for tarea in tareas:
        tipo = tarea.get('tipo', 'Otro')
        tipos[tipo] = tipos.get(tipo, 0) + 1
    
    # Calcular tiempo promedio de finalización (simulado)
    # En producción, esto vendría de la API con fechas reales
    tiempo_promedio_dias = 3.5  # Simulado
    
    # Calcular productividad (tareas/día) - últimos 30 días
    # Simulado para este ejemplo
    dias_periodo = 30
    productividad = round(total_tareas / dias_periodo, 2) if total_tareas > 0 else 0
    
    # Calcular racha (días consecutivos con tareas completadas)
    racha_actual = 5  # Simulado
    
    # Tarea más común
    tipo_mas_comun = max(tipos.items(), key=lambda x: x[1])[0] if tipos else "N/A"
    
    # Estadísticas de esta semana
    # Simulado: en producción filtrar tareas de últimos 7 días
    tareas_semana = max(0, total_tareas // 4)  # ~25% del total como estimación
    
    return {
        'total_tareas': total_tareas,
        'activas': activas,
        'finalizadas': finalizadas,
        'tipos': tipos,
        'tiempo_promedio_dias': tiempo_promedio_dias,
        'productividad': productividad,
        'racha_actual': racha_actual,
        'tipo_mas_comun': tipo_mas_comun,
        'tareas_semana': tareas_semana
    }


def _format_statistics(stats: dict[str, Any], user_name: str) -> str:
    """
    Formatea estadísticas en un mensaje bonito de Telegram.
    
    Args:
        stats: Diccionario con estadísticas calculadas
        user_name: Nombre del usuario
        
    Returns:
        str: Mensaje formateado con Markdown
    """
    # Header
    text = (
        f"📊 *Estadísticas de {user_name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    # Resumen general
    text += (
        f"📋 *Resumen General*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Total de tareas: *{stats['total_tareas']}*\n"
        f"⚡ Activas: *{stats['activas']}*\n"
        f"✅ Finalizadas: *{stats['finalizadas']}*\n\n"
    )
    
    # Barra de progreso visual
    if stats['total_tareas'] > 0:
        porcentaje = int((stats['finalizadas'] / stats['total_tareas']) * 100)
        barra = _create_progress_bar(porcentaje)
        text += f"Completado: {barra} {porcentaje}%\n\n"
    
    # Tareas por tipo
    text += (
        f"📂 *Tareas por Tipo*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    if stats['tipos']:
        # Ordenar tipos por cantidad (descendente)
        sorted_tipos = sorted(stats['tipos'].items(), key=lambda x: x[1], reverse=True)
        for tipo, cantidad in sorted_tipos[:5]:  # Top 5
            emoji = _get_tipo_emoji(tipo)
            bar_chart = "▰" * min(cantidad, 10)  # Gráfico de barras ASCII
            text += f"{emoji} {tipo}: {bar_chart} {cantidad}\n"
        text += "\n"
    else:
        text += "No hay tareas registradas.\n\n"
    
    # Métricas de rendimiento
    text += (
        f"⚡ *Métricas de Rendimiento*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ Tiempo promedio: *{stats['tiempo_promedio_dias']} días*\n"
        f"📈 Productividad: *{stats['productividad']} tareas/día*\n"
        f"🔥 Racha actual: *{stats['racha_actual']} días*\n"
        f"🏆 Tipo más común: *{stats['tipo_mas_comun']}*\n\n"
    )
    
    # Estadísticas de esta semana
    text += (
        f"📅 *Esta Semana*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Tareas completadas: *{stats['tareas_semana']}*\n"
    )
    
    # Mensaje motivacional basado en rendimiento
    if stats['finalizadas'] >= 10:
        text += "\n🌟 *¡Excelente trabajo! Eres muy productivo.*\n"
    elif stats['finalizadas'] >= 5:
        text += "\n👏 *¡Buen trabajo! Sigue así.*\n"
    elif stats['finalizadas'] > 0:
        text += "\n💪 *¡Buen comienzo! Sigue avanzando.*\n"
    else:
        text += "\n🚀 *¡Empieza a finalizar tareas para ver tu progreso!*\n"
    
    # Footer con comandos útiles
    text += (
        f"\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 *Comandos útiles:*\n"
        f"• `/historial` - Ver tus tareas\n"
        f"• `/start` - Crear nueva tarea\n"
        f"• `/ayuda` - Obtener ayuda\n\n"
        f"📅 Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"🔙 Volver al menú: /start"
    )
    
    return text


def _create_progress_bar(percentage: int, length: int = 10) -> str:
    """
    Crea una barra de progreso visual en ASCII.
    
    Args:
        percentage: Porcentaje de progreso (0-100)
        length: Longitud de la barra en caracteres
        
    Returns:
        str: Barra de progreso formateada
    """
    filled = int((percentage / 100) * length)
    empty = length - filled
    return "▰" * filled + "░" * empty


def _get_tipo_emoji(tipo: str) -> str:
    """
    Obtiene emoji apropiado para el tipo de tarea.
    
    Args:
        tipo: Tipo de tarea
        
    Returns:
        str: Emoji correspondiente
    """
    emoji_map = {
        "Denuncia": "🚨",
        "Requerimiento": "📝",
        "Inspección": "🔍",
        "Otro": "📋",
        "Mantenimiento": "🔧",
        "Emergencia": "🚑"
    }
    return emoji_map.get(tipo, "📋")


# Handler para el comando
estadisticas_handler = CommandHandler("estadisticas", estadisticas)
