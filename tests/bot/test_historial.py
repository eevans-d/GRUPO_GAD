# -*- coding: utf-8 -*-
"""
Tests para el comando /historial
"""

import pytest
from unittest.mock import AsyncMock, Mock
from telegram import Update, User, Message, Chat
from telegram.ext import CallbackContext

from src.bot.commands.historial import historial


@pytest.fixture
def mock_update():
    """Crea un mock de Update para testing."""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=User)
    update.effective_user.id = 12345
    update.message = Mock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture  
def mock_context():
    """Crea un mock de CallbackContext para testing."""
    context = Mock(spec=CallbackContext)
    context.args = []
    return context


@pytest.mark.asyncio
async def test_historial_sin_argumentos(mock_update, mock_context):
    """Test comando /historial sin argumentos (debería mostrar todas)."""
    # Ejecutar comando
    await historial(mock_update, mock_context)
    
    # Verificar que se llamó reply_text al menos una vez
    assert mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_historial_filtro_valido(mock_update, mock_context):
    """Test comando /historial con filtro válido."""
    mock_context.args = ["activas"]
    
    # Ejecutar comando
    await historial(mock_update, mock_context)
    
    # Verificar que se llamó reply_text
    assert mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_historial_filtro_invalido(mock_update, mock_context):
    """Test comando /historial con filtro inválido."""
    mock_context.args = ["invalido"]
    
    # Ejecutar comando
    await historial(mock_update, mock_context)
    
    # Verificar que se llamó reply_text con mensaje de error
    assert mock_update.message.reply_text.called
    call_args = mock_update.message.reply_text.call_args[0][0]
    assert "⚠️" in call_args
    assert "Filtro inválido" in call_args


@pytest.mark.asyncio
async def test_historial_sin_user(mock_context):
    """Test comando /historial sin usuario válido."""
    update = Mock(spec=Update)
    update.effective_user = None
    update.message = None
    
    # Ejecutar comando (no debería hacer nada)
    result = await historial(update, mock_context)
    
    # No debería haber resultado
    assert result is None


def test_historial_handler_exists():
    """Verificar que el handler existe y está configurado."""
    from src.bot.commands.historial import historial_handler
    assert historial_handler is not None
    assert hasattr(historial_handler, 'callback')