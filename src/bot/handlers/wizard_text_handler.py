# -*- coding: utf-8 -*-
"""
Manejador de texto para wizard de creación/finalización de tareas.
"""

from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from telegram import Bot, Chat, User
from loguru import logger
from typing import Dict, Any

from src.bot.utils.keyboards import KeyboardFactory
from src.bot.utils.emojis import (
    TaskEmojis, StatusEmojis, ActionEmojis, ProgressEmojis,
    get_task_emoji
)


# ==================== UTILIDADES DE PROGRESS ====================

def get_progress_bar(step: int, total: int = 6) -> str:
    """
    Genera una barra de progreso visual para el wizard.
    
    Args:
        step: Paso actual (1-based)
        total: Total de pasos
    
    Returns:
        String con barra de progreso ASCII con emojis
    """
    filled = step
    empty = total - step
    percentage = int((step / total) * 100)
    
    bar = (ProgressEmojis.FILLED * filled) + (ProgressEmojis.EMPTY * empty)
    return f"{bar} {percentage}%"


def get_step_header(current_step: int, title: str = "Crear Nueva Tarea") -> str:
    """
    Genera header mejorado con progress y paso actual.
    
    Args:
        current_step: Paso actual (1-6)
        title: Título del wizard
    
    Returns:
        String formateado con progress
    """
    progress = get_progress_bar(current_step)
    return f"📋 *{title}* [Paso {current_step}/6]\n{progress}\n"


def format_task_summary(task_data: Dict[str, Any]) -> str:
    """
    Formatea el resumen de una tarea con diseño visual mejorado.
    
    Args:
        task_data: Diccionario con datos de la tarea (tipo, codigo, titulo, etc.)
    
    Returns:
        String con resumen formateado en Markdown con emojis semánticos
    """
    tipo = task_data.get('tipo', 'N/A')
    codigo = task_data.get('codigo', 'N/A')
    titulo = task_data.get('titulo', 'N/A')
    delegado_id = task_data.get('delegado_id', 'N/A')
    asignados = task_data.get('asignados', [])
    
    # Obtener emoji del tipo de tarea
    tipo_emoji = get_task_emoji(tipo)
    
    return (
        f"📋 *RESUMEN DE LA TAREA*\n"
        f"{'─' * 30}\n\n"
        f"🔤 *Código:* `{codigo}`\n"
        f"📝 *Título:* {titulo}\n"
        f"{tipo_emoji} *Tipo:* {tipo}\n"
        f"👤 *Delegado:* ID `{delegado_id}`\n"
        f"👥 *Asignados:* {', '.join(map(str, asignados)) if asignados else 'Ninguno'}\n\n"
        f"{'─' * 30}\n"
        f"⚠️ *¿Confirmar creación?*\n"
        f"Revisa los datos antes de continuar."
    )


def get_step_help(step: int) -> str:
    """
    Retorna texto de ayuda contextual para cada paso del wizard.
    
    Args:
        step: Número de paso del wizard (1-6)
    
    Returns:
        String con ayuda específica para el paso
    """
    help_texts = {
        1: (
            f"{StatusEmojis.INFO} *Ayuda: Tipo de Tarea*\n\n"
            f"{TaskEmojis.OPERATIONAL} *OPERATIVO:* Tareas técnicas y de campo\n"
            f"{TaskEmojis.ADMINISTRATIVE} *ADMINISTRATIVO:* Tareas de oficina y gestión\n"
            f"{TaskEmojis.EMERGENCY} *EMERGENCIA:* Situaciones urgentes que requieren atención inmediata\n\n"
            f"Selecciona el tipo que mejor describe la tarea."
        ),
        2: (
            f"{StatusEmojis.INFO} *Ayuda: Código de Tarea*\n\n"
            f"📌 *Formato sugerido:* `TIPO-AÑO-NÚMERO`\n"
            f"✅ *Ejemplos válidos:*\n"
            f"  • `OPE-2025-001`\n"
            f"  • `ADM-2025-042`\n"
            f"  • `EMG-2025-005`\n\n"
            f"⚠️ Máximo 20 caracteres\n"
            f"⚠️ Debe ser único en el sistema"
        ),
        3: (
            f"{StatusEmojis.INFO} *Ayuda: Título de Tarea*\n\n"
            f"✍️ Escribe un título descriptivo y claro.\n\n"
            f"✅ *Buenas prácticas:*\n"
            f"  • Sé específico y conciso\n"
            f"  • Incluye acción y objetivo\n"
            f"  • Máximo 100 caracteres\n\n"
            f"📝 *Ejemplos:*\n"
            f"  • 'Reparar tubería principal edificio A'\n"
            f"  • 'Actualizar inventario de equipos'\n"
            f"  • 'Responder emergencia en sector 3'"
        ),
        4: (
            f"{StatusEmojis.INFO} *Ayuda: Delegado*\n\n"
            f"👤 Selecciona el usuario que *delegará* esta tarea.\n\n"
            f"🔑 *Importante:*\n"
            f"  • El delegado es quien asigna la tarea\n"
            f"  • Tiene permisos de seguimiento\n"
            f"  • Puede modificar la tarea después\n\n"
            f"Selecciona un ID de la lista o escribe el ID del usuario."
        ),
        5: (
            f"{StatusEmojis.INFO} *Ayuda: Asignados*\n\n"
            f"👥 Selecciona los usuarios que *ejecutarán* esta tarea.\n\n"
            f"📌 *Puedes:*\n"
            f"  • Seleccionar múltiples usuarios\n"
            f"  • Dejar sin asignados (opcional)\n"
            f"  • Modificar selección después\n\n"
            f"Envía IDs separados por comas (ej: 101,102,103)"
        ),
        6: (
            f"{StatusEmojis.INFO} *Ayuda: Confirmación*\n\n"
            f"✅ Revisa cuidadosamente los datos antes de confirmar.\n\n"
            f"💡 *Opciones disponibles:*\n"
            f"  • {ActionEmojis.CONFIRM} *Confirmar:* Crear la tarea\n"
            f"  • {ActionEmojis.EDIT} *Editar:* Modificar datos\n"
            f"  • {ActionEmojis.CANCEL} *Cancelar:* Descartar todo\n\n"
            f"Una vez creada, podrás editarla desde el menú principal."
        ),
    }
    
    return help_texts.get(step, f"{StatusEmojis.INFO} Ayuda no disponible para este paso.")


