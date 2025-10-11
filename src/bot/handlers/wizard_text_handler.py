# -*- coding: utf-8 -*-
"""
Handler para capturar inputs de texto del wizard de creación.
"""

from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from telegram import Bot, Chat, User
from loguru import logger

from src.bot.utils.keyboards import KeyboardFactory


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
    wizard = context.user_data.get('wizard')  # type: ignore
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


async def _handle_codigo_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    codigo: str
) -> None:
    """
    Valida y guarda el código de la tarea.
    
    Args:
        update: Update de Telegram
        context: Contexto con wizard state
        codigo: Código ingresado por el usuario
    """
    # Validación
    if not codigo:
        await update.message.reply_text("❌ El código no puede estar vacío. Intenta nuevamente:")
        return
    
    if len(codigo) > 20:
        await update.message.reply_text(
            f"❌ El código es demasiado largo ({len(codigo)} caracteres). "
            f"Máximo 20 caracteres. Intenta nuevamente:"
        )
        return
    
    # Guardar en wizard
    context.user_data['wizard']['data']['codigo'] = codigo  # type: ignore
    context.user_data['wizard']['current_step'] = 3  # type: ignore
    
    logger.bind(wizard=True).info(
        f"Wizard Step 2 completado: código={codigo}",
        user_id=update.effective_user.id if update.effective_user else None
    )
    
    # Step 3: Solicitar título
    keyboard = KeyboardFactory.back_button("crear:cancel")
    await update.message.reply_text(
        f"📝 *Crear Tarea - Paso 3 de 6*\n\n"
        f"Código: `{codigo}`\n\n"
        f"Por favor, envía el *título* de la tarea\n"
        f"(máximo 200 caracteres):",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def _handle_titulo_input(
    update: Update,
    context: CallbackContext[Bot, Update, Chat, User],
    titulo: str
) -> None:
    """
    Valida y guarda el título de la tarea.
    
    Args:
        update: Update de Telegram
        context: Contexto con wizard state
        titulo: Título ingresado por el usuario
    """
    # Validación
    if not titulo:
        await update.message.reply_text("❌ El título no puede estar vacío. Intenta nuevamente:")
        return
    
    if len(titulo) > 200:
        await update.message.reply_text(
            f"❌ El título es demasiado largo ({len(titulo)} caracteres). "
            f"Máximo 200 caracteres. Intenta nuevamente:"
        )
        return
    
    # Guardar en wizard
    context.user_data['wizard']['data']['titulo'] = titulo  # type: ignore
    context.user_data['wizard']['current_step'] = 4  # type: ignore
    
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
    context.user_data['wizard']['data']['delegado_id'] = delegado_id  # type: ignore
    context.user_data['wizard']['current_step'] = 5  # type: ignore
    
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
    context.user_data['wizard']['data']['asignados'] = asignados_ids  # type: ignore
    context.user_data['wizard']['current_step'] = 6  # type: ignore
    
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
    wizard_data = context.user_data.get('wizard', {}).get('data', {})  # type: ignore
    
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
