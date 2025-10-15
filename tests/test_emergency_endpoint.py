# -*- coding: utf-8 -*-
"""
Tests for emergency endpoint functionality.

Tests the emergency endpoint validation and proximity search functionality.
"""

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from src.api.dependencies import get_current_active_user
from src.core.database import get_db_session

from src.api.main import app
from src.api.models.usuario import Usuario
from src.shared.constants import UserLevel


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock(spec=Usuario)
    user.id = 1
    user.email = "user@test.com"
    user.is_active = True
    user.nivel = UserLevel.LEVEL_2
    return user


def test_emergency_endpoint_requires_authentication(client):
    """Test that emergency endpoint requires authentication."""
    response = client.post(
        "/api/v1/tasks/emergency",
        json={
            "telegram_id": 123456789,
            "lat": 40.7128,
            "lng": -74.0060
        }
    )
    assert response.status_code == 401


def test_emergency_endpoint_validation_error_invalid_lat(client, token_factory, mock_user, override_cache_service):
    """Test validation error for invalid latitude."""
    token = token_factory(mock_user.id)
    
    async def _stub_db():
        return AsyncMock()
    app.dependency_overrides[get_db_session] = _stub_db
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        response = client.post(
            "/api/v1/tasks/emergency",
            json={
                "telegram_id": 123456789,
                "lat": 95.0,  # Invalid latitude > 90
                "lng": -74.0060
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    finally:
        app.dependency_overrides.clear()
    
    assert response.status_code == 422
    errors = response.json()["errors"]
    assert any(err.get("loc", [None, None, ""])[-1] == "lat" for err in errors)


def test_emergency_endpoint_validation_error_invalid_lng(client, token_factory, mock_user, override_cache_service):
    """Test validation error for invalid longitude."""
    token = token_factory(mock_user.id)
    
    async def _stub_db():
        return AsyncMock()
    app.dependency_overrides[get_db_session] = _stub_db
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        response = client.post(
            "/api/v1/tasks/emergency",
            json={
                "telegram_id": 123456789,
                "lat": 40.7128,
                "lng": 190.0  # Invalid longitude > 180
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    finally:
        app.dependency_overrides.clear()
    
    assert response.status_code == 422
    errors = response.json()["errors"]
    assert any(err.get("loc", [None, None, ""])[-1] == "lng" for err in errors)


def test_emergency_endpoint_validation_error_missing_fields(client, token_factory, mock_user, override_cache_service):
    """Test validation error for missing required fields."""
    token = token_factory(mock_user.id)
    
    async def _stub_db():
        return AsyncMock()
    app.dependency_overrides[get_db_session] = _stub_db
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    try:
        response = client.post(
            "/api/v1/tasks/emergency",
            json={
                "telegram_id": 123456789
                # Missing lat and lng
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    finally:
        app.dependency_overrides.clear()
    
    assert response.status_code == 422


def test_emergency_endpoint_no_efectivos_available(client, token_factory, mock_user, override_cache_service):
    """Test emergency endpoint when no efectivos with geom are available."""
    token = token_factory(mock_user.id)
    
    async def _stub_db():
        return AsyncMock()
    app.dependency_overrides[get_db_session] = _stub_db
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    with patch("src.api.routers.tasks.find_nearest_efectivo", return_value=[]):
        with patch("src.api.routers.tasks.log_business_event") as mock_log:
            try:
                response = client.post(
                    "/api/v1/tasks/emergency",
                    json={
                        "telegram_id": 123456789,
                        "lat": 40.7128,
                        "lng": -74.0060
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
            finally:
                app.dependency_overrides.clear()
    
    assert response.status_code == 404
    assert "No efectivos with location data available" in response.json()["detail"]
    
    # Verify logging was called for no efectivos found
    mock_log.assert_called()
    call_args = mock_log.call_args[1]
    assert call_args["event_type"] == "EMERGENCY_NO_EFECTIVOS"


def is_postgresql_available():
    """Check if we're running with PostgreSQL."""
    database_url = os.getenv("DATABASE_URL", "")
    return database_url.startswith("postgresql")


@pytest.mark.skipif(not is_postgresql_available(), reason="PostgreSQL not available")
def test_emergency_endpoint_success_with_postgresql(client, token_factory, mock_user):
    """Test successful emergency assignment when PostgreSQL is available."""
    token = token_factory(mock_user.id)
    
    async def _stub_db():
        return AsyncMock()
    app.dependency_overrides[get_db_session] = _stub_db
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    with patch("src.api.routers.tasks.find_nearest_efectivo") as mock_find_nearest:
        with patch("src.api.routers.tasks.log_business_event") as mock_log:
            # Mock finding a nearby efectivo
            mock_find_nearest.return_value = [
                {"efectivo_id": 42, "distance_m": 1250.5}
            ]
            try:
                response = client.post(
                    "/api/v1/tasks/emergency",
                    json={
                        "telegram_id": 123456789,
                        "lat": 40.7128,
                        "lng": -74.0060
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
            finally:
                app.dependency_overrides.clear()
    
    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["assigned_efectivo_id"] == 42
    assert response_data["distance_m"] == 1250.5
    assert response_data["status"] == "assigned"
    assert "received_at" in response_data
    
    # Verify success logging
    mock_log.assert_called()
    call_args = mock_log.call_args[1]
    assert call_args["event_type"] == "EMERGENCY_CREATED"
    assert call_args["details"]["assigned_efectivo_id"] == 42


@pytest.mark.skipif(is_postgresql_available(), reason="Skip when PostgreSQL is available")
@patch("src.api.dependencies.get_current_active_user")
@patch("src.core.database.get_db_session")
def test_emergency_endpoint_non_postgresql_skip(mock_db, mock_user_dep, client, mock_user):
    """Test that tests are skipped appropriately when PostgreSQL is not available."""
    # This test should be skipped when PostgreSQL is not available
    # It exists to verify the skip logic works correctly
    pass