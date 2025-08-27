# -*- coding: utf-8 -*-
"""
Tests unitarios para las operaciones CRUD de Usuario.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.api.crud.crud_usuario import CRUDUsuario
from src.api.models.usuario import Usuario
from src.schemas.usuario import UsuarioCreate, UsuarioUpdate
from src.core.security import get_password_hash, verify_password


@pytest.fixture
def mock_db_session():
    """
    Fixture que proporciona una sesión de base de datos mockeada.
    """
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def crud_usuario_instance():
    """
    Fixture que proporciona una instancia de CRUDUsuario.
    """
    return CRUDUsuario(Usuario)


@pytest.mark.asyncio
async def test_create_user(mock_db_session, crud_usuario_instance):
    """
    Test para crear un usuario.
    """
    user_in = UsuarioCreate(
        email="test@example.com",
        password="testpassword",
        nombre="Test",
        apellido="User",
        dni="12345678A",
    )
    
    # Mock the Usuario model constructor
    mock_usuario_instance = MagicMock(spec=Usuario)
    mock_usuario_instance.email = user_in.email
    mock_usuario_instance.hashed_password = get_password_hash(user_in.password)
    mock_usuario_instance.nombre = user_in.nombre
    mock_usuario_instance.apellido = user_in.apellido
    mock_usuario_instance.dni = user_in.dni

    # Configure the mock session to return the mock user instance
    mock_db_session.add.return_value = None
    mock_db_session.refresh.return_value = None
    mock_db_session.commit.return_value = None

    # Replace the actual Usuario constructor with our mock
    with pytest.MonkeyPatch().context() as m:
        m.setattr("src.api.models.usuario.Usuario", MagicMock(return_value=mock_usuario_instance))
        
        created_user = await crud_usuario_instance.create(mock_db_session, obj_in=user_in)

    mock_db_session.add.assert_called_once_with(mock_usuario_instance)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_usuario_instance)
    assert created_user.email == user_in.email
    assert created_user.nombre == user_in.nombre
    assert created_user.apellido == user_in.apellido
    assert created_user.dni == user_in.dni
    assert created_user.hashed_password is not None


@pytest.mark.asyncio
async def test_get_user_by_email(mock_db_session, crud_usuario_instance):
    """
    Test para obtener un usuario por email.
    """
    mock_user = MagicMock(spec=Usuario)
    mock_user.email = "existing@example.com"
    
    # Configure the mock session.execute to return a mock scalar result
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = mock_user

    user = await crud_usuario_instance.get_by_email(mock_db_session, email="existing@example.com")

    mock_db_session.execute.assert_called_once()
    assert user == mock_user


@pytest.mark.asyncio
async def test_update_user(mock_db_session, crud_usuario_instance):
    """
    Test para actualizar un usuario.
    """
    existing_user = MagicMock(spec=Usuario)
    existing_user.email = "old@example.com"
    existing_user.nombre = "Old"
    existing_user.hashed_password = get_password_hash("oldpassword")

    user_update = UsuarioUpdate(email="new@example.com", nombre="New", password="newpassword")

    updated_user = await crud_usuario_instance.update(mock_db_session, db_obj=existing_user, obj_in=user_update)

    mock_db_session.add.assert_called_once_with(existing_user)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(existing_user)
    assert updated_user.email == "new@example.com"
    assert updated_user.nombre == "New"
    assert updated_user.hashed_password != get_password_hash("newpassword") # Should be hashed
    assert verify_password("newpassword", updated_user.hashed_password)


@pytest.mark.asyncio
async def test_remove_user(mock_db_session, crud_usuario_instance):
    """
    Test para eliminar un usuario.
    """
    user_to_delete = MagicMock(spec=Usuario)
    user_to_delete.id = 1
    
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = user_to_delete

    deleted_user = await crud_usuario_instance.remove(mock_db_session, id=1)

    mock_db_session.delete.assert_called_once_with(user_to_delete)
    mock_db_session.commit.assert_called_once()
    assert deleted_user == user_to_delete
