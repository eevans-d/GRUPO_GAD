# -*-
"""
Tests de integración para un flujo de trabajo completo de la API.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.usuario import UsuarioCreate
from src.api.crud.crud_usuario import usuario

# Marcador para todas las pruebas en este módulo
pytestmark = pytest.mark.asyncio


async def test_user_creation_and_login(client: AsyncClient, db_session: AsyncSession):
    """ 
    Test para verificar la creación de un usuario y el posterior login.
    """
    # Datos del usuario de prueba
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
