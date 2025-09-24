"""Fixtures para pruebas WebSocket en vivo.

Levanta un servidor uvicorn real en un hilo separado para permitir
conexiones reales via websockets.client.

NOTA: Mantener el puerto fijo (8765) para simplicidad. Si falla por conflicto,
se puede parametrizar más adelante.
"""
from __future__ import annotations

import threading
import time
from typing import Iterator

import pytest
import uvicorn

from src.api.main import app


@pytest.fixture(scope="session")
def ws_server() -> Iterator[str]:
    host = "127.0.0.1"
    port = 8765
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Esperar a que el server arranque
    timeout = time.time() + 10
    while not server.started:  # type: ignore[attr-defined]
        if time.time() > timeout:
            raise RuntimeError("Timeout iniciando servidor uvicorn para pruebas WS")
        time.sleep(0.05)

    yield f"ws://{host}:{port}"

    server.should_exit = True
    thread.join(timeout=5)
