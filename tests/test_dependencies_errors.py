# -*- coding: utf-8 -*-
import pytest
from httpx import AsyncClient, ASGITransport

from src.api.main import app


@pytest.mark.asyncio
async def test_protected_endpoint_with_bad_token_returns_403():
    # Usamos un endpoint protegido para provocar el uso de get_current_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/users/", headers={"Authorization": "Bearer bad.token.here"})
    # Por el handler de credenciales inválidas esperamos 403
    assert resp.status_code == 403