def validate_codigo(codigo: str) -> tuple[bool, str]:
    """
    Valida el código de tarea en tiempo real.
    
    Args:
        codigo: Código ingresado por el usuario
    
    Returns:
        tuple: (es_valido, mensaje_feedback)
    """
    from src.bot.utils.emojis import ValidationEmojis
    
    # Validación: no vacío
    if not codigo or codigo.strip() == "":
        return (False, f"{ValidationEmojis.INVALID} El código no puede estar vacío.")
    
    # Validación: longitud
    if len(codigo) > 20:
        return (False, f"{ValidationEmojis.INVALID} El código es muy largo ({len(codigo)}/20 caracteres).")
    
    if len(codigo) < 3:
        return (False, f"{ValidationEmojis.INVALID} El código es muy corto (mínimo 3 caracteres).")
    
    # Validación: formato sugerido
    if not any(c in codigo for c in ['-', '_', '.']):
        return (True, f"{ValidationEmojis.FORMAT_OK} Formato aceptable. Sugerencia: usa guiones (ej: OPE-2025-001)")
    
    return (True, f"{ValidationEmojis.VALID} Código válido.")


def validate_titulo(titulo: str) -> tuple[bool, str]:
    """
    Valida el título de tarea en tiempo real.
    
    Args:
        titulo: Título ingresado por el usuario
    
    Returns:
        tuple: (es_valido, mensaje_feedback)
    """
    from src.bot.utils.emojis import ValidationEmojis
    
    # Validación: no vacío
    if not titulo or titulo.strip() == "":
        return (False, f"{ValidationEmojis.INVALID} El título no puede estar vacío.")
    
    # Validación: longitud
    if len(titulo) > 100:
        return (False, f"{ValidationEmojis.INVALID} El título es muy largo ({len(titulo)}/100 caracteres).")
    
    if len(titulo) < 10:
        return (False, f"{ValidationEmojis.REQUIRED} El título es muy corto (mínimo 10 caracteres para ser descriptivo).")
    
    # Validación: contiene verbo de acción
    verbos_accion = [
        'reparar', 'actualizar', 'revisar', 'instalar', 'configurar', 
        'gestionar', 'coordinar', 'supervisar', 'verificar', 'completar',
        'realizar', 'ejecutar', 'implementar', 'desarrollar'
    ]
    
    tiene_verbo = any(verbo in titulo.lower() for verbo in verbos_accion)
    
    if not tiene_verbo:
        return (True, f"{ValidationEmojis.FORMAT_OK} Título aceptable. Sugerencia: inicia con un verbo de acción.")
    
    return (True, f"{ValidationEmojis.VALID} Título descriptivo y claro.")


