# -*- coding: utf-8 -*-
import pytest
from httpx import AsyncClient, ASGITransport

from src.api.main import app
from src.core.database import get_db_session


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_401():
    transport = ASGITransport(app=app)
    # Evitar acceso a BD en este test: stub de sesión que imita execute().scalars().first()
    class _FakeScalar:
        def first(self):
            return None

    class _FakeResult:
        def scalars(self):
            return _FakeScalar()

        # Permitir acceso por compatibilidad si se usa .first() directo
        def first(self):
            return None

    class _FakeSession:
        async def execute(self, *args, **kwargs):
            return _FakeResult()

    async def _stub_db():
        # get_db_session es un dependency generator; debemos hacer yield
        yield _FakeSession()
    app.dependency_overrides[get_db_session] = _stub_db
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/auth/login", data={"username": "bad@example.com", "password": "wrong"})
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 401
    data = resp.json()
    assert data.get("detail") == "Incorrect email or password"
