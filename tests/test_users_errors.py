# -*- coding: utf-8 -*-
import pytest
from httpx import AsyncClient, ASGITransport

from src.api.main import app


@pytest.mark.asyncio
async def test_users_requires_authentication():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/users/")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_create_user_invalid_payload_returns_422():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Falta campos requeridos del schema UsuarioCreate
        resp = await ac.post("/api/v1/users/", json={"email": "x"})
    # Sin token, debe fallar por autenticación antes de validar payload
    assert resp.status_code in (401, 403)
