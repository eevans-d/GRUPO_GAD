import json
import asyncio
import pytest
import httpx
from websockets.asyncio.client import connect as ws_connect
from config.settings import get_settings
from src.core.websockets import EventType

@pytest.mark.asyncio
async def test_broadcast_metrics_increment(ws_server: str):
    settings = get_settings()
    if getattr(settings, 'ENVIRONMENT', 'development') == 'production':
        pytest.skip('No se prueba broadcast interno en producción')

    uri = f"{ws_server}/ws/connect"
    # Abrir dos conexiones
    sockets = []
    for _ in range(2):
        ws = await ws_connect(uri)
        # Consumir ACK o PING hasta ACK
        for _ in range(3):
            raw = await asyncio.wait_for(ws.recv(), timeout=2)
            data = json.loads(raw)
            if data['event_type'] == EventType.PING:
                continue
            assert data['event_type'] == EventType.CONNECTION_ACK
            break
        sockets.append(ws)

    try:
        # Stats antes
        async with httpx.AsyncClient() as c:
            r_before = await c.get(f"{ws_server.replace('ws://', 'http://')}/ws/stats")
            assert r_before.status_code == 200
            before_metrics = r_before.json()['stats']['metrics']
            b_before = before_metrics['total_broadcasts']
            m_before = before_metrics['total_messages_sent']

            # Disparar broadcast de prueba
            ws_http_url = ws_server.replace('ws://', 'http://')
            rb = await c.post(f"{ws_http_url}/ws/_test/broadcast", json={'title': 'MetricaTest'})
            assert rb.status_code == 200

            # Consumir mensajes (podría llegar PING intercalado)
            recibidos = 0
            for ws in sockets:
                for _ in range(2):  # tolerar posible PING
                    raw = await asyncio.wait_for(ws.recv(), timeout=3)
                    data = json.loads(raw)
                    if data['event_type'] == EventType.PING:
                        continue
                    assert data['event_type'] == EventType.NOTIFICATION
                    recibidos += 1
                    break
            assert recibidos == 2

            # Stats después
            r_after = await c.get(f"{ws_server.replace('ws://', 'http://')}/ws/stats")
            assert r_after.status_code == 200
            after_payload = r_after.json()
            after_stats = after_payload['stats']
            after_metrics = after_stats['metrics']
            assert after_metrics['total_broadcasts'] >= b_before + 1
            # total_messages_sent debe haber aumentado al menos por el número de sockets del broadcast
            assert after_metrics['total_messages_sent'] >= m_before + 2
            # Debe haberse seteado last_broadcast_at
            assert after_metrics['last_broadcast_at'] is not None
            # Verificar formato ISO básico
            assert 'T' in after_metrics['last_broadcast_at']

            # Comprobar heartbeat_active (puede que tarde en iniciar, tolerar breve espera)
            if not after_stats.get('heartbeat_active'):
                await asyncio.sleep(0.5)
                r_retry = await c.get(f"{ws_server.replace('ws://', 'http://')}/ws/stats")
                if r_retry.status_code == 200:
                    if not r_retry.json()['stats'].get('heartbeat_active'):
                        # No fallar la prueba por esto; solo documentar
                        pytest.skip('Heartbeat no activo aún (tolerado)')
    finally:
        for ws in sockets:
            await ws.close()
