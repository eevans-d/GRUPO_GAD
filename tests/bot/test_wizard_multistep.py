# -*- coding: utf-8 -*-
"""
Tests para el wizard multi-step de creación de tareas.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.handlers.wizard_text_handler import (
    handle_wizard_text_input,
    _handle_codigo_input,
    _handle_titulo_input,
    _handle_delegado_input,
    _handle_asignados_input,
)


@pytest.mark.asyncio
async def test_wizard_codigo_input_valid():
    """Test de input válido de código."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.text = "TSK001"
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 12345
    
    context = MagicMock()
    context.user_data = {
        'wizard': {
            'current_step': 2,
            'data': {'tipo': 'OPERATIVO'}
        }
    }
    
    await _handle_codigo_input(update, context, "TSK001")
    
    # Verificar que se guardó el código
    assert context.user_data['wizard']['data']['codigo'] == "TSK001"
    assert context.user_data['wizard']['current_step'] == 3
    
    # Verificar que se pidió el título
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "Paso 3 de 6" in call_args[0][0]
    assert "título" in call_args[0][0].lower()


@pytest.mark.asyncio
async def test_wizard_codigo_input_empty():
    """Test de input vacío de código."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'wizard': {
            'current_step': 2,
            'data': {}
        }
    }
    
    await _handle_codigo_input(update, context, "")
    
    # No debe cambiar el step
    assert context.user_data['wizard']['current_step'] == 2
    
    # Debe mostrar error
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "❌" in call_args[0][0]
    assert "vacío" in call_args[0][0].lower()


@pytest.mark.asyncio
async def test_wizard_codigo_input_too_long():
    """Test de código demasiado largo."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'wizard': {
            'current_step': 2,
            'data': {}
        }
    }
    
    long_codigo = "A" * 25  # Más de 20 caracteres
    
    await _handle_codigo_input(update, context, long_codigo)
    
    # No debe cambiar el step
    assert context.user_data['wizard']['current_step'] == 2
    
    # Debe mostrar error
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "❌" in call_args[0][0]
    assert "largo" in call_args[0][0].lower()


@pytest.mark.asyncio
async def test_wizard_titulo_input_valid():
    """Test de input válido de título."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 12345
    
    context = MagicMock()
    context.user_data = {
        'wizard': {
            'current_step': 3,
            'data': {'codigo': 'TSK001'}
        }
    }
    
    titulo = "Reparar servidor de producción"
    
    await _handle_titulo_input(update, context, titulo)
    
    # Verificar que se guardó el título
    assert context.user_data['wizard']['data']['titulo'] == titulo
    assert context.user_data['wizard']['current_step'] == 4
    
    # Verificar que se pidió el delegado
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "Paso 4 de 6" in call_args[0][0]
    assert "delegado" in call_args[0][0].lower()


@pytest.mark.asyncio
async def test_wizard_titulo_input_empty():
    """Test de título vacío."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'wizard': {
            'current_step': 3,
            'data': {}
        }
    }
    
    await _handle_titulo_input(update, context, "")
    
    # No debe cambiar el step
    assert context.user_data['wizard']['current_step'] == 3
    
    # Debe mostrar error
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "❌" in call_args[0][0]


@pytest.mark.asyncio
async def test_wizard_delegado_input_valid():
    """Test de input válido de delegado ID."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 12345
    
    context = MagicMock()
    context.user_data = {
        'wizard': {
            'current_step': 4,
            'data': {'codigo': 'TSK001', 'titulo': 'Test'}
        }
    }
    
    await _handle_delegado_input(update, context, "123")
    
    # Verificar que se guardó el delegado
    assert context.user_data['wizard']['data']['delegado_id'] == 123
    assert context.user_data['wizard']['current_step'] == 5
    
    # Verificar que se pidieron los asignados
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "Paso 5 de 6" in call_args[0][0]
    assert "asignados" in call_args[0][0].lower()


@pytest.mark.asyncio
async def test_wizard_delegado_input_invalid():
    """Test de delegado ID inválido (no numérico)."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'wizard': {
            'current_step': 4,
            'data': {}
        }
    }
    
    await _handle_delegado_input(update, context, "abc")
    
    # No debe cambiar el step
    assert context.user_data['wizard']['current_step'] == 4
    
    # Debe mostrar error
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "❌" in call_args[0][0]
    assert "número" in call_args[0][0].lower()


