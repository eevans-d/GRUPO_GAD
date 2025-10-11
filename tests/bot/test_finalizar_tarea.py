# -*- coding: utf-8 -*-
"""
Tests para la funcionalidad de finalización de tareas.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.handlers.callback_handler import (
    handle_finalizar_action,
    _show_pending_tasks_list,
    _show_finalize_confirmation,
    _finalize_task,
)
from src.schemas.tarea import Tarea
from src.shared.constants import TaskStatus, TaskType, TaskPriority


def create_mock_tarea(
    codigo: str = "TSK001",
    titulo: str = "Tarea de prueba",
    tipo: str = "OPERATIVO",
    estado: str = "pending"
) -> Tarea:
    """Helper para crear tareas mock con todos los campos obligatorios."""
    return Tarea(
        id=1,
        uuid=uuid4(),
        codigo=codigo,
        titulo=titulo,
        tipo=TaskType(tipo),
        estado=TaskStatus(estado),
        prioridad=TaskPriority.MEDIUM,
        delegado_usuario_id=100,
        creado_por_usuario_id=200,
        inicio_programado=datetime.now()
    )


@pytest.mark.asyncio
async def test_show_pending_tasks_empty_list():
    """Test cuando el usuario no tiene tareas pendientes."""
    query = MagicMock()
    query.from_user.id = 12345
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {}
    
    # Mock ApiService para retornar lista vacía
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        mock_api.get_user_pending_tasks.return_value = []
        
        await _show_pending_tasks_list(query, context, page=0)
    
    # Verificar que se mostró mensaje de lista vacía
    query.edit_message_text.assert_called_once()
    call_args = query.edit_message_text.call_args
    assert "No tienes tareas pendientes" in call_args[0][0]
    assert "📭" in call_args[0][0]


@pytest.mark.asyncio
async def test_show_pending_tasks_with_items():
    """Test cuando el usuario tiene tareas pendientes."""
    query = MagicMock()
    query.from_user.id = 12345
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {}
    
    # Crear tareas de ejemplo
    tareas = [
        create_mock_tarea(codigo="TSK001", titulo="Tarea 1", tipo="OPERATIVO"),
        create_mock_tarea(codigo="TSK002", titulo="Tarea 2", tipo="ESTRATEGICO"),
        create_mock_tarea(codigo="TSK003", titulo="Tarea 3", tipo="SEGUIMIENTO"),
    ]
    
    # Mock ApiService
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        mock_api.get_user_pending_tasks.return_value = tareas
        
        await _show_pending_tasks_list(query, context, page=0)
    
    # Verificar que se guardó el contexto
    assert context.user_data['finalizar_context'] is True
    
    # Verificar que se mostró la lista
    query.edit_message_text.assert_called_once()
    call_args = query.edit_message_text.call_args
    assert "3 tareas pendientes" in call_args[0][0]
    assert "Finalizar Tarea" in call_args[0][0]


@pytest.mark.asyncio
async def test_show_pending_tasks_pagination():
    """Test de paginación con más de 5 tareas."""
    query = MagicMock()
    query.from_user.id = 12345
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {}
    
    # Crear 8 tareas para probar paginación
    tareas = [
        create_mock_tarea(codigo=f"TSK{i:03d}", titulo=f"Tarea {i}")
        for i in range(1, 9)
    ]
    
    # Mock ApiService
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        mock_api.get_user_pending_tasks.return_value = tareas
        
        await _show_pending_tasks_list(query, context, page=0)
    
    # Verificar que muestra página 1 de 2
    query.edit_message_text.assert_called_once()
    call_args = query.edit_message_text.call_args
    assert "8 tareas pendientes" in call_args[0][0]
    assert "1-5 de 8" in call_args[0][0]
    
    # Verificar que el keyboard tiene paginación
    keyboard_arg = call_args[1]['reply_markup']
    assert keyboard_arg is not None


@pytest.mark.asyncio
async def test_handle_finalizar_select():
    """Test de selección de tarea desde la lista."""
    query = MagicMock()
    query.from_user.id = 12345
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {}
    
    # Crear tarea de ejemplo
    tarea = create_mock_tarea(codigo="TSK001", titulo="Tarea de prueba")
    
    # Mock ApiService
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        mock_api.get_user_pending_tasks.return_value = [tarea]
        
        await handle_finalizar_action(query, context, "select", ["TSK001"])
    
    # Verificar que se guardó la tarea en contexto
    assert 'finalizar_task' in context.user_data
    assert context.user_data['finalizar_task']['codigo'] == "TSK001"
    assert context.user_data['finalizar_task']['titulo'] == "Tarea de prueba"
    
    # Verificar que se mostró la confirmación
    query.edit_message_text.assert_called_once()
    call_args = query.edit_message_text.call_args
    assert "Confirmar Finalización" in call_args[0][0]
    assert "TSK001" in call_args[0][0]


@pytest.mark.asyncio
async def test_handle_finalizar_select_not_found():
    """Test cuando se intenta seleccionar una tarea que no existe."""
    query = MagicMock()
    query.from_user.id = 12345
    query.answer = AsyncMock()
    
    context = MagicMock()
    context.user_data = {}
    
    # Mock ApiService con lista vacía
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        mock_api.get_user_pending_tasks.return_value = []
        
        await handle_finalizar_action(query, context, "select", ["TSK999"])
    
    # Verificar que mostró error
    query.answer.assert_called_once()
    call_args = query.answer.call_args
    assert "Tarea no encontrada" in call_args[0][0]
    assert call_args[1]['show_alert'] is True


@pytest.mark.asyncio
async def test_show_finalize_confirmation():
    """Test de pantalla de confirmación."""
    query = MagicMock()
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'finalizar_task': {
            'codigo': 'TSK001',
            'titulo': 'Tarea de prueba',
            'tipo': 'OPERATIVO'
        }
    }
    
    await _show_finalize_confirmation(query, context)
    
    # Verificar que se mostró la confirmación
    query.edit_message_text.assert_called_once()
    call_args = query.edit_message_text.call_args
    assert "Confirmar Finalización" in call_args[0][0]
    assert "TSK001" in call_args[0][0]
    assert "Tarea de prueba" in call_args[0][0]
    assert "OPERATIVO" in call_args[0][0]
    
    # Verificar que tiene botones de confirmación
    keyboard_arg = call_args[1]['reply_markup']
    assert keyboard_arg is not None


@pytest.mark.asyncio
async def test_finalize_task_success():
    """Test de finalización exitosa de tarea."""
    query = MagicMock()
    query.from_user.id = 12345
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'finalizar_task': {
            'codigo': 'TSK001',
            'titulo': 'Tarea de prueba',
            'tipo': 'OPERATIVO'
        },
        'finalizar_context': True
    }
    
    # Mock de tarea finalizada
    tarea_finalizada = create_mock_tarea(
        codigo="TSK001",
        titulo="Tarea de prueba",
        estado="completed"
    )
    
    # Mock ApiService
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        mock_api.finalize_task.return_value = tarea_finalizada
        
        await _finalize_task(query, context)
    
    # Verificar que se llamó a la API
    mock_api.finalize_task.assert_called_once_with("TSK001", 12345)
    
    # Verificar que se limpió el contexto
    assert 'finalizar_task' not in context.user_data
    assert 'finalizar_context' not in context.user_data
    
    # Verificar mensaje de éxito
    query.edit_message_text.assert_called_once()
    call_args = query.edit_message_text.call_args
    assert "¡Tarea Finalizada!" in call_args[0][0]
    assert "TSK001" in call_args[0][0]


@pytest.mark.asyncio
async def test_finalize_task_not_found():
    """Test cuando la tarea no existe o ya fue finalizada."""
    query = MagicMock()
    query.from_user.id = 12345
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'finalizar_task': {
            'codigo': 'TSK001',
            'titulo': 'Tarea de prueba',
            'tipo': 'OPERATIVO'
        }
    }
    
    # Mock ApiService para simular error 404
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        mock_api.finalize_task.side_effect = Exception("404 not found")
        
        await _finalize_task(query, context)
    
    # Verificar mensaje de error
    query.edit_message_text.assert_called_once()
    call_args = query.edit_message_text.call_args
    assert "Error al Finalizar" in call_args[0][0]
    assert "no fue encontrada" in call_args[0][0]


@pytest.mark.asyncio
async def test_finalize_task_forbidden():
    """Test cuando el usuario no tiene permisos."""
    query = MagicMock()
    query.from_user.id = 12345
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'finalizar_task': {
            'codigo': 'TSK001',
            'titulo': 'Tarea de prueba',
            'tipo': 'OPERATIVO'
        }
    }
    
    # Mock ApiService para simular error 403
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        mock_api.finalize_task.side_effect = Exception("403 forbidden")
        
        await _finalize_task(query, context)
    
    # Verificar mensaje de error
    query.edit_message_text.assert_called_once()
    call_args = query.edit_message_text.call_args
    assert "Error al Finalizar" in call_args[0][0]
    assert "No tienes permisos" in call_args[0][0]


@pytest.mark.asyncio
async def test_finalize_task_generic_error():
    """Test de error genérico al finalizar."""
    query = MagicMock()
    query.from_user.id = 12345
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'finalizar_task': {
            'codigo': 'TSK001',
            'titulo': 'Tarea de prueba',
            'tipo': 'OPERATIVO'
        }
    }
    
    # Mock ApiService para simular error genérico
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        mock_api.finalize_task.side_effect = Exception("Connection timeout")
        
        await _finalize_task(query, context)
    
    # Verificar mensaje de error genérico
    query.edit_message_text.assert_called_once()
    call_args = query.edit_message_text.call_args
    assert "Error al Finalizar" in call_args[0][0]
    assert "Intenta nuevamente" in call_args[0][0]


@pytest.mark.asyncio
async def test_handle_finalizar_cancel():
    """Test de cancelación del flujo de finalización."""
    query = MagicMock()
    query.from_user.id = 12345
    query.edit_message_text = AsyncMock()
    
    context = MagicMock()
    context.user_data = {
        'finalizar_task': {
            'codigo': 'TSK001',
            'titulo': 'Tarea de prueba',
            'tipo': 'OPERATIVO'
        },
        'finalizar_context': True
    }
    
    # Mock ApiService
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        mock_api.get_user_pending_tasks.return_value = []
        
        await handle_finalizar_action(query, context, "cancel", [])
    
    # Verificar que se limpió el contexto
    assert 'finalizar_task' not in context.user_data
    
    # Verificar que volvió a la lista
    query.edit_message_text.assert_called_once()


@pytest.mark.asyncio
async def test_complete_finalize_flow():
    """Test de flujo completo: lista → select → confirm → finalize."""
    query = MagicMock()
    query.from_user.id = 12345
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    
    context = MagicMock()
    context.user_data = {}
    
    # Crear tarea de ejemplo
    tarea = create_mock_tarea(codigo="TSK001", titulo="Tarea completa")
    tarea_finalizada = create_mock_tarea(codigo="TSK001", titulo="Tarea completa", estado="completed")
    
    # Mock ApiService
    with patch('src.bot.handlers.callback_handler.ApiService') as MockApiService:
        mock_api = MockApiService.return_value
        
        # Step 1: Mostrar lista
        mock_api.get_user_pending_tasks.return_value = [tarea]
        await handle_finalizar_action(query, context, "list", [])
        
        assert 'finalizar_context' in context.user_data
        
        # Step 2: Seleccionar tarea
        mock_api.get_user_pending_tasks.return_value = [tarea]
        await handle_finalizar_action(query, context, "select", ["TSK001"])
        
        assert context.user_data['finalizar_task']['codigo'] == "TSK001"
        
        # Step 3: Confirmar
        mock_api.finalize_task.return_value = tarea_finalizada
        await handle_finalizar_action(query, context, "confirm", [])
        
        # Verificar que se finalizó correctamente
        mock_api.finalize_task.assert_called_once_with("TSK001", 12345)
        assert 'finalizar_task' not in context.user_data
        assert 'finalizar_context' not in context.user_data
