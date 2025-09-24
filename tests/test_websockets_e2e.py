"""Pruebas E2E reales del subsistema WebSocket.

Escenarios:
1. Conexión sin token (modo dev) debe recibir CONNECTION_ACK.
2. Conexión con token válido recibe CONNECTION_ACK.
3. Broadcast manual desde el manager llega a múltiples clientes.

NOTA: La validación estricta en modo producción (token obligatorio) se añadirá
en un test separado para no mutar ENVIRONMENT global todavía.
"""
from __future__ import annotations

import json
import os
import asyncio
from typing import List

import pytest
from jose import jwt
from websockets.asyncio.client import connect as ws_connect  # websockets>=14 API moderna
from tests.ws_fixtures import ws_server  # noqa: F401  # Registrar fixture en este módulo

from config.settings import get_settings, settings as global_settings
from src.core.websockets import websocket_manager, WSMessage, EventType

ALGORITHM = "HS256"


def _generate_token(subject: str | int) -> str:
    """Genera un JWT usando exactamente el mismo SECRET_KEY que el router.

    Si el SECRET_KEY está vacío (escenario de test sin var de entorno), fija uno
    de prueba de forma consistente tanto en os.environ como en la instancia
    interna del proxy (si existe) para que encode/decode coincidan.
    """
    secret = getattr(global_settings, "SECRET_KEY", "")
    if not secret:
        secret = "test-secret-key"
        os.environ["SECRET_KEY"] = secret
        try:  # noqa: S110 - acceso controlado en tests
            if getattr(global_settings, "_inst", None) is not None:  # type: ignore[attr-defined]
                global_settings._inst.SECRET_KEY = secret  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - tolerar
            pass
    payload = {"sub": str(subject)}
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


@pytest.mark.asyncio
async def test_ws_connect_without_token_dev(ws_server: str):
    settings = get_settings()
    if getattr(settings, "ENVIRONMENT", "development") == "production":
        pytest.skip("En producción se exige token para conectar sin credenciales")
    uri = f"{ws_server}/ws/connect"
    async with ws_connect(uri) as ws:
        raw = await asyncio.wait_for(ws.recv(), timeout=2)
        data = json.loads(raw)
        assert data["event_type"] == EventType.CONNECTION_ACK
        assert "connection_id" in data["data"]


@pytest.mark.asyncio
async def test_ws_connect_with_token(ws_server: str):
    token = _generate_token(42)
    uri = f"{ws_server}/ws/connect?token={token}"
    async with ws_connect(uri) as ws:
        # El primer mensaje puede ser CONNECTION_ACK o un PING del heartbeat temprano.
        for _ in range(2):  # Intentar hasta 2 lecturas
            raw = await asyncio.wait_for(ws.recv(), timeout=2)
            data = json.loads(raw)
            if data["event_type"] == EventType.PING:
                continue
            assert data["event_type"] == EventType.CONNECTION_ACK
            break
        else:  # pragma: no cover - bucle agotado sin ACK
            pytest.fail("No se recibió CONNECTION_ACK tras 2 mensajes iniciales")


@pytest.mark.asyncio
async def test_ws_broadcast_reaches_all_clients(ws_server: str):
    settings = get_settings()
    if getattr(settings, "ENVIRONMENT", "development") == "production":
        pytest.skip("Broadcast test saltado en producción (endpoint de prueba deshabilitado)")

    # Abrir conexiones reales
    uri = f"{ws_server}/ws/connect"
    connections = []
    for _ in range(3):
        ws = await ws_connect(uri)
        # Consumir hasta obtener ACK (ignorando PING inicial)
        for _ in range(2):
            raw = await asyncio.wait_for(ws.recv(), timeout=2)
            data = json.loads(raw)
            if data["event_type"] == EventType.PING:
                continue
            break
        connections.append(ws)

    try:
        # Disparar broadcast vía endpoint HTTP (mismo loop)
        import httpx
        async with httpx.AsyncClient() as client_http:
            resp = await client_http.post(f"{ws_server.replace('ws://', 'http://')}/ws/_test/broadcast", json={
                "title": "BroadcastTest",
                "content": "Contenido de broadcast"
            })
            assert resp.status_code == 200
            data_resp = resp.json()
            assert data_resp.get("status") == "ok"
        received = 0
        for ws in connections:
            raw = await asyncio.wait_for(ws.recv(), timeout=3)
            data = json.loads(raw)
            # Saltar pings adicionales
            if data["event_type"] == EventType.PING:
                raw = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(raw)
            assert data["event_type"] == EventType.NOTIFICATION
            assert data["data"].get("title") == "BroadcastTest"
            received += 1
        assert received == 3
    finally:
        for ws in connections:
            await ws.close()
