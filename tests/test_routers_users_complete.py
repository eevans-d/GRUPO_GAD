# -*- coding: utf-8 -*-
"""
Tests completos para src/api/routers/users.py
Objetivo: Aumentar cobertura del 53% al 85%
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from src.api.models.usuario import Usuario
from src.shared.constants import UserLevel


# =======================
# Fixtures
# =======================

@pytest_asyncio.fixture
async def mock_user(db_session):
    """Fixture para usuario de prueba regular."""
    user = Usuario(
        dni="1234567890",
        nombre="Test",
        apellido="User",
        email="test@example.com",
        hashed_password="hashed_password",
        nivel=UserLevel.LEVEL_1,
        verificado=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def mock_admin_user(db_session):
    """Fixture para usuario administrador."""
    admin = Usuario(
        dni="0987654321",
        nombre="Admin",
        apellido="User",
        email="admin@example.com",
        hashed_password="hashed_password",
        nivel=UserLevel.LEVEL_3,
        verificado=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(token_factory, mock_user):
    """Fixture para headers de autenticación de usuario regular."""
    token = token_factory(mock_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(token_factory, mock_admin_user):
    """Fixture para headers de autenticación de administrador."""
    token = token_factory(mock_admin_user.id)
    return {"Authorization": f"Bearer {token}"}


# =======================
# Tests para GET /users/
# =======================

@pytest.mark.asyncio
async def test_read_users_list(client: AsyncClient, mock_user, auth_headers):
    """
    Test GET /users/ debe retornar lista de usuarios.
    """
    response = await client.get("/api/v1/users/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_read_users_with_pagination(client: AsyncClient, mock_user, auth_headers):
    """
    Test GET /users/ con paginación debe respetar skip y limit.
    """
    response = await client.get(
        "/api/v1/users/",
        params={"skip": 0, "limit": 10},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10


@pytest.mark.asyncio
async def test_read_users_without_auth_fails(client: AsyncClient):
    """
    Test GET /users/ sin autenticación debe fallar con 401/403.
    """
    response = await client.get("/api/v1/users/")
    
    assert response.status_code in [401, 403]


# =======================
# Tests para GET /users/me
# =======================

@pytest.mark.asyncio
async def test_read_user_me_success(client: AsyncClient, mock_user, auth_headers):
    """
    Test GET /users/me debe retornar el usuario actual.
    """
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == mock_user.email


@pytest.mark.asyncio
async def test_read_user_me_without_auth_fails(client: AsyncClient):
    """
    Test GET /users/me sin autenticación debe fallar con 401/403.
    """
    response = await client.get("/api/v1/users/me")
    
    assert response.status_code in [401, 403]


# =======================
# Tests para GET /users/{id}
# =======================

@pytest.mark.asyncio
async def test_read_user_by_id_success(client: AsyncClient, mock_user, auth_headers):
    """
    Test GET /users/{id} debe retornar usuario específico.
    """
    response = await client.get(
        f"/api/v1/users/{mock_user.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == mock_user.id
    assert data["email"] == mock_user.email


@pytest.mark.asyncio
async def test_read_user_by_id_not_found(client: AsyncClient, auth_headers):
    """
    Test GET /users/{id} con ID inexistente debe retornar 404.
    """
    response = await client.get(
        "/api/v1/users/99999",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "not exist" in data["detail"].lower()


# =======================
# Tests para POST /users/
# =======================

@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient, auth_headers):
    """
    Test POST /users/ debe crear nuevo usuario con datos válidos.
    """
    user_data = {
        "dni": "9876543210",
        "nombre": "Nuevo",
        "apellido": "Usuario",
        "email": "nuevo@example.com",
        "password": "SecurePassword123",
        "nivel": UserLevel.LEVEL_1.value,
    }
    
    response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers=auth_headers
    )
    
    # Puede ser 200 o 201 dependiendo de la implementación
    assert response.status_code in [200, 201]
    if response.status_code == 200:
        data = response.json()
        assert data["email"] == "nuevo@example.com"
        assert data["nombre"] == "Nuevo"


@pytest.mark.asyncio
async def test_create_user_duplicate_email_fails(client: AsyncClient, mock_user, auth_headers):
    """
    Test POST /users/ con email duplicado debe retornar 400.
    """
    user_data = {
        "dni": "1111111111",
        "nombre": "Duplicate",
        "apellido": "Email",
        "email": mock_user.email,  # Email ya existe
        "password": "SecurePassword123",
        "nivel": UserLevel.LEVEL_1.value,
    }
    
    response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data["detail"].lower()


@pytest.mark.asyncio
async def test_create_user_invalid_email_fails(client: AsyncClient, auth_headers):
    """
    Test POST /users/ con email inválido debe retornar 422.
    """
    user_data = {
        "dni": "2222222222",
        "nombre": "Invalid",
        "apellido": "Email",
        "email": "not-a-valid-email",  # Email mal formado
        "password": "SecurePassword123",
        "nivel": UserLevel.LEVEL_1.value,
    }
    
    response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_missing_required_fields_fails(client: AsyncClient, auth_headers):
    """
    Test POST /users/ sin campos requeridos debe retornar 422.
    """
    user_data = {
        "email": "incomplete@example.com",
        # Faltan campos requeridos como dni, nombre, apellido, password
    }
    
    response = await client.post(
        "/api/v1/users/",
        json=user_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_without_auth_fails(client: AsyncClient):
    """
    Test POST /users/ sin autenticación debe fallar con 401/403.
    """
    user_data = {
        "dni": "3333333333",
        "nombre": "No",
        "apellido": "Auth",
        "email": "noauth@example.com",
        "password": "SecurePassword123",
        "nivel": UserLevel.LEVEL_1.value,
    }
    
    response = await client.post("/api/v1/users/", json=user_data)
    
    assert response.status_code in [401, 403]


# =======================
# Tests para PUT /users/{id}
# =======================

@pytest.mark.asyncio
async def test_update_user_success(client: AsyncClient, mock_user, auth_headers):
    """
    Test PUT /users/{id} debe actualizar usuario existente.
    """
    update_data = {
        "nombre": "Updated",
        "apellido": "Name",
    }
    
    response = await client.put(
        f"/api/v1/users/{mock_user.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["nombre"] == "Updated"
    assert data["apellido"] == "Name"


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient, auth_headers):
    """
    Test PUT /users/{id} con ID inexistente debe retornar 404.
    """
    update_data = {
        "nombre": "NonExistent",
    }
    
    response = await client.put(
        "/api/v1/users/99999",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_partial_update(client: AsyncClient, mock_user, auth_headers):
    """
    Test PUT /users/{id} debe permitir actualización parcial.
    """
    # Solo actualizar teléfono
    update_data = {
        "telefono": "0987654321",
    }
    
    response = await client.put(
        f"/api/v1/users/{mock_user.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["telefono"] == "0987654321"
    # El nombre original debe permanecer
    assert data["nombre"] == mock_user.nombre


# =======================
# Tests adicionales de validación
# =======================

@pytest.mark.asyncio
async def test_update_user_with_invalid_email(client: AsyncClient, mock_user, auth_headers):
    """
    Test PUT /users/{id} con email inválido debe retornar 422.
    """
    update_data = {
        "email": "invalid-email-format",
    }
    
    response = await client.put(
        f"/api/v1/users/{mock_user.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_users_password_not_exposed_in_response(client: AsyncClient, mock_user, auth_headers):
    """
    Test que las respuestas de usuarios no expongan el password hasheado.
    """
    response = await client.get(
        f"/api/v1/users/{mock_user.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    # El password hasheado no debe estar en la respuesta
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_list_users_pagination_limits(client: AsyncClient, mock_user, auth_headers):
    """
    Test que la paginación respeta los límites correctamente.
    """
    # Crear varios usuarios adicionales para probar paginación
    for i in range(5):
        user_data = {
            "dni": f"444444444{i}",
            "nombre": f"User{i}",
            "apellido": f"Test{i}",
            "email": f"user{i}@test.com",
            "password": "TestPassword123",
            "nivel": UserLevel.LEVEL_1.value,
        }
        await client.post("/api/v1/users/", json=user_data, headers=auth_headers)
    
    # Solicitar solo 3 usuarios
    response = await client.get(
        "/api/v1/users/",
        params={"skip": 0, "limit": 3},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3


@pytest.mark.asyncio
async def test_read_users_skip_pagination(client: AsyncClient, mock_user, auth_headers):
    """
    Test que skip en paginación funciona correctamente.
    """
    # Obtener todos los usuarios
    response_all = await client.get("/api/v1/users/", headers=auth_headers)
    all_users = response_all.json()
    
    if len(all_users) > 1:
        # Obtener usuarios con skip=1
        response_skip = await client.get(
            "/api/v1/users/",
            params={"skip": 1},
            headers=auth_headers
        )
        
        assert response_skip.status_code == 200
        skipped_users = response_skip.json()
        # Debe haber uno menos que el total
        assert len(skipped_users) == len(all_users) - 1
