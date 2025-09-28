import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_websocket_stats_endpoint(client: AsyncClient):
    response = await client.get('/ws/stats')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    stats = data['stats']
    # Claves básicas según implementación actual
    assert 'total_connections' in stats
    assert 'connections_by_role' in stats
    assert 'unique_users' in stats
    assert 'metrics' in stats
    metrics = stats['metrics']
    for key in ['total_messages_sent', 'total_broadcasts', 'total_send_errors', 'last_broadcast_at']:
        assert key in metrics
    # Valores iniciales esperados (sin actividad aún)
    assert metrics['total_messages_sent'] >= 0
    assert metrics['total_broadcasts'] >= 0
    assert metrics['total_send_errors'] == 0
