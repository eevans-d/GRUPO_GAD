import pytest

from src.core.websockets import websocket_manager


def test_websocket_manager_basic_stats_structure():
    """Cubre importación del módulo y estructura mínima de get_stats.

    No abre conexiones (modo anclado) pero asegura que el dict base
    mantiene claves esperadas; útil para cobertura estática.
    """
    stats = websocket_manager.get_stats()
    assert isinstance(stats, dict)
    for key in ["total_connections", "connections_by_role", "unique_users", "heartbeat_active", "metrics"]:
        assert key in stats
    metrics = stats["metrics"]
    for m in ["total_messages_sent", "total_broadcasts", "total_send_errors", "last_broadcast_at"]:
        assert m in metrics
    # Valores iniciales esperados
    assert stats["total_connections"] == 0
    assert metrics["total_send_errors"] == 0