# -*- coding: utf-8 -*-
"""
Tests for administrative bypass functionality.

Tests the admin endpoint security and proper access control.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch, MagicMock

from src.api.main import app
from src.api.models.usuario import Usuario
from src.shared.constants import UserLevel
from src.api.dependencies import get_current_active_superuser
from src.core.database import get_db_session


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_normal_user():
    """Mock normal user (non-admin)."""
    user = MagicMock(spec=Usuario)
    user.id = 1
    user.email = "user@test.com"
    user.is_superuser = False
    user.nivel = UserLevel.LEVEL_1
    user.is_active = True
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user (superuser)."""
    user = MagicMock(spec=Usuario)
    user.id = 2
    user.email = "admin@test.com"
    user.is_superuser = True
    user.nivel = UserLevel.LEVEL_3
    user.is_active = True
    return user


def mock_superuser_dependency_fail():
    """Mock superuser dependency that raises HTTPException for non-admin."""
    raise HTTPException(status_code=400, detail="The user doesn't have enough privileges")


def test_admin_command_requires_authentication(client):
    """Test that admin endpoint requires authentication."""
    response = client.post(
        "/api/v1/admin/agent/command",
        json={"action": "test_action", "payload": {"test": "data"}}
    )
    assert response.status_code == 401


def test_admin_command_forbidden_for_normal_user(client, token_factory, mock_normal_user):
    """Test that normal users get 403 when trying to access admin endpoint."""
    token = token_factory(mock_normal_user.id)
    
    # Override dependencias reales para evitar acceso a BD y forzar fallo de superusuario
    async def _stub_db():
        return MagicMock()
    app.dependency_overrides[get_db_session] = _stub_db
    app.dependency_overrides[get_current_active_superuser] = lambda: (_ for _ in ()).throw(HTTPException(status_code=400, detail="The user doesn't have enough privileges"))

    try:
        response = client.post(
            "/api/v1/admin/agent/command",
            json={"action": "test_action", "payload": {"test": "data"}},
            headers={"Authorization": f"Bearer {token}"}
        )
    finally:
        app.dependency_overrides.clear()
    
    # Normal user should get 400 (insufficient privileges) from get_current_active_superuser
    assert response.status_code == 400
    assert "privileges" in response.json()["detail"]


def test_admin_command_success_for_admin_user(client, token_factory, mock_admin_user):
    """Test that admin users can successfully execute commands."""
    token = token_factory(mock_admin_user.id)
    
    async def _stub_db():
        return MagicMock()
    app.dependency_overrides[get_db_session] = _stub_db
    app.dependency_overrides[get_current_active_superuser] = lambda: mock_admin_user

    with patch("src.api.routers.admin.log_security_event") as mock_log:
        try:
            response = client.post(
                "/api/v1/admin/agent/command",
                json={"action": "test_action", "payload": {"test": "data"}},
                headers={"Authorization": f"Bearer {token}"}
            )
        finally:
            app.dependency_overrides.clear()
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "accepted"
    assert "test_action" in response_data["message"]
    assert "timestamp" in response_data
    
    # Verify security logging was called
    mock_log.assert_called_once()
    call_args = mock_log.call_args
    assert call_args[1]["event_type"] == "ADMIN_COMMAND_EXECUTED"
    assert call_args[1]["details"]["user_id"] == mock_admin_user.id
    assert call_args[1]["details"]["action"] == "test_action"


def test_admin_command_with_no_payload(client, token_factory, mock_admin_user):
    """Test admin command without payload."""
    token = token_factory(mock_admin_user.id)
    
    async def _stub_db():
        return MagicMock()
    app.dependency_overrides[get_db_session] = _stub_db
    app.dependency_overrides[get_current_active_superuser] = lambda: mock_admin_user

    with patch("src.api.routers.admin.log_security_event") as mock_log:
        try:
            response = client.post(
                "/api/v1/admin/agent/command",
                json={"action": "simple_action"},
                headers={"Authorization": f"Bearer {token}"}
            )
        finally:
            app.dependency_overrides.clear()
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "accepted"
    
    # Verify logging includes payload_size=0 for no payload
    mock_log.assert_called_once()
    call_args = mock_log.call_args
    assert call_args[1]["details"]["payload_size"] == 0


def test_admin_command_validation_error(client, token_factory, mock_admin_user):
    """Test validation error for malformed requests."""
    token = token_factory(mock_admin_user.id)
    
    async def _stub_db():
        return MagicMock()
    app.dependency_overrides[get_db_session] = _stub_db
    app.dependency_overrides[get_current_active_superuser] = lambda: mock_admin_user
    try:
        # Missing required 'action' field
        response = client.post(
            "/api/v1/admin/agent/command",
            json={"payload": {"test": "data"}},
            headers={"Authorization": f"Bearer {token}"}
        )
    finally:
        app.dependency_overrides.clear()
    
    assert response.status_code == 422  # Validation error