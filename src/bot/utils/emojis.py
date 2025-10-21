# -*- coding: utf-8 -*-
"""
Sistema centralizado de emojis para consistencia visual en el bot.

Este módulo define todos los emojis utilizados en el bot de Telegram,
organizados por categorías semánticas para facilitar su uso consistente
en toda la aplicación.

Uso:
    from src.bot.utils.emojis import TaskEmojis, ActionEmojis
    
    message = f"{TaskEmojis.CREATE} Nueva tarea creada"
    status = f"{StatusEmojis.SUCCESS} Operación exitosa"
"""


class TaskEmojis:
    """Emojis relacionados con tareas."""
    CREATE = "📋"
    COMPLETE = "✅"
    PENDING = "⏳"
    IN_PROGRESS = "🔄"
    CANCELLED = "❌"
    URGENT = "🚨"
    EMERGENCY = "🆘"
    OPERATIONAL = "🔧"
    ADMINISTRATIVE = "📄"
    SEARCH = "🔍"
    LIST = "📊"


class UserEmojis:
    """Emojis relacionados con usuarios y roles."""
    ADMIN = "👑"
    SUPERVISOR = "👤"
    AGENT = "🧑‍💼"
    DELEGATED = "📤"
    ASSIGNED = "📥"
    TEAM = "👥"
    ID = "🆔"


class ActionEmojis:
    """Emojis para acciones del bot."""
    START = "🚀"
    STOP = "🛑"
    EDIT = "✏️"
    DELETE = "🗑️"
    SAVE = "💾"
    SEND = "📤"
    RECEIVE = "📥"
    BACK = "🔙"
    FORWARD = "⏩"
    REFRESH = "🔄"
    CONFIRM = "✔️"
    CANCEL = "🚫"


class StatusEmojis:
    """Emojis para estados y feedback."""
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    LOADING = "⏳"
    DONE = "✔️"
    PENDING = "⏸️"
    ATTENTION = "⚡"


class NavigationEmojis:
    """Emojis para navegación."""
    MENU = "📱"
    HOME = "🏠"
    BACK = "◀️"
    FORWARD = "▶️"
    UP = "⬆️"
    DOWN = "⬇️"
    LEFT = "⬅️"
    RIGHT = "➡️"
    EXPAND = "📂"
    COLLAPSE = "📁"


class GeneralEmojis:
    """Emojis generales y misceláneos."""
    ROBOT = "🤖"
    WELCOME = "👋"
    HELP = "❓"
    SETTINGS = "⚙️"
    NOTIFICATION = "🔔"
    MESSAGE = "💬"
    CALENDAR = "📅"
    CLOCK = "🕐"
    LOCATION = "📍"
    PHONE = "📞"
    EMAIL = "📧"
    LINK = "🔗"
    KEY = "🔑"
    LOCK = "🔒"
    UNLOCK = "🔓"


class ProgressEmojis:
    """Emojis para barras de progreso y porcentajes."""
    FILLED = "▰"
    EMPTY = "▱"
    PERCENT_0 = "0️⃣"
    PERCENT_25 = "2️⃣5️⃣"
    PERCENT_50 = "5️⃣0️⃣"
    PERCENT_75 = "7️⃣5️⃣"
    PERCENT_100 = "💯"


class ValidationEmojis:
    """Emojis para validación de campos."""
    VALID = "✅"
    INVALID = "❌"
    REQUIRED = "⚠️"
    OPTIONAL = "🔘"
    FORMAT_OK = "✔️"
    FORMAT_ERROR = "❗"


# Mapeo de tipos de tarea a emojis
TASK_TYPE_EMOJI = {
    "OPERATIVO": TaskEmojis.OPERATIONAL,
    "ADMINISTRATIVO": TaskEmojis.ADMINISTRATIVE,
    "EMERGENCIA": TaskEmojis.EMERGENCY,
}

# Mapeo de estados de tarea a emojis
TASK_STATUS_EMOJI = {
    "pending": TaskEmojis.PENDING,
    "in_progress": TaskEmojis.IN_PROGRESS,
    "completed": TaskEmojis.COMPLETE,
    "cancelled": TaskEmojis.CANCELLED,
}


def get_task_emoji(task_type: str) -> str:
    """
    Obtiene el emoji correspondiente a un tipo de tarea.
    
    Args:
        task_type: Tipo de tarea (OPERATIVO, ADMINISTRATIVO, EMERGENCIA)
    
    Returns:
        Emoji correspondiente o emoji genérico si no se encuentra
    """
    return TASK_TYPE_EMOJI.get(task_type.upper(), TaskEmojis.CREATE)


def get_status_emoji(status: str) -> str:
    """
    Obtiene el emoji correspondiente a un estado de tarea.
    
    Args:
        status: Estado de la tarea (pending, in_progress, completed, cancelled)
    
    Returns:
        Emoji correspondiente o emoji genérico si no se encuentra
    """
    return TASK_STATUS_EMOJI.get(status.lower(), StatusEmojis.INFO)


def format_boolean(value: bool) -> str:
    """
    Formatea un valor booleano con emojis.
    
    Args:
        value: Valor booleano a formatear
    
    Returns:
        Emoji de éxito o error según el valor
    """
    return StatusEmojis.SUCCESS if value else StatusEmojis.ERROR


def format_progress(current: int, total: int, width: int = 6) -> str:
    """
    Crea una barra de progreso visual con emojis.
    
    Args:
        current: Valor actual
        total: Valor total
        width: Ancho de la barra (número de bloques)
    
    Returns:
        Barra de progreso con emojis
    """
    if total == 0:
        return ProgressEmojis.EMPTY * width
    
    percentage = current / total
    filled = int(percentage * width)
    empty = width - filled
    
    return (ProgressEmojis.FILLED * filled) + (ProgressEmojis.EMPTY * empty)
