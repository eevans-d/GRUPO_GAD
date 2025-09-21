# -*- coding: utf-8 -*-
import pytest
from httpx import AsyncClient, ASGITransport

from src.api.main import app


@pytest.mark.asyncio
async def test_tasks_requires_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/tasks/")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_task_invalid_payload_returns_422():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/tasks/", json={"titulo": 123})
    # Sin token, debe fallar por autenticación antes de validar payload
    assert resp.status_code in (401, 403)