async def handle_wizard_text_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User]
) -> None:
    """
    Procesa inputs de texto cuando hay un wizard activo.
    
    Args:
        update: Update de Telegram con mensaje de texto
        context: Contexto de la conversación con wizard state
    """
    if not update.message or not update.message.text:
        return
    
    # Verificar si hay wizard activo
    wizard = context.user_data.get('wizard')
    if not wizard:
        # No hay wizard activo, dejar que message_handler lo procese
        return
    
    text_input = update.message.text.strip()
    current_step = wizard.get('current_step', 0)
    wizard_data = wizard.get('data', {})
    
    logger.bind(wizard=True).info(
        f"Wizard text input - Step {current_step}: {text_input[:50]}",
        user_id=update.effective_user.id if update.effective_user else None
    )
    
    # Step 2: Código
    if current_step == 2:
        await _handle_codigo_input(update, context, text_input)
    
    # Step 3: Título
    elif current_step == 3:
        await _handle_titulo_input(update, context, text_input)
    
    # Step 4: Delegado ID
    elif current_step == 4:
        await _handle_delegado_input(update, context, text_input)
    
    # Step 5: Asignados (IDs separados por comas)
    elif current_step == 5:
        await _handle_asignados_input(update, context, text_input)
    
    else:
        await update.message.reply_text(
            f"❌ Estado de wizard inválido (step {current_step}). "
            f"Usa /start para comenzar de nuevo."
        )


async def _handle_step_2_codigo(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    codigo: str
) -> None:
    """
    Valida y guarda el código de la tarea con validación en tiempo real.
    
    Args:
        update: Update de Telegram
        context: Contexto con wizard state
        codigo: Código ingresado por el usuario
    """
    # Validación en tiempo real
    es_valido, mensaje = validate_codigo(codigo)
    
    if not es_valido:
        await update.message.reply_text(
            f"{mensaje}\n\n"
            f"Intenta nuevamente con un código válido:"
        )
        return
    
    # Guardar en wizard
    context.user_data['wizard']['data']['codigo'] = codigo
    context.user_data['wizard']['current_step'] = 3
    
    logger.bind(wizard=True).info(
        f"Wizard Step 2 completado: código={codigo}",
        user_id=update.effective_user.id if update.effective_user else None
    )
    
    # Guardar en wizard
    context.user_data['wizard']['data']['codigo'] = codigo
    context.user_data['wizard']['current_step'] = 3
    
    logger.bind(wizard=True).info(
        f"Wizard Step 2 completado: código={codigo}",
        user_id=update.effective_user.id if update.effective_user else None
    )
    
    # Step 3: Solicitar título
    keyboard = KeyboardFactory.back_button("crear:cancel")
    header = get_step_header(3, "Crear Nueva Tarea")
    await update.message.reply_text(
        f"{mensaje}\n\n"  # Mostrar feedback positivo
        f"{header}\n"
        f"Código: `{codigo}`\n\n"
        f"✏️ *Ingresa el título de la tarea:*\n\n"
        f"💡 *Consejos:* Sé específico y claro\n"
        f"📝 *Máximo:* 100 caracteres",  # Corregido: 100 caracteres (consistente con validación)
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def _handle_codigo_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    codigo: str
) -> None:
    """
    Valida y guarda el código de la tarea con validación en tiempo real.
    
    Args:
        update: Update de Telegram
        context: Contexto con wizard state
        codigo: Código ingresado por el usuario
    """
    # Validación en tiempo real
    es_valido, mensaje = validate_codigo(codigo)
    
    if not es_valido:
        await update.message.reply_text(
            f"{mensaje}\n\n"
            f"Intenta nuevamente con un código válido:"
        )
        return
    
    # Guardar en wizard
    context.user_data['wizard']['data']['codigo'] = codigo.upper()
    context.user_data['wizard']['current_step'] = 3
    
    logger.bind(wizard=True).info(
        f"Wizard Step 2 completado: codigo={codigo}",
        user_id=update.effective_user.id if update.effective_user else None
    )
    
    # Step 3: Solicitar título
    await update.message.reply_text(
        f"✅ Código guardado: *{codigo.upper()}*\n\n"
        f"🏷️ *Paso 3/6:* Escribe el título de la tarea\n"
        f"💡 *Guía:* Título descriptivo (5-200 caracteres)\n"
        f"📝 *Ejemplo:* Patrullaje nocturno sector norte",
        parse_mode='Markdown'
    )


