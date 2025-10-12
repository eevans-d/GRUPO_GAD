# -*- coding: utf-8 -*-
"""
Tests para el comando /estadisticas
"""

import pytest
from unittest.mock import AsyncMock, Mock
from telegram import Update, User, Message, Chat
from telegram.ext import CallbackContext

from src.bot.commands.estadisticas import estadisticas


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
async def test_estadisticas_comando_basico(mock_update, mock_context):
    """Test comando /estadisticas básico."""
    # Ejecutar comando
    await estadisticas(mock_update, mock_context)
    
    # Verificar que se llamó reply_text al menos una vez
    assert mock_update.message.reply_text.called


@pytest.mark.asyncio
async def test_estadisticas_sin_user(mock_context):
    """Test comando /estadisticas sin usuario válido."""
    update = Mock(spec=Update)
    update.effective_user = None
    update.message = None
    
    # Ejecutar comando (no debería hacer nada)
    result = await estadisticas(update, mock_context)
    
    # No debería haber resultado
    assert result is None


def test_estadisticas_handler_exists():
    """Verificar que el handler existe y está configurado."""
    from src.bot.commands.estadisticas import estadisticas_handler
    assert estadisticas_handler is not None
    assert hasattr(estadisticas_handler, 'callback')


def test_format_tipo_tarea():
    """Test función de formateo de tipo de tarea."""
    from src.bot.commands.estadisticas import _get_tipo_emoji
    
    # Test casos comunes
    assert _get_tipo_emoji("Denuncia") == "🚨"
    assert _get_tipo_emoji("Requerimiento") == "📝"
    assert _get_tipo_emoji("Inspección") == "🔍"
    assert _get_tipo_emoji("Emergencia") == "🚑"
    assert _get_tipo_emoji("Otro") == "📋"
    
    # Test caso no existente (debería devolver default)
    assert _get_tipo_emoji("TipoInexistente") == "📋"


def test_generate_progress_bar():
    """Test función de generación de barra de progreso."""
    from src.bot.commands.estadisticas import _create_progress_bar
    
    # Test casos varios
    bar_0 = _create_progress_bar(0)
    assert "░" in bar_0  # Debería tener solo barras vacías
    
    bar_50 = _create_progress_bar(50)
    assert "▰" in bar_50  # Debería tener barras llenas
    assert "░" in bar_50  # Y también vacías
    
    bar_100 = _create_progress_bar(100)
    assert "▰" in bar_100  # Debería tener solo barras llenas
    
    # Test valores límite
    bar_negative = _create_progress_bar(-10)
    assert isinstance(bar_negative, str)  # No debería crashear
    
    bar_over_100 = _create_progress_bar(150)
    assert isinstance(bar_over_100, str)  # No debería crashear