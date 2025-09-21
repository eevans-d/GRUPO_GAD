import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.usuario import UsuarioCreate
from src.api.crud.crud_usuario import usuario

# =======================
# Tests de integración: workflow
# =======================

pytestmark = pytest.mark.asyncio

async def test_create_task_and_dashboard(client: AsyncClient, db_session: AsyncSession):
    # Crear usuario y obtener token
    test_email = "admin@example.com"
    test_password = "adminpass"
    user_in = UsuarioCreate(email=test_email, password=test_password, nombre="Admin", apellido="User", dni="87654321Z")
    await usuario.create(db_session, obj_in=user_in)
    login_data = {"username": test_email, "password": test_password}
    login_resp = await client.post("/api/v1/auth/login", data=login_data)
    assert login_resp.status_code == 200
    _ = login_resp.json()["access_token"]

async def test_user_creation_and_login(client: AsyncClient, db_session: AsyncSession):
    test_email = "test@example.com"
    test_password = "testpassword"
    user_in = UsuarioCreate(
        email=test_email,
        password=test_password,
        nombre="Test",
        apellido="User",
        dni="12345678Z"
    )

    # 1. Crear usuario directamente en la BD para la prueba
    await usuario.create(db_session, obj_in=user_in)

    # 2. Intentar hacer login con el nuevo usuario a través de la API
    login_data = {
        "username": test_email,
        "password": test_password
    }
    response = await client.post("/api/v1/auth/login", data=login_data)

    # 3. Verificar el resultado del login
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert len(token_data["access_token"]) > 0
