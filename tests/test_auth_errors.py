# -*- coding: utf-8 -*-
import pytest
from httpx import AsyncClient, ASGITransport

from src.api.main import app


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/login", data={"username": "bad@example.com", "password": "wrong"})
    assert resp.status_code == 401
    data = resp.json()
    assert data.get("detail") == "Incorrect email or password"