@pytest.mark.asyncio
async def test_wizard_asignados_input_valid():
    """Test de input válido de asignados."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 12345
    
    context = MagicMock()
    context.user_data = {
        'wizard': {
            'current_step': 5,
            'data': {
                'codigo': 'TSK001',
                'titulo': 'Test',
                'tipo': 'OPERATIVO',
                'delegado_id': 123
            }
        }
    }
    
    await _handle_asignados_input(update, context, "101,102,103")
    
    # Verificar que se guardaron los asignados
    assert context.user_data['wizard']['data']['asignados'] == [101, 102, 103]
    assert context.user_data['wizard']['current_step'] == 6
    
    # Verificar que se mostró el resumen
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "Resumen" in call_args[0][0]
    assert "Paso 6 de 6" in call_args[0][0]


@pytest.mark.asyncio
async def test_wizard_asignados_input_invalid():
    """Test de asignados con formato inválido."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'wizard': {
            'current_step': 5,
            'data': {}
        }
    }
    
    await _handle_asignados_input(update, context, "abc,xyz")
    
    # No debe cambiar el step
    assert context.user_data['wizard']['current_step'] == 5
    
    # Debe mostrar error
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "❌" in call_args[0][0]
    assert "formato" in call_args[0][0].lower()


@pytest.mark.asyncio
async def test_wizard_complete_flow():
    """Test del flujo completo del wizard."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.effective_user.id = 12345
    
    context = MagicMock()
    
    # Step 1: Tipo (se hace desde callback, aquí iniciamos desde step 2)
    context.user_data = {
        'wizard': {
            'current_step': 2,
            'data': {'tipo': 'OPERATIVO'}
        }
    }
    
    # Step 2: Código
    await _handle_codigo_input(update, context, "TSK001")
    assert context.user_data['wizard']['data']['codigo'] == "TSK001"
    assert context.user_data['wizard']['current_step'] == 3
    
    # Step 3: Título
    await _handle_titulo_input(update, context, "Tarea de prueba")
    assert context.user_data['wizard']['data']['titulo'] == "Tarea de prueba"
    assert context.user_data['wizard']['current_step'] == 4
    
    # Step 4: Delegado
    await _handle_delegado_input(update, context, "123")
    assert context.user_data['wizard']['data']['delegado_id'] == 123
    assert context.user_data['wizard']['current_step'] == 5
    
    # Step 5: Asignados
    await _handle_asignados_input(update, context, "101,102")
    assert context.user_data['wizard']['data']['asignados'] == [101, 102]
    assert context.user_data['wizard']['current_step'] == 6
    
    # Verificar datos completos
    wizard_data = context.user_data['wizard']['data']
    assert wizard_data['tipo'] == 'OPERATIVO'
    assert wizard_data['codigo'] == 'TSK001'
    assert wizard_data['titulo'] == 'Tarea de prueba'
    assert wizard_data['delegado_id'] == 123
    assert wizard_data['asignados'] == [101, 102]


@pytest.mark.asyncio
async def test_wizard_text_handler_no_wizard_active():
    """Test cuando no hay wizard activo."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.text = "Texto cualquiera"
    
    context = MagicMock()
    context.user_data = {}  # No hay wizard
    
    # No debe hacer nada (retorna sin procesar)
    await handle_wizard_text_input(update, context)
    
    # Verificar que no se llamó a reply_text
    update.message.reply_text.assert_not_called()


@pytest.mark.asyncio
async def test_wizard_asignados_input_empty():
    """Test de lista vacía de asignados."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'wizard': {
            'current_step': 5,
            'data': {}
        }
    }
    
    await _handle_asignados_input(update, context, "")
    
    # No debe cambiar el step
    assert context.user_data['wizard']['current_step'] == 5
    
    # Debe mostrar error
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args
    assert "❌" in call_args[0][0]
