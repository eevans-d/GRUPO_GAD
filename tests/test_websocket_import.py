"""Test mínimo para forzar la importación temprana del módulo websockets.

No modifica comportamiento ni abre conexiones. Ayuda a evitar CoverageWarning
cuando se ejecutan subconjuntos mínimos de tests con --cov dirigido.
"""

from src.core.websockets import websocket_manager


def test_websocket_module_import_structure():
    # Aislar métricas por si otras pruebas corrieron antes en el mismo proceso
    websocket_manager.total_messages_sent = 0
    websocket_manager.total_broadcasts = 0
    websocket_manager.total_send_errors = 0
    websocket_manager.last_broadcast_at = None

    stats = websocket_manager.get_stats()
    # Estructura base
    assert set(stats.keys()) == {
        "total_connections",
        "connections_by_role",
        "unique_users",
        "heartbeat_active",
        "heartbeat_interval",
        "metrics",
    }
    assert stats["total_connections"] == 0
    assert stats["metrics"]["total_messages_sent"] == 0
    assert stats["metrics"]["total_broadcasts"] == 0
    assert stats["metrics"]["total_send_errors"] == 0
    assert stats["metrics"]["last_broadcast_at"] is None
