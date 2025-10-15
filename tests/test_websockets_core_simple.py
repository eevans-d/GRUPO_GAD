# -*- coding: utf-8 -*-
"""
Tests para aumentar cobertura de src/core/websockets.py
Objetivo: 57% → >85%
"""

import pytest
import asyncio
from datetime import datetime
from src.core.websockets import (
    WebSocketManager,
    WSMessage,
    EventType,
    ConnectionInfo,
)


def test_websocket_manager_initialization():
    """Test WebSocketManager se inicializa correctamente."""
    manager = WebSocketManager()
    
    assert manager is not None
    assert isinstance(manager.active_connections, dict)
    assert len(manager.active_connections) == 0
    assert manager.total_messages_sent == 0
    assert manager.total_broadcasts == 0
    assert manager._heartbeat_task is None


def test_event_type_enum_values():
    """Test EventType enum tiene valores esperados."""
    assert EventType.CONNECTION_ACK == "connection_ack"
    assert EventType.PING == "ping"
    assert EventType.PONG == "pong"
    assert EventType.TASK_CREATED == "task_created"
    assert EventType.TASK_UPDATED == "task_updated"
    assert EventType.NOTIFICATION == "notification"
    assert EventType.ALERT == "alert"


def test_ws_message_model_creation():
    """Test WSMessage se crea correctamente."""
    message = WSMessage(
        event_type=EventType.NOTIFICATION,
        data={"title": "Test", "content": "Message"}
    )
    
    assert message.event_type == EventType.NOTIFICATION
    assert message.data == {"title": "Test", "content": "Message"}
    assert isinstance(message.timestamp, datetime)
    assert message.message_id is not None


def test_ws_message_with_target():
    """Test WSMessage con target_user_id."""
    message = WSMessage(
        event_type=EventType.TASK_ASSIGNED,
        data={"task_id": 123},
        target_user_id=456
    )
    
    assert message.target_user_id == 456
    assert message.data["task_id"] == 123


def test_ws_message_with_role():
    """Test WSMessage con target_role."""
    message = WSMessage(
        event_type=EventType.ALERT,
        data={"message": "Alert"},
        target_role="admin"
    )
    
    assert message.target_role == "admin"


def test_get_stats_empty_manager():
    """get_stats debe retornar dict con campos esperados."""
    manager = WebSocketManager()
    stats = manager.get_stats()
    
    assert "total_connections" in stats
    assert stats["total_connections"] == 0
    assert "connections_by_role" in stats
    assert "unique_users" in stats
    assert stats["unique_users"] == 0
    assert "metrics" in stats
    assert stats["metrics"]["total_messages_sent"] == 0
    assert stats["metrics"]["total_broadcasts"] == 0


def test_heartbeat_interval_default():
    """Test intervalo de heartbeat por defecto."""
    manager = WebSocketManager()
    assert manager._heartbeat_interval == 30


def test_metrics_initialization():
    """Test métricas se inicializan en 0."""
    manager = WebSocketManager()
    
    assert manager.total_messages_sent == 0
    assert manager.total_broadcasts == 0
    assert manager.total_send_errors == 0
    assert manager.last_broadcast_at is None


@pytest.mark.asyncio
async def test_disconnect_nonexistent_connection():
    """Test desconectar conexión inexistente no causa error."""
    manager = WebSocketManager()
    
    # No debería lanzar excepción
    await manager.disconnect("nonexistent-id")
    assert len(manager.active_connections) == 0


@pytest.mark.asyncio
async def test_send_to_connection_nonexistent():
    """Test enviar a conexión inexistente retorna False."""
    manager = WebSocketManager()
    message = WSMessage(
        event_type=EventType.NOTIFICATION,
        data={"test": "data"}
    )
    
    result = await manager.send_to_connection("nonexistent-id", message)
    assert result is False


@pytest.mark.asyncio
async def test_send_to_user_nonexistent():
    """Test enviar a usuario inexistente no causa error."""
    manager = WebSocketManager()
    message = WSMessage(
        event_type=EventType.NOTIFICATION,
        data={"test": "data"}
    )
    
    # No debería lanzar excepción
    await manager.send_to_user(99999, message)


@pytest.mark.asyncio
async def test_send_to_role_nonexistent():
    """Test enviar a rol inexistente no causa error."""
    manager = WebSocketManager()
    message = WSMessage(
        event_type=EventType.NOTIFICATION,
        data={"test": "data"}
    )
    
    # No debería lanzar excepción
    await manager.send_to_role("nonexistent-role", message)


@pytest.mark.asyncio
async def test_broadcast_empty_connections():
    """broadcast sin conexiones debe retornar 0 y NO incrementar contador."""
    manager = WebSocketManager()
    message = WSMessage(event_type=EventType.NOTIFICATION, data={"msg": "test"})
    
    sent = await manager.broadcast(message)
    
    assert sent == 0
    assert manager.total_broadcasts == 0  # NO incrementa sin envíos exitosos


def test_event_type_all_variants():
    """Test que todos los tipos de eventos existen."""
    event_types = [
        "system_status", "user_activity",
        "dashboard_update", "metrics_update",
        "task_created", "task_updated", "task_status_changed", "task_assigned",
        "efectivo_status_changed", "efectivo_location_update",
        "notification", "alert", "warning", "error",
        "connection_ack", "ping", "pong"
    ]
    
    for event_type in event_types:
        # Verificar que existe en el enum
        assert any(e.value == event_type for e in EventType)


def test_manager_user_connections_dict():
    """Test user_connections es un dict vacío inicialmente."""
    manager = WebSocketManager()
    assert isinstance(manager.user_connections, dict)
    assert len(manager.user_connections) == 0


def test_manager_role_connections_dict():
    """Test role_connections es un dict vacío inicialmente."""
    manager = WebSocketManager()
    assert isinstance(manager.role_connections, dict)
    assert len(manager.role_connections) == 0


def test_ws_message_timestamp_is_datetime():
    """Test timestamp es datetime."""
    message = WSMessage(
        event_type=EventType.NOTIFICATION,
        data={}
    )
    assert isinstance(message.timestamp, datetime)


def test_ws_message_message_id_unique():
    """Test message_id es único para cada mensaje."""
    msg1 = WSMessage(event_type=EventType.NOTIFICATION, data={})
    msg2 = WSMessage(event_type=EventType.NOTIFICATION, data={})
    
    assert msg1.message_id != msg2.message_id


def test_ws_message_default_data():
    """Test data tiene default factory."""
    message = WSMessage(event_type=EventType.PING)
    assert message.data == {}


def test_manager_pubsub_initially_none():
    """Test _pubsub es None inicialmente."""
    manager = WebSocketManager()
    assert manager._pubsub is None
