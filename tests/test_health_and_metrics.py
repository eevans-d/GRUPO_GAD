# -*- coding: utf-8 -*-
import pytest
from httpx import AsyncClient
from httpx import ASGITransport

from src.api.main import app


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_uptime():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "app_uptime_seconds" in body


@pytest.mark.asyncio
async def test_health_endpoint_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"
