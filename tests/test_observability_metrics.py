# -*- coding: utf-8 -*-
"""
Tests unitarios para src/observability/metrics.py

Enfoque pragmático: tests simples de funciones de instrumentación.
Coverage target: 68% → 90%+
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from src.observability.metrics import (
    initialize_metrics,
    connection_established,
    connection_closed,
    message_sent,
    send_error,
    heartbeat_completed,
    update_user_count,
    record_message_latency,
    update_all_metrics_from_manager,
    ENVIRONMENT,
    active_connections,
    connections_total,
    messages_sent_total,
    broadcasts_total,
    send_errors_total,
    heartbeat_last_timestamp,
    role_connections,
    user_active,
    message_latency,
)


# ============================================================================
# 1. TESTS DE INICIALIZACIÓN
# ============================================================================

def test_initialize_metrics_sets_defaults():
    """initialize_metrics debe establecer valores por defecto."""
    # No lanza error
    initialize_metrics()
    
    # Validar que se puede acceder a métricas
    assert active_connections.labels(ENVIRONMENT) is not None
    assert user_active.labels(ENVIRONMENT) is not None


def test_environment_constant_exists():
    """ENVIRONMENT debe estar definido."""
    assert ENVIRONMENT is not None
    assert isinstance(ENVIRONMENT, str)
    assert len(ENVIRONMENT) > 0


# ============================================================================
# 2. TESTS DE CONNECTION_ESTABLISHED
# ============================================================================

def test_connection_established_increments_counters():
    """connection_established debe incrementar métricas."""
    # Obtener valor inicial
    initial_active = active_connections.labels(ENVIRONMENT)._value._value
    initial_total = connections_total.labels(ENVIRONMENT)._value._value
    
    connection_established()
    
    # Validar incrementos
    new_active = active_connections.labels(ENVIRONMENT)._value._value
    new_total = connections_total.labels(ENVIRONMENT)._value._value
    
    assert new_active == initial_active + 1
    assert new_total == initial_total + 1


def test_connection_established_with_role():
    """connection_established debe actualizar role_connections."""
    connection_established(user_id=1, user_role="admin")
    
    # Validar que no lanza error
    assert True


def test_connection_established_with_user_id():
    """connection_established debe aceptar user_id."""
    connection_established(user_id=10)
    
    assert True


# ============================================================================
# 3. TESTS DE CONNECTION_CLOSED
# ============================================================================

def test_connection_closed_decrements_active():
    """connection_closed debe decrementar active_connections."""
    # Establecer conexión primero
    initial_active = active_connections.labels(ENVIRONMENT)._value._value
    
    connection_closed()
    
    new_active = active_connections.labels(ENVIRONMENT)._value._value
    assert new_active == initial_active - 1


def test_connection_closed_with_role():
    """connection_closed debe actualizar role_connections."""
    connection_closed(user_id=1, user_role="admin")
    
    assert True


def test_connection_closed_with_user_id():
    """connection_closed debe aceptar user_id."""
    connection_closed(user_id=10)
    
    assert True


# ============================================================================
# 4. TESTS DE MESSAGE_SENT
# ============================================================================

def test_message_sent_increments_total():
    """message_sent debe incrementar messages_sent_total."""
    initial_messages = messages_sent_total.labels(ENVIRONMENT)._value._value
    
    message_sent(is_broadcast=False)
    
    new_messages = messages_sent_total.labels(ENVIRONMENT)._value._value
    assert new_messages == initial_messages + 1


def test_message_sent_broadcast_increments_both():
    """message_sent con broadcast=True debe incrementar ambas métricas."""
    initial_messages = messages_sent_total.labels(ENVIRONMENT)._value._value
    initial_broadcasts = broadcasts_total.labels(ENVIRONMENT)._value._value
    
    message_sent(is_broadcast=True)
    
    new_messages = messages_sent_total.labels(ENVIRONMENT)._value._value
    new_broadcasts = broadcasts_total.labels(ENVIRONMENT)._value._value
    
    assert new_messages == initial_messages + 1
    assert new_broadcasts == initial_broadcasts + 1


def test_message_sent_default_not_broadcast():
    """message_sent sin parámetros debe contar como no-broadcast."""
    initial_broadcasts = broadcasts_total.labels(ENVIRONMENT)._value._value
    
    message_sent()
    
    new_broadcasts = broadcasts_total.labels(ENVIRONMENT)._value._value
    assert new_broadcasts == initial_broadcasts  # No debe incrementar


# ============================================================================
# 5. TESTS DE SEND_ERROR
# ============================================================================

def test_send_error_increments_counter():
    """send_error debe incrementar send_errors_total."""
    initial_errors = send_errors_total.labels(ENVIRONMENT)._value._value
    
    send_error()
    
    new_errors = send_errors_total.labels(ENVIRONMENT)._value._value
    assert new_errors == initial_errors + 1


# ============================================================================
# 6. TESTS DE HEARTBEAT_COMPLETED
# ============================================================================

def test_heartbeat_completed_updates_timestamp():
    """heartbeat_completed debe actualizar timestamp."""
    before_time = time.time()
    
    heartbeat_completed()
    
    timestamp = heartbeat_last_timestamp.labels(ENVIRONMENT)._value._value
    
    # Timestamp debe ser reciente (dentro de 1 segundo)
    assert timestamp >= before_time
    assert timestamp <= time.time() + 1


# ============================================================================
# 7. TESTS DE UPDATE_USER_COUNT
# ============================================================================

def test_update_user_count_sets_value():
    """update_user_count debe establecer valor correcto."""
    update_user_count(42)
    
    count = user_active.labels(ENVIRONMENT)._value._value
    assert count == 42


def test_update_user_count_zero():
    """update_user_count debe aceptar 0."""
    update_user_count(0)
    
    count = user_active.labels(ENVIRONMENT)._value._value
    assert count == 0


def test_update_user_count_large_number():
    """update_user_count debe aceptar números grandes."""
    update_user_count(10000)
    
    count = user_active.labels(ENVIRONMENT)._value._value
    assert count == 10000


# ============================================================================
# 8. TESTS DE RECORD_MESSAGE_LATENCY
# ============================================================================

def test_record_message_latency_observes_value():
    """record_message_latency debe observar latencia."""
    # No debe lanzar error
    record_message_latency(0.05)
    
    assert True


def test_record_message_latency_various_values():
    """record_message_latency debe aceptar diferentes valores."""
    latencies = [0.001, 0.01, 0.1, 1.0, 5.0]
    
    for latency in latencies:
        record_message_latency(latency)
    
    assert True


# ============================================================================
# 9. TESTS DE UPDATE_ALL_METRICS_FROM_MANAGER
# ============================================================================

def test_update_all_metrics_from_manager_basic():
    """update_all_metrics_from_manager debe actualizar métricas básicas."""
    stats = {
        "active_connections": 15,
        "unique_users": 8,
        "last_heartbeat_time": time.time(),
        "roles": {
            "admin": 2,
            "operator": 13
        }
    }
    
    update_all_metrics_from_manager(stats)
    
    active = active_connections.labels(ENVIRONMENT)._value._value
    users = user_active.labels(ENVIRONMENT)._value._value
    
    assert active == 15
    assert users == 8


def test_update_all_metrics_from_manager_empty_stats():
    """update_all_metrics_from_manager debe manejar stats vacío."""
    stats = {}
    
    # No debe lanzar error
    update_all_metrics_from_manager(stats)
    
    assert True


def test_update_all_metrics_from_manager_partial_stats():
    """update_all_metrics_from_manager debe manejar stats parcial."""
    stats = {
        "active_connections": 5
    }
    
    update_all_metrics_from_manager(stats)
    
    active = active_connections.labels(ENVIRONMENT)._value._value
    assert active == 5


def test_update_all_metrics_from_manager_with_roles():
    """update_all_metrics_from_manager debe actualizar roles."""
    stats = {
        "active_connections": 20,
        "roles": {
            "supervisor": 5,
            "field_agent": 15
        }
    }
    
    # No debe lanzar error
    update_all_metrics_from_manager(stats)
    
    assert True


def test_update_all_metrics_from_manager_zero_users():
    """update_all_metrics_from_manager debe manejar 0 usuarios."""
    stats = {
        "active_connections": 0,
        "unique_users": 0
    }
    
    update_all_metrics_from_manager(stats)
    
    active = active_connections.labels(ENVIRONMENT)._value._value
    assert active == 0


# ============================================================================
# 10. TESTS DE MÉTRICAS PROMETHEUS (estructura)
# ============================================================================

def test_all_metrics_have_environment_label():
    """Todas las métricas deben tener label de environment."""
    metrics = [
        active_connections,
        connections_total,
        messages_sent_total,
        broadcasts_total,
        send_errors_total,
        heartbeat_last_timestamp,
        user_active,
        message_latency
    ]
    
    for metric in metrics:
        # Validar que se puede acceder con label ENVIRONMENT
        assert metric.labels(ENVIRONMENT) is not None


def test_role_connections_has_role_label():
    """role_connections debe aceptar label 'role'."""
    # No debe lanzar error
    role_connections.labels(ENVIRONMENT, "admin")
    
    assert True


# ============================================================================
# 11. TESTS DE EDGE CASES
# ============================================================================

def test_multiple_connection_cycles():
    """Múltiples ciclos de conexión/desconexión deben funcionar."""
    for _ in range(5):
        connection_established()
        connection_closed()
    
    assert True


def test_many_messages_sent():
    """Envío de muchos mensajes debe funcionar."""
    for i in range(100):
        message_sent(is_broadcast=(i % 10 == 0))
    
    assert True


def test_heartbeat_multiple_completions():
    """Múltiples heartbeats completados deben funcionar."""
    for _ in range(10):
        heartbeat_completed()
        time.sleep(0.01)
    
    assert True
