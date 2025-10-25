"""
Redis Pub/Sub bridge para broadcast cross-worker de WebSockets.

Permite que múltiples procesos/workers compartan mensajes de broadcast
publicando en un canal Redis y suscribiéndose al mismo.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Optional, Protocol, cast

from src.core.logging import get_logger

ws_pubsub_logger = get_logger("websockets.pubsub")


class _BroadcastManager(Protocol):
    async def broadcast_local_dict(self, message_dict: dict[str, Any]) -> int:  # pragma: no cover - protocolo mínimo
        ...


class RedisWebSocketPubSub:
    def __init__(self, redis_url: str, channel: str = "ws_broadcast"):
        self.redis_url = redis_url
        self.channel = channel
        # Cliente Redis asíncrono (tipo dinámico del paquete redis.asyncio)
        self._redis: Optional[Any] = None
        self._subscriber_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._manager: Optional[_BroadcastManager] = None

    async def start(self, manager: _BroadcastManager) -> None:
        """Conecta a Redis y arranca la tarea de suscripción."""
        try:
            # Import local para no obligar dependencia en paths que no lo usen
            from redis import asyncio as redis
        except Exception as e:  # pragma: no cover - dependencia opcional
            ws_pubsub_logger.error(f"Redis client no disponible: {e}")
            return

        self._manager = manager
        # from_url devuelve un cliente dinámico; lo tipamos como Any para mypy
        self._redis = cast(Any, redis).from_url(self.redis_url)
        self._running = True
        self._subscriber_task = asyncio.create_task(self._subscriber_loop())
        ws_pubsub_logger.info("RedisWebSocketPubSub iniciado", channel=self.channel)

    async def stop(self) -> None:
        self._running = False
        if self._subscriber_task:
            self._subscriber_task.cancel()
            try:
                await self._subscriber_task
            except asyncio.CancelledError:
                pass
            self._subscriber_task = None
        if self._redis is not None:
            try:
                await self._redis.aclose()
            except Exception:
                pass
            self._redis = None
        ws_pubsub_logger.info("RedisWebSocketPubSub detenido")

    async def publish(self, message_dict: dict[str, Any]) -> None:
        """Publica un mensaje en el canal compartido."""
        if not self._redis:
            ws_pubsub_logger.warning("Redis no inicializado; no se publica broadcast")
            return
        try:
            payload = json.dumps(message_dict)
            await self._redis.publish(self.channel, payload)
        except Exception as e:
            ws_pubsub_logger.error(f"Error publicando broadcast en Redis: {e}")

    async def _subscriber_loop(self) -> None:
        """Consume mensajes del canal y los reenvía a conexiones locales."""
        assert self._redis is not None
        try:
            pubsub = self._redis.pubsub()
            await pubsub.subscribe(self.channel)
            ws_pubsub_logger.info("Suscrito a canal Redis", channel=self.channel)

            async for raw in pubsub.listen():
                if not self._running:
                    break
                try:
                    if raw is None:
                        continue
                    if isinstance(raw, dict):
                        if raw.get("type") != "message":
                            continue
                        data = raw.get("data")
                    else:
                        data = raw
                    if isinstance(data, (bytes, bytearray)):
                        data = data.decode("utf-8")
                    if not data:
                        continue
                    message_dict = json.loads(data)
                    # Reenviar a conexiones locales sin re-publicar
                    if self._manager is not None:
                        await self._manager.broadcast_local_dict(message_dict)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    ws_pubsub_logger.error(f"Error en subscriber Redis: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            ws_pubsub_logger.error(f"Fallo en suscripción Redis: {e}")
