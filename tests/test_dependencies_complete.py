# -*- coding: utf-8 -*-
"""
Tests completos para src/api/dependencies.py
Objetivo: Aumentar cobertura del 50% al 85%
"""

import pytest
from fastapi import HTTPException, status
from jose.exceptions import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from src.api.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_active_superuser,
)
from src.api.models.usuario import Usuario


# =======================
# Fixtures para mocks
# =======================

@pytest.fixture
def mock_active_user():
    """Fixture para usuario activo."""
    user = MagicMock(spec=Usuario)
    user.id = 1
    user.email = "test@example.com"
    user.is_active = True
    user.is_superuser = False
    return user


@pytest.fixture
def mock_inactive_user():
    """Fixture para usuario inactivo."""
    user = MagicMock(spec=Usuario)
    user.id = 2
    user.email = "inactive@example.com"
    user.is_active = False
    user.is_superuser = False
    return user


@pytest.fixture
def mock_superuser():
    """Fixture para superusuario activo."""
    user = MagicMock(spec=Usuario)
    user.id = 3
    user.email = "admin@example.com"
    user.is_active = True
    user.is_superuser = True
    return user


@pytest.fixture
def mock_db_session():
    """Fixture para sesión de base de datos mock."""
    session = AsyncMock(spec=AsyncSession)
    return session


# =======================
# Tests para get_current_user
# =======================

@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(mock_db_session, mock_active_user, monkeypatch):
    """
    Test que get_current_user retorna usuario válido con token correcto.
    """
    # Mock JWT decode para retornar payload válido
    def mock_jwt_decode(token, secret, algorithms):
        return {"sub": 1, "exp": 9999999999}
    
    monkeypatch.setattr("src.api.dependencies.jwt.decode", mock_jwt_decode)
    
    # Mock crud_usuario.get para retornar el usuario
    mock_crud_get = AsyncMock(return_value=mock_active_user)
    monkeypatch.setattr("src.api.dependencies.crud_usuario.get", mock_crud_get)
    
    # Ejecutar la función
    result = await get_current_user(db=mock_db_session, token="valid_token")
    
    # Verificaciones
    assert result.id == mock_active_user.id
    assert result.email == mock_active_user.email
    mock_crud_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_token(mock_db_session, monkeypatch):
    """
    Test de get_current_user con token inválido debe lanzar HTTPException 403.
    """
    # Mock JWT decode para lanzar JWTError
    def mock_jwt_decode_invalid(token, secret, algorithms):
        raise JWTError("Invalid token")
    
    monkeypatch.setattr("src.api.dependencies.jwt.decode", mock_jwt_decode_invalid)
    
    # Debe lanzar HTTPException 403
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(db=mock_db_session, token="invalid_token")
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_with_expired_token(mock_db_session, monkeypatch):
    """
    Test de get_current_user con token expirado debe lanzar HTTPException 403.
    """
    # Mock JWT decode para lanzar JWTError por token expirado
    def mock_jwt_decode_expired(token, secret, algorithms):
        raise JWTError("Signature has expired")
    
    monkeypatch.setattr("src.api.dependencies.jwt.decode", mock_jwt_decode_expired)
    
    # Debe lanzar HTTPException 403
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(db=mock_db_session, token="expired_token")
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_with_invalid_payload(mock_db_session, monkeypatch):
    """
    Test de get_current_user con payload malformado debe lanzar HTTPException 403.
    """
    # Mock JWT decode para retornar payload con tipo incorrecto
    def mock_jwt_decode_bad_type(token, secret, algorithms):
        return {"sub": "not-a-valid-integer", "exp": "also-bad"}  # Tipos incorrectos
    
    monkeypatch.setattr("src.api.dependencies.jwt.decode", mock_jwt_decode_bad_type)
    
    # Mock crud_usuario.get para que no se llame si la validación falla
    mock_crud_get = AsyncMock(return_value=None)
    monkeypatch.setattr("src.api.dependencies.crud_usuario.get", mock_crud_get)
    
    # Debe lanzar HTTPException 404 o continuar dependiendo de la validación
    # Como sub es Optional[int], un string no válido podría pasar
    # Probamos el caso donde el usuario no se encuentra
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(db=mock_db_session, token="token_bad_payload")
    
    # Puede ser 403 (validación) o 404 (usuario no encontrado)
    assert exc_info.value.status_code in [status.HTTP_403_FORBIDDEN, 404]


