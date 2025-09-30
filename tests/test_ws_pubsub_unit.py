import asyncio
import sys
import types
from typing import Any

import pytest

from src.core.ws_pubsub import RedisWebSocketPubSub


class FakePubSub:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self._subscribed = []

    async def subscribe(self, channel: str) -> None:
        self._subscribed.append(channel)

    async def listen(self):  # async generator
        while True:
            item = await self.queue.get()
            yield item


class FakeRedis:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.published: list[tuple[str, str]] = []

    def pubsub(self) -> FakePubSub:  # type: ignore[name-defined]
        return FakePubSub(self.queue)

    async def publish(self, channel: str, payload: str) -> None:
        self.published.append((channel, payload))

    async def aclose(self) -> None:
        pass


class FakeAsyncioModule:
    def __init__(self, queue: asyncio.Queue):
        self._queue = queue
        self.last_client: FakeRedis | None = None

    def from_url(self, _: str) -> FakeRedis:  # emulate redis.asyncio.from_url
        client = FakeRedis(self._queue)
        self.last_client = client
        return client


class DummyManager:
    def __init__(self):
        self.received: list[dict[str, Any]] = []

    async def broadcast_local_dict(self, message_dict: dict[str, Any]) -> None:
        self.received.append(message_dict)


@pytest.mark.asyncio
async def test_pubsub_start_and_forward(monkeypatch: pytest.MonkeyPatch):
    queue: asyncio.Queue = asyncio.Queue()

    # Patch "from redis import asyncio as redis" by injecting a fake module
    fake_redis_pkg = types.SimpleNamespace()
    fake_asyncio = FakeAsyncioModule(queue)
    fake_redis_pkg.asyncio = fake_asyncio
    monkeypatch.setitem(sys.modules, "redis", fake_redis_pkg)

    mgr = DummyManager()
    pubsub = RedisWebSocketPubSub("redis://fake:6379/0", channel="test_channel")
    await pubsub.start(mgr)

    # Enqueue one message as if coming from Redis
    await queue.put({"type": "message", "data": '{"event":"ECHO","data":{"x":1}}'})

    # Give the subscriber loop a brief time to process
    await asyncio.sleep(0.05)

    # Stop and assert
    await pubsub.stop()
    assert mgr.received and mgr.received[0]["event"] == "ECHO"


@pytest.mark.asyncio
async def test_publish_sends_payload(monkeypatch: pytest.MonkeyPatch):
    queue: asyncio.Queue = asyncio.Queue()
    fake_redis_pkg = types.SimpleNamespace()
    fake_asyncio = FakeAsyncioModule(queue)
    fake_redis_pkg.asyncio = fake_asyncio
    monkeypatch.setitem(sys.modules, "redis", fake_redis_pkg)

    mgr = DummyManager()
    pubsub = RedisWebSocketPubSub("redis://fake:6379/0", channel="test_channel")
    await pubsub.start(mgr)

    await pubsub.publish({"hello": "world"})
    await pubsub.stop()

    client = fake_asyncio.last_client
    assert client is not None
    assert client.published and client.published[0][0] == "test_channel"
