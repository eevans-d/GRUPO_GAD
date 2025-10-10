# -*- coding: utf-8 -*-
"""
Tests para callback_handler.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.bot.handlers.callback_handler import (
    handle_callback_query,
    handle_menu_action,
    handle_crear_action
)


@pytest.mark.asyncio
async def test_menu_ayuda_callback():
    """Test del callback de ayuda."""
    update = MagicMock()
    update.callback_query.data = "menu:ayuda:general"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.effective_user.id = 123456
    
    context = MagicMock()
    context.user_data = {}
    
    await handle_callback_query(update, context)
    
    update.callback_query.answer.assert_called_once()
    update.callback_query.edit_message_text.assert_called_once()
    
    # Verificar que el mensaje contiene "Ayuda"
    call_args = update.callback_query.edit_message_text.call_args
    assert "Ayuda" in call_args[0][0]


@pytest.mark.asyncio
async def test_crear_tipo_callback():
    """Test de selección de tipo de tarea."""
    update = MagicMock()
    update.callback_query.data = "crear:tipo:OPERATIVO"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.effective_user.id = 123456
    
    context = MagicMock()
    context.user_data = {}
    
    await handle_callback_query(update, context)
    
    # Verificar que se guardó en contexto
    assert 'wizard' in context.user_data
    assert context.user_data['wizard']['tipo'] == 'OPERATIVO'
    
    update.callback_query.answer.assert_called_once()
    update.callback_query.edit_message_text.assert_called_once()


@pytest.mark.asyncio
async def test_menu_main_callback():
    """Test de volver al menú principal."""
    update = MagicMock()
    update.callback_query.data = "menu:main"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.effective_user.id = 123456
    
    context = MagicMock()
    
    await handle_callback_query(update, context)
    
    update.callback_query.answer.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args
    assert "Menú Principal" in call_args[0][0]


@pytest.mark.asyncio
async def test_invalid_callback_format():
    """Test de callback con formato inválido."""
    update = MagicMock()
    update.callback_query.data = "invalid"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.effective_user.id = 123456
    
    context = MagicMock()
    
    await handle_callback_query(update, context)
    
    update.callback_query.answer.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args
    assert "Error" in call_args[0][0]


@pytest.mark.asyncio
async def test_crear_cancel_callback():
    """Test de cancelación de wizard."""
    update = MagicMock()
    update.callback_query.data = "crear:cancel"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.effective_user.id = 123456
    
    context = MagicMock()
    context.user_data = {'wizard': {'tipo': 'OPERATIVO'}}
    
    await handle_callback_query(update, context)
    
    # Verificar que se limpió el wizard
    assert 'wizard' not in context.user_data
    
    update.callback_query.answer.assert_called_once()
    call_args = update.callback_query.edit_message_text.call_args
    assert "Cancelada" in call_args[0][0]
