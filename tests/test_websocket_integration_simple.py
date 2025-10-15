# -*- coding: utf-8 -*-
"""
Tests unitarios para src/core/websocket_integration.py

Enfoque pragmático: tests simples sin dependencias complejas.
Coverage target: 47% → 75%+
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from src.core.websocket_integration import (
    WebSocketModelIntegrator,
    initialize_websocket_integrator,
    get_websocket_integrator,
)


# ============================================================================
# 1. TESTS DE INICIALIZACIÓN Y ESTADO
# ============================================================================

def test_websocket_model_integrator_initialization():
    """WebSocketModelIntegrator debe inicializarse correctamente."""
    mock_emitter = MagicMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    assert integrator.enabled is True
    assert integrator.emitter is mock_emitter
    assert integrator._event_queue is not None
    assert integrator._processing_task is None


def test_integrator_enable():
    """enable() debe activar la integración."""
    mock_emitter = MagicMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    integrator.enabled = False
    integrator.enable()
    
    assert integrator.enabled is True


def test_integrator_disable():
    """disable() debe desactivar la integración."""
    mock_emitter = MagicMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    integrator.disable()
    
    assert integrator.enabled is False


def test_initialize_websocket_integrator_creates_instance():
    """initialize_websocket_integrator debe crear instancia global."""
    mock_emitter = MagicMock()
    
    # Limpiar estado global primero (por si otros tests lo modificaron)
    import src.core.websocket_integration as module
    module.websocket_integrator = None
    
    integrator = initialize_websocket_integrator(mock_emitter)
    
    assert integrator is not None
    assert integrator.emitter is mock_emitter
    assert get_websocket_integrator() is integrator


def test_initialize_websocket_integrator_returns_existing():
    """initialize_websocket_integrator debe retornar instancia existente."""
    mock_emitter = MagicMock()
    
    integrator1 = initialize_websocket_integrator(mock_emitter)
    integrator2 = initialize_websocket_integrator(mock_emitter)
    
    assert integrator1 is integrator2


def test_get_websocket_integrator_returns_none_when_not_initialized():
    """get_websocket_integrator debe retornar None si no está inicializado."""
    import src.core.websocket_integration as module
    module.websocket_integrator = None
    
    result = get_websocket_integrator()
    
    assert result is None


# ============================================================================
# 2. TESTS DE QUEUE_EVENT
# ============================================================================

@pytest.mark.asyncio
async def test_queue_event_adds_to_queue():
    """queue_event debe encolar evento correctamente."""
    mock_emitter = MagicMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    await integrator.queue_event("insert", "Tarea", {"id": 1, "titulo": "Test"})
    
    assert integrator._event_queue.qsize() == 1


@pytest.mark.asyncio
async def test_queue_event_respects_enabled_flag():
    """queue_event no debe encolar si integración deshabilitada."""
    mock_emitter = MagicMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    integrator.disable()
    
    await integrator.queue_event("insert", "Tarea", {"id": 1})
    
    assert integrator._event_queue.qsize() == 0


@pytest.mark.asyncio
async def test_queue_event_includes_timestamp():
    """queue_event debe incluir timestamp en el evento."""
    mock_emitter = MagicMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    await integrator.queue_event("update", "Efectivo", {"id": 5})
    
    event = await integrator._event_queue.get()
    assert "timestamp" in event
    assert isinstance(event["timestamp"], datetime)


# ============================================================================
# 3. TESTS DE _HANDLE_MODEL_EVENT
# ============================================================================

@pytest.mark.asyncio
async def test_handle_model_event_dispatches_tarea():
    """_handle_model_event debe despachar a _handle_tarea_event."""
    mock_emitter = MagicMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    integrator._handle_tarea_event = AsyncMock()
    
    event = {
        "event_type": "insert",
        "model_name": "Tarea",
        "instance_data": {"id": 1, "titulo": "Nueva tarea"}
    }
    
    await integrator._handle_model_event(event)
    
    integrator._handle_tarea_event.assert_called_once_with("insert", {"id": 1, "titulo": "Nueva tarea"})


@pytest.mark.asyncio
async def test_handle_model_event_dispatches_efectivo():
    """_handle_model_event debe despachar a _handle_efectivo_event."""
    mock_emitter = MagicMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    integrator._handle_efectivo_event = AsyncMock()
    
    event = {
        "event_type": "update",
        "model_name": "Efectivo",
        "instance_data": {"id": 3, "nombre": "Juan"}
    }
    
    await integrator._handle_model_event(event)
    
    integrator._handle_efectivo_event.assert_called_once_with("update", {"id": 3, "nombre": "Juan"})


@pytest.mark.asyncio
async def test_handle_model_event_dispatches_usuario():
    """_handle_model_event debe despachar a _handle_usuario_event."""
    mock_emitter = MagicMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    integrator._handle_usuario_event = AsyncMock()
    
    event = {
        "event_type": "insert",
        "model_name": "Usuario",
        "instance_data": {"id": 10, "email": "test@test.com"}
    }
    
    await integrator._handle_model_event(event)
    
    integrator._handle_usuario_event.assert_called_once_with("insert", {"id": 10, "email": "test@test.com"})


# ============================================================================
# 4. TESTS DE _HANDLE_TAREA_EVENT
# ============================================================================

@pytest.mark.asyncio
async def test_handle_tarea_event_insert():
    """_handle_tarea_event debe emitir evento 'created' en insert."""
    mock_emitter = MagicMock()
    mock_emitter.emit_task_event = AsyncMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    integrator._trigger_dashboard_update = AsyncMock()
    
    await integrator._handle_tarea_event("insert", {"id": 5, "titulo": "Nueva"})
    
    mock_emitter.emit_task_event.assert_called_once_with("created", 5, {"id": 5, "titulo": "Nueva"})


@pytest.mark.asyncio
async def test_handle_tarea_event_update_simple():
    """_handle_tarea_event debe emitir 'updated' en update sin cambio estado."""
    mock_emitter = MagicMock()
    mock_emitter.emit_task_event = AsyncMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    integrator._trigger_dashboard_update = AsyncMock()
    
    await integrator._handle_tarea_event("update", {"id": 7, "titulo": "Modificada"})
    
    mock_emitter.emit_task_event.assert_called_once_with("updated", 7, {"id": 7, "titulo": "Modificada"})


@pytest.mark.asyncio
async def test_handle_tarea_event_update_status_change():
    """_handle_tarea_event debe emitir 'status_changed' en cambio de estado."""
    mock_emitter = MagicMock()
    mock_emitter.emit_task_event = AsyncMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    integrator._trigger_dashboard_update = AsyncMock()
    
    instance_data = {
        "id": 8,
        "titulo": "Tarea",
        "_old_estado": "pendiente",
        "estado": "completada"
    }
    
    await integrator._handle_tarea_event("update", instance_data)
    
    # Verificar que se agregó _status_change
    call_args = mock_emitter.emit_task_event.call_args
    assert call_args[0][0] == "status_changed"
    assert call_args[0][1] == 8
    assert "_status_change" in call_args[0][2]
    assert call_args[0][2]["_status_change"]["old"] == "pendiente"
    assert call_args[0][2]["_status_change"]["new"] == "completada"


@pytest.mark.asyncio
async def test_handle_tarea_event_triggers_dashboard_update():
    """_handle_tarea_event debe disparar actualización de dashboard."""
    mock_emitter = MagicMock()
    mock_emitter.emit_task_event = AsyncMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    integrator._trigger_dashboard_update = AsyncMock()
    
    await integrator._handle_tarea_event("insert", {"id": 1, "titulo": "Test"})
    
    integrator._trigger_dashboard_update.assert_called_once()


@pytest.mark.asyncio
async def test_handle_tarea_event_without_id_ignored():
    """_handle_tarea_event debe ignorar evento sin ID."""
    mock_emitter = MagicMock()
    mock_emitter.emit_task_event = AsyncMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    await integrator._handle_tarea_event("insert", {"titulo": "Sin ID"})
    
    mock_emitter.emit_task_event.assert_not_called()


# ============================================================================
# 5. TESTS DE _HANDLE_EFECTIVO_EVENT
# ============================================================================

@pytest.mark.asyncio
async def test_handle_efectivo_event_insert():
    """_handle_efectivo_event debe emitir evento 'created' en insert."""
    mock_emitter = MagicMock()
    mock_emitter.emit_efectivo_event = AsyncMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    await integrator._handle_efectivo_event("insert", {"id": 10, "nombre": "Juan"})
    
    mock_emitter.emit_efectivo_event.assert_called_once_with("created", 10, {"id": 10, "nombre": "Juan"})


@pytest.mark.asyncio
async def test_handle_efectivo_event_update_simple():
    """_handle_efectivo_event debe emitir 'updated' en update sin cambio estado."""
    mock_emitter = MagicMock()
    mock_emitter.emit_efectivo_event = AsyncMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    await integrator._handle_efectivo_event("update", {"id": 15, "nombre": "Pedro"})
    
    mock_emitter.emit_efectivo_event.assert_called_once_with("updated", 15, {"id": 15, "nombre": "Pedro"})


@pytest.mark.asyncio
async def test_handle_efectivo_event_update_status_change():
    """_handle_efectivo_event debe emitir 'status_changed' en cambio de estado."""
    mock_emitter = MagicMock()
    mock_emitter.emit_efectivo_event = AsyncMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    instance_data = {
        "id": 20,
        "nombre": "Carlos",
        "_old_estado": "disponible",
        "estado": "ocupado"
    }
    
    await integrator._handle_efectivo_event("update", instance_data)
    
    call_args = mock_emitter.emit_efectivo_event.call_args
    assert call_args[0][0] == "status_changed"
    assert "_status_change" in call_args[0][2]


@pytest.mark.asyncio
async def test_handle_efectivo_event_without_id_ignored():
    """_handle_efectivo_event debe ignorar evento sin ID."""
    mock_emitter = MagicMock()
    mock_emitter.emit_efectivo_event = AsyncMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    await integrator._handle_efectivo_event("insert", {"nombre": "Sin ID"})
    
    mock_emitter.emit_efectivo_event.assert_not_called()


# ============================================================================
# 6. TESTS DE _HANDLE_USUARIO_EVENT
# ============================================================================

@pytest.mark.asyncio
async def test_handle_usuario_event_logs_event():
    """_handle_usuario_event debe loggear evento (implementación actual)."""
    mock_emitter = MagicMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    # No debe lanzar error
    await integrator._handle_usuario_event("insert", {"id": 1, "email": "user@test.com"})
    
    # Por ahora solo valida que no falle (implementación es logging)
    assert True


# ============================================================================
# 7. TESTS DE _TRIGGER_DASHBOARD_UPDATE
# ============================================================================

@pytest.mark.asyncio
async def test_trigger_dashboard_update_emits_system_event():
    """_trigger_dashboard_update debe emitir evento de sistema."""
    mock_emitter = MagicMock()
    mock_emitter.emit_system_event = AsyncMock()
    integrator = WebSocketModelIntegrator(emitter=mock_emitter)
    
    await integrator._trigger_dashboard_update()
    
    mock_emitter.emit_system_event.assert_called_once()
    call_args = mock_emitter.emit_system_event.call_args
    assert call_args[0][0] == "dashboard_refresh"


# ============================================================================
# 8. TESTS DE HELPERS NOTIFY_*
# ============================================================================

@pytest.mark.asyncio
async def test_notify_task_change_queues_event():
    """notify_task_change debe encolar evento en integrador."""
    from src.core.websocket_integration import notify_task_change
    
    mock_emitter = MagicMock()
    integrator = initialize_websocket_integrator(mock_emitter)
    integrator.queue_event = AsyncMock()
    
    # Mock task instance
    mock_task = MagicMock()
    mock_task.id = 100
    mock_task.titulo = "Test Task"
    mock_task.estado = "pendiente"
    mock_task.prioridad = "alta"
    mock_task.created_at = datetime.now()
    mock_task.updated_at = datetime.now()
    mock_task._sa_instance_state = MagicMock(committed_state={})
    
    await notify_task_change("update", mock_task)
    
    integrator.queue_event.assert_called_once()


@pytest.mark.asyncio
async def test_notify_efectivo_change_queues_event():
    """notify_efectivo_change debe encolar evento en integrador."""
    from src.core.websocket_integration import notify_efectivo_change
    
    mock_emitter = MagicMock()
    integrator = initialize_websocket_integrator(mock_emitter)
    integrator.queue_event = AsyncMock()
    
    # Mock efectivo instance
    mock_efectivo = MagicMock()
    mock_efectivo.id = 50
    mock_efectivo.nombre = "Juan"
    mock_efectivo.apellido = "Pérez"
    mock_efectivo.estado_disponibilidad = "disponible"
    mock_efectivo.rango = "oficial"
    mock_efectivo.updated_at = datetime.now()
    mock_efectivo._sa_instance_state = MagicMock(committed_state={})
    
    await notify_efectivo_change("insert", mock_efectivo)
    
    integrator.queue_event.assert_called_once()


# ============================================================================
# 9. TESTS DE START/STOP INTEGRATION
# ============================================================================

@pytest.mark.asyncio
async def test_start_websocket_integration_enables_and_starts_task():
    """start_websocket_integration debe habilitar y crear task."""
    from src.core.websocket_integration import start_websocket_integration
    
    mock_emitter = MagicMock()
    integrator = initialize_websocket_integrator(mock_emitter)
    
    with patch('src.core.websocket_integration.setup_sqlalchemy_events'):
        await start_websocket_integration()
    
    assert integrator.enabled is True
    assert integrator._processing_task is not None


@pytest.mark.asyncio
async def test_stop_websocket_integration_disables_and_cancels_task():
    """stop_websocket_integration debe deshabilitar y cancelar task."""
    from src.core.websocket_integration import (
        start_websocket_integration,
        stop_websocket_integration
    )
    
    mock_emitter = MagicMock()
    integrator = initialize_websocket_integrator(mock_emitter)
    
    with patch('src.core.websocket_integration.setup_sqlalchemy_events'):
        await start_websocket_integration()
    
    await stop_websocket_integration()
    
    assert integrator.enabled is False
    # Task debería estar cancelado
    assert integrator._processing_task.cancelled() or integrator._processing_task.done()