async def _handle_titulo_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    titulo: str
) -> None:
    """
    Valida y guarda el título de la tarea con validación en tiempo real.
    
    Args:
        update: Update de Telegram
        context: Contexto con wizard state
        titulo: Título ingresado por el usuario
    """
    # Validación en tiempo real
    es_valido, mensaje = validate_titulo(titulo)
    
    if not es_valido:
        await update.message.reply_text(
            f"{mensaje}\n\n"
            f"Intenta nuevamente con un título descriptivo:"
        )
        return
    
    # Guardar en wizard
    context.user_data['wizard']['data']['titulo'] = titulo
    context.user_data['wizard']['current_step'] = 4
    
    logger.bind(wizard=True).info(
        f"Wizard Step 3 completado: titulo={titulo[:50]}",
        user_id=update.effective_user.id if update.effective_user else None
    )
    
    # Step 4: Solicitar delegado
    # TODO: Llamar a API para obtener lista de delegados
    # Por ahora, solicitar ID manualmente
    keyboard = KeyboardFactory.back_button("crear:cancel")
    await update.message.reply_text(
        f"📝 *Crear Tarea - Paso 4 de 6*\n\n"
        f"Título: {titulo}\n\n"
        f"Por favor, envía el *ID del delegado*\n"
        f"(ejemplo: 123):",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def _handle_delegado_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    delegado_input: str
) -> None:
    """
    Valida y guarda el ID del delegado.
    
    Args:
        update: Update de Telegram
        context: Contexto con wizard state
        delegado_input: ID del delegado ingresado
    """
    # Validación
    try:
        delegado_id = int(delegado_input)
    except ValueError:
        await update.message.reply_text(
            "❌ El ID del delegado debe ser un número. Intenta nuevamente:"
        )
        return
    
    # Guardar en wizard
    context.user_data['wizard']['data']['delegado_id'] = delegado_id
    context.user_data['wizard']['current_step'] = 5
    
    logger.bind(wizard=True).info(
        f"Wizard Step 4 completado: delegado_id={delegado_id}",
        user_id=update.effective_user.id if update.effective_user else None
    )
    
    # Step 5: Solicitar asignados
    keyboard = KeyboardFactory.back_button("crear:cancel")
    await update.message.reply_text(
        f"📝 *Crear Tarea - Paso 5 de 6*\n\n"
        f"Delegado: ID {delegado_id}\n\n"
        f"Por favor, envía los *IDs de agentes asignados*\n"
        f"separados por comas (ej: 101,102,103):",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def _handle_asignados_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    asignados_input: str
) -> None:
    """
    Valida y guarda los IDs de asignados.
    
    Args:
        update: Update de Telegram
        context: Contexto con wizard state
        asignados_input: IDs separados por comas
    """
    # Validación y parsing
    try:
        asignados_ids = [int(x.strip()) for x in asignados_input.split(',')]
    except ValueError:
        await update.message.reply_text(
            "❌ Formato inválido. Usa números separados por comas (ej: 101,102,103).\n"
            "Intenta nuevamente:"
        )
        return
    
    if not asignados_ids:
        await update.message.reply_text(
            "❌ Debes asignar al menos un agente. Intenta nuevamente:"
        )
        return
    
    # Guardar en wizard
    context.user_data['wizard']['data']['asignados'] = asignados_ids
    context.user_data['wizard']['current_step'] = 6
    
    logger.bind(wizard=True).info(
        f"Wizard Step 5 completado: asignados={asignados_ids}",
        user_id=update.effective_user.id if update.effective_user else None
    )
    
    # Step 6: Mostrar resumen
    await _show_wizard_summary(update, context)


async def _show_wizard_summary(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User]
) -> None:
    """
    Muestra resumen del wizard antes de crear la tarea.
    
    Args:
        update: Update de Telegram
        context: Contexto con datos del wizard
    """
    wizard_data = context.user_data.get('wizard', {}).get('data', {})
    
    tipo = wizard_data.get('tipo', 'N/A')
    codigo = wizard_data.get('codigo', 'N/A')
    titulo = wizard_data.get('titulo', 'N/A')
    delegado_id = wizard_data.get('delegado_id', 'N/A')
    asignados = wizard_data.get('asignados', [])
    
    summary_text = (
        f"📋 *Resumen de la Tarea - Paso 6 de 6*\n\n"
        f"*Código:* `{codigo}`\n"
        f"*Título:* {titulo}\n"
        f"*Tipo:* {tipo}\n"
        f"*Delegado:* ID {delegado_id}\n"
        f"*Asignados:* {', '.join(map(str, asignados)) if asignados else 'Ninguno'}\n\n"
        f"¿Confirmar creación?"
    )
    
    keyboard = KeyboardFactory.confirmation("crear:confirm", "crear:cancel")
    
    await update.message.reply_text(
        summary_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Definir handler con filtro
# Solo procesa si hay wizard activo (se verifica dentro de la función)
wizard_text_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND,
    handle_wizard_text_input
)