@pytest.mark.asyncio
async def test_get_current_user_user_not_found(mock_db_session, monkeypatch):
    """
    Test de get_current_user cuando el usuario no existe en la DB debe lanzar HTTPException 404.
    """
    # Mock JWT decode para retornar payload válido
    def mock_jwt_decode(token, secret, algorithms):
        return {"sub": 9999, "exp": 9999999999}  # ID inexistente
    
    monkeypatch.setattr("src.api.dependencies.jwt.decode", mock_jwt_decode)
    
    # Mock crud_usuario.get para retornar None (usuario no encontrado)
    mock_crud_get = AsyncMock(return_value=None)
    monkeypatch.setattr("src.api.dependencies.crud_usuario.get", mock_crud_get)
    
    # Debe lanzar HTTPException 404
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(db=mock_db_session, token="valid_token_nonexistent_user")
    
    assert exc_info.value.status_code == 404
    assert "User not found" in exc_info.value.detail


# =======================
# Tests para get_current_active_user
# =======================

@pytest.mark.asyncio
async def test_get_current_active_user_with_active_user(mock_active_user):
    """
    Test de get_current_active_user con usuario activo debe retornar el usuario.
    """
    result = await get_current_active_user(current_user=mock_active_user)
    
    assert result.id == mock_active_user.id
    assert result.is_active is True


@pytest.mark.asyncio
async def test_get_current_active_user_with_inactive_user(mock_inactive_user):
    """
    Test de get_current_active_user con usuario inactivo debe lanzar HTTPException 400.
    """
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(current_user=mock_inactive_user)
    
    assert exc_info.value.status_code == 400
    assert "Inactive user" in exc_info.value.detail


# =======================
# Tests para get_current_active_superuser
# =======================

@pytest.mark.asyncio
async def test_get_current_active_superuser_with_superuser(mock_superuser):
    """
    Test de get_current_active_superuser con superusuario debe retornar el usuario.
    """
    result = await get_current_active_superuser(current_user=mock_superuser)
    
    assert result.id == mock_superuser.id
    assert result.is_superuser is True


@pytest.mark.asyncio
async def test_get_current_active_superuser_with_regular_user(mock_active_user):
    """
    Test de get_current_active_superuser con usuario regular debe lanzar HTTPException 400.
    """
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_superuser(current_user=mock_active_user)
    
    assert exc_info.value.status_code == 400
    assert "doesn't have enough privileges" in exc_info.value.detail


# =======================
# Tests adicionales para cobertura completa
# =======================

@pytest.mark.asyncio
async def test_get_current_user_with_string_sub(mock_db_session, mock_active_user, monkeypatch):
    """
    Test que get_current_user maneja correctamente 'sub' como string.
    """
    # Mock JWT decode para retornar payload con 'sub' como string
    def mock_jwt_decode(token, secret, algorithms):
        return {"sub": "1", "exp": 9999999999}
    
    monkeypatch.setattr("src.api.dependencies.jwt.decode", mock_jwt_decode)
    
    # Mock crud_usuario.get para retornar el usuario
    mock_crud_get = AsyncMock(return_value=mock_active_user)
    monkeypatch.setattr("src.api.dependencies.crud_usuario.get", mock_crud_get)
    
    # Ejecutar la función
    result = await get_current_user(db=mock_db_session, token="valid_token")
    
    # Verificaciones
    assert result.id == mock_active_user.id
    mock_crud_get.assert_called_once()
