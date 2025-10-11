# -*- coding: utf-8 -*-
"""
Tests para el comando start con botones.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.bot.commands.start import start


@pytest.mark.asyncio
async def test_start_command_with_buttons():
    """Test del comando /start con menú de botones."""
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    
    await start(update, context)
    
    # Verificar que se llamó reply_text
    update.message.reply_text.assert_called_once()
    
    # Verificar que tiene reply_markup
    call_kwargs = update.message.reply_text.call_args[1]
    assert 'reply_markup' in call_kwargs
    assert call_kwargs['reply_markup'] is not None
    
    # Verificar que el mensaje contiene "Bienvenido"
    call_args = update.message.reply_text.call_args[0]
    assert "Bienvenido" in call_args[0]


@pytest.mark.asyncio
async def test_start_command_with_none_message():
    """Test del comando /start con mensaje None."""
    update = MagicMock()
    update.message = None
    
    context = MagicMock()
    
    # No debe lanzar excepción
    await start(update, context)
