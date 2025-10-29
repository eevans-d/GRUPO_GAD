# -*- coding: utf-8 -*-
import json
import os
import time
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

# Asegurar que la app arranque sin DB real en tests
os.environ.setdefault("ALLOW_NO_DB", "1")

from src.api.main import app


@contextmanager
def ws_connection(client):
    """Context manager que maneja una conexión WS y drena el ACK inicial."""
    with client.websocket_connect("/ws/connect") as ws:
        # Consumir ACK de conexión
        initial = ws.receive_json()
        assert initial["event_type"] == "connection_ack"
        yield ws


def drain_until(ws, target_event_type, timeout=2.0):
    """Recibe mensajes hasta encontrar el tipo deseado o agotar timeout.
    Devuelve el mensaje encontrado o None.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            msg = ws.receive_json(timeout=timeout)
        except Exception:
            break
        if isinstance(msg, dict) and msg.get("event_type") == target_event_type:
            return msg
        # ignorar otros (PING, etc.)
    return None


@pytest.mark.parametrize("with_topic", [True, False])
def test_broadcast_respects_topic_filtering(with_topic):
    client = TestClient(app)

    # Conexión A: se suscribe a 'notifications'
    with ws_connection(client) as ws_a:
        subscribe_msg = {
            "event_type": "subscribe",
            "data": {"events": ["notifications"]},
        }
        ws_a.send_text(json.dumps(subscribe_msg))
        # Confirmación de suscripción (NOTIFICATION)
        _ = drain_until(ws_a, "notification", timeout=2.0)

        # Conexión B: no se suscribe
        with ws_connection(client) as ws_b:
            # Disparar broadcast con o sin topic
            payload = {
                "title": "Test Broadcast",
                "content": "Hola",
                "level": "info",
            }
            if with_topic:
                payload["topic"] = "notifications"

            resp = client.post("/ws/_test/broadcast", json=payload)
            assert resp.status_code == 200

            # Esperar recepción
            got_a = drain_until(ws_a, "notification", timeout=2.0)
            got_b = drain_until(ws_b, "notification", timeout=1.0)

            if with_topic:
                # Solo A debe recibir (suscrito al topic)
                assert got_a is not None, "A (suscrito) debió recibir con topic"
                assert got_b is None, "B (no suscrito) no debió recibir con topic"
            else:
                # Sin topic, ambos reciben
                assert got_a is not None
                assert got_b is not None
