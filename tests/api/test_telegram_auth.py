"""
Tests for Telegram Authentication endpoints.

Test coverage:
- POST /telegram/auth/authenticate
- GET /telegram/auth/{telegram_id}
- GET /telegram/auth/verify/{token}
"""

import pytest
from fastapi import status
from unittest.mock import AsyncMock, MagicMock
import jwt
from datetime import datetime, timedelta

from src.api.schemas.telegram import TelegramAuthRequest, TelegramAuthResponse
from config.settings import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_authenticate_telegram_user_success(async_client, mock_db_session):
    """Test successful Telegram user authentication."""
    # Mock user in database
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.telegram_id = 123456789
    mock_user.nombre = "Test User"
    mock_user.role = "member"
    
    # Mock database query
    mock_result = AsyncMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_user)))
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    # Make request
    auth_data = {
        "telegram_id": 123456789,
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = await async_client.post("/api/v1/telegram/auth/authenticate", json=auth_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["authenticated"] is True
    assert data["user_id"] == 1
    assert data["telegram_id"] == 123456789
    assert data["role"] == "member"
    assert "token" in data
    assert data["message"] == "Usuario autenticado correctamente"


@pytest.mark.asyncio
async def test_authenticate_telegram_user_not_found(async_client, mock_db_session):
    """Test authentication of non-existent Telegram user."""
    # Mock empty database result
    mock_result = AsyncMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    auth_data = {
        "telegram_id": 999999999,
        "username": "nonexistent"
    }
    
    response = await async_client.post("/api/v1/telegram/auth/authenticate", json=auth_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["authenticated"] is False
    assert data["telegram_id"] == 999999999
    assert "no encontrado" in data["message"].lower()


@pytest.mark.asyncio
async def test_get_telegram_user_auth_success(async_client, mock_db_session):
    """Test GET endpoint for Telegram authentication."""
    mock_user = MagicMock()
    mock_user.id = 2
    mock_user.telegram_id = 987654321
    mock_user.nombre = "Admin User"
    mock_user.role = "admin"
    
    mock_result = AsyncMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_user)))
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    response = await async_client.get("/api/v1/telegram/auth/987654321")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["authenticated"] is True
    assert data["user_id"] == 2
    assert data["role"] == "admin"
    assert "token" in data


@pytest.mark.asyncio
async def test_verify_token_valid(async_client):
    """Test token verification with valid token."""
    # Create a valid token
    payload = {
        "sub": "123456789",
        "user_id": 1,
        "role": "member",
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    
    response = await async_client.get(f"/api/v1/telegram/auth/verify/{token}")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["valid"] is True
    assert data["telegram_id"] == 123456789
    assert data["user_id"] == 1
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_verify_token_expired(async_client):
    """Test token verification with expired token."""
    # Create an expired token
    payload = {
        "sub": "123456789",
        "user_id": 1,
        "role": "member",
        "exp": datetime.utcnow() - timedelta(days=1)  # Expired yesterday
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    
    response = await async_client.get(f"/api/v1/telegram/auth/verify/{token}")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "expirado" in data["detail"].lower()


@pytest.mark.asyncio
async def test_verify_token_invalid(async_client):
    """Test token verification with invalid token."""
    invalid_token = "invalid.jwt.token"
    
    response = await async_client.get(f"/api/v1/telegram/auth/verify/{invalid_token}")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "inválido" in data["detail"].lower()


@pytest.mark.asyncio
async def test_token_contains_correct_claims(async_client, mock_db_session):
    """Test that generated tokens contain all necessary claims."""
    mock_user = MagicMock()
    mock_user.id = 5
    mock_user.telegram_id = 111222333
    mock_user.nombre = "Claims User"
    mock_user.role = "supervisor"
    
    mock_result = AsyncMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_user)))
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    response = await async_client.get("/api/v1/telegram/auth/111222333")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    token = data["token"]
    
    # Decode token to verify claims
    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    
    assert decoded["sub"] == "111222333"
    assert decoded["user_id"] == 5
    assert decoded["role"] == "supervisor"
    assert "exp" in decoded
