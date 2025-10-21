"""
Tests for Telegram Tasks endpoints.

Test coverage:
- POST /telegram/tasks/create
- POST /telegram/tasks/finalize
- GET /telegram/tasks/user/{telegram_id}
- GET /telegram/tasks/code/{codigo}
"""

import pytest
from fastapi import status
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.mark.asyncio
async def test_create_task_from_telegram_success(async_client, mock_db_session):
    """Test successful task creation from Telegram bot."""
    # Mock user exists
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.telegram_id = 123456789
    mock_user.nombre = "Task Creator"
    
    # Mock no existing task with same code
    mock_user_result = AsyncMock()
    mock_user_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_user)))
    
    mock_codigo_result = AsyncMock()
    mock_codigo_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
    
    # Setup execute to return different results for different queries
    mock_db_session.execute = AsyncMock(side_effect=[mock_user_result, mock_codigo_result])
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()
    
    task_data = {
        "telegram_id": 123456789,
        "tipo": "operativa",
        "codigo": "OP-2024-001",
        "titulo": "Test Task",
        "descripcion": "Test description",
        "prioridad": "media",
        "ubicacion": "Test Location"
    }
    
    with patch('src.api.routers.telegram_tasks.websocket_manager'):
        response = await async_client.post("/api/v1/telegram/tasks/create", json=task_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["codigo"] == "OP-2024-001"
    assert "creada exitosamente" in data["message"]


@pytest.mark.asyncio
async def test_create_task_user_not_found(async_client, mock_db_session):
    """Test task creation fails when user doesn't exist."""
    mock_result = AsyncMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    task_data = {
        "telegram_id": 999999999,
        "tipo": "operativa",
        "codigo": "OP-2024-999",
        "titulo": "Test Task"
    }
    
    response = await async_client.post("/api/v1/telegram/tasks/create", json=task_data)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "no encontrado" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_task_duplicate_code(async_client, mock_db_session):
    """Test task creation fails with duplicate code."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.telegram_id = 123456789
    
    mock_existing_task = MagicMock()
    mock_existing_task.codigo = "OP-2024-001"
    
    mock_user_result = AsyncMock()
    mock_user_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_user)))
    
    mock_task_result = AsyncMock()
    mock_task_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_existing_task)))
    
    mock_db_session.execute = AsyncMock(side_effect=[mock_user_result, mock_task_result])
    
    task_data = {
        "telegram_id": 123456789,
        "tipo": "operativa",
        "codigo": "OP-2024-001",
        "titulo": "Duplicate Task"
    }
    
    response = await async_client.post("/api/v1/telegram/tasks/create", json=task_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "ya existe" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_urgent_task_broadcasts_alert(async_client, mock_db_session):
    """Test that urgent tasks trigger WebSocket broadcast."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.telegram_id = 123456789
    mock_user.nombre = "Urgent Creator"
    
    mock_user_result = AsyncMock()
    mock_user_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_user)))
    
    mock_codigo_result = AsyncMock()
    mock_codigo_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
    
    mock_db_session.execute = AsyncMock(side_effect=[mock_user_result, mock_codigo_result])
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()
    
    task_data = {
        "telegram_id": 123456789,
        "tipo": "emergencia",
        "codigo": "URGENT-001",
        "titulo": "Urgent Task",
        "prioridad": "urgente"
    }
    
    with patch('src.api.routers.telegram_tasks.websocket_manager') as mock_ws:
        mock_ws.broadcast = AsyncMock()
        response = await async_client.post("/api/v1/telegram/tasks/create", json=task_data)
        
        # Verify broadcast was called
        assert mock_ws.broadcast.called


@pytest.mark.asyncio
async def test_finalize_task_by_code_success(async_client, mock_db_session):
    """Test successful task finalization."""
    mock_task = MagicMock()
    mock_task.id = 1
    mock_task.codigo = "OP-2024-001"
    mock_task.estado = "activa"
    mock_task.titulo = "Active Task"
    mock_task.completada_en = None
    
    mock_user = MagicMock()
    mock_user.id = 2
    mock_user.telegram_id = 987654321
    mock_user.nombre = "Finalizer"
    
    mock_task_result = AsyncMock()
    mock_task_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_task)))
    
    mock_user_result = AsyncMock()
    mock_user_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_user)))
    
    mock_db_session.execute = AsyncMock(side_effect=[mock_task_result, mock_user_result])
    mock_db_session.commit = AsyncMock()
    mock_db_session.refresh = AsyncMock()
    
    finalize_data = {
        "codigo": "OP-2024-001",
        "telegram_id": 987654321,
        "observaciones": "Task completed successfully"
    }
    
    with patch('src.api.routers.telegram_tasks.websocket_manager'):
        response = await async_client.post("/api/v1/telegram/tasks/finalize", json=finalize_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["codigo"] == "OP-2024-001"
    assert "finalizada exitosamente" in data["message"]


@pytest.mark.asyncio
async def test_finalize_task_not_found(async_client, mock_db_session):
    """Test finalization fails when task doesn't exist."""
    mock_result = AsyncMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    finalize_data = {
        "codigo": "NONEXISTENT-001",
        "telegram_id": 123456789
    }
    
    response = await async_client.post("/api/v1/telegram/tasks/finalize", json=finalize_data)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "no encontrada" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_finalize_already_completed_task(async_client, mock_db_session):
    """Test finalizing an already completed task."""
    mock_task = MagicMock()
    mock_task.id = 1
    mock_task.codigo = "OP-2024-DONE"
    mock_task.estado = "completada"
    mock_task.completada_en = datetime.now()
    
    mock_user = MagicMock()
    mock_user.id = 2
    mock_user.telegram_id = 123456789
    
    mock_task_result = AsyncMock()
    mock_task_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_task)))
    
    mock_user_result = AsyncMock()
    mock_user_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_user)))
    
    mock_db_session.execute = AsyncMock(side_effect=[mock_task_result, mock_user_result])
    
    finalize_data = {
        "codigo": "OP-2024-DONE",
        "telegram_id": 123456789
    }
    
    with patch('src.api.routers.telegram_tasks.websocket_manager'):
        response = await async_client.post("/api/v1/telegram/tasks/finalize", json=finalize_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is False
    assert "ya está completada" in data["message"]


@pytest.mark.asyncio
async def test_get_user_tasks_by_telegram_success(async_client, mock_db_session):
    """Test getting user tasks by telegram_id."""
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.telegram_id = 123456789
    
    mock_task1 = MagicMock()
    mock_task1.id = 1
    mock_task1.codigo = "OP-001"
    mock_task1.titulo = "Active Task"
    mock_task1.estado = "activa"
    mock_task1.prioridad = "alta"
    mock_task1.tipo = "operativa"
    mock_task1.creada_en = datetime.now()
    
    mock_task2 = MagicMock()
    mock_task2.id = 2
    mock_task2.codigo = "OP-002"
    mock_task2.titulo = "Pending Task"
    mock_task2.estado = "pendiente"
    mock_task2.prioridad = "media"
    mock_task2.tipo = "administrativa"
    mock_task2.creada_en = datetime.now()
    
    mock_task3 = MagicMock()
    mock_task3.id = 3
    mock_task3.codigo = "OP-003"
    mock_task3.titulo = "Completed Task"
    mock_task3.estado = "completada"
    mock_task3.prioridad = "baja"
    mock_task3.tipo = "operativa"
    mock_task3.creada_en = datetime.now()
    
    mock_user_result = AsyncMock()
    mock_user_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_user)))
    
    mock_tasks_result = AsyncMock()
    mock_tasks_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_task1, mock_task2, mock_task3])))
    
    mock_db_session.execute = AsyncMock(side_effect=[mock_user_result, mock_tasks_result])
    
    response = await async_client.get("/api/v1/telegram/tasks/user/123456789")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["telegram_id"] == 123456789
    assert data["total_tasks"] == 3
    assert data["active_tasks"] == 1
    assert data["pending_tasks"] == 1
    assert data["completed_tasks"] == 1
    assert len(data["tasks"]) == 2  # Only active + pending


@pytest.mark.asyncio
async def test_get_task_by_code_success(async_client, mock_db_session):
    """Test getting task details by code."""
    mock_task = MagicMock()
    mock_task.id = 42
    mock_task.codigo = "OP-2024-042"
    mock_task.titulo = "Test Task"
    mock_task.descripcion = "Test description"
    mock_task.tipo = "operativa"
    mock_task.prioridad = "alta"
    mock_task.estado = "activa"
    mock_task.ubicacion = "Test Location"
    mock_task.creada_en = datetime(2025, 10, 21, 14, 30)
    mock_task.completada_en = None
    
    mock_result = AsyncMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=mock_task)))
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    response = await async_client.get("/api/v1/telegram/tasks/code/OP-2024-042")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == 42
    assert data["codigo"] == "OP-2024-042"
    assert data["titulo"] == "Test Task"
    assert data["tipo"] == "operativa"
    assert data["prioridad"] == "alta"
    assert data["estado"] == "activa"


@pytest.mark.asyncio
async def test_get_task_by_code_not_found(async_client, mock_db_session):
    """Test getting non-existent task by code."""
    mock_result = AsyncMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
    mock_db_session.execute = AsyncMock(return_value=mock_result)
    
    response = await async_client.get("/api/v1/telegram/tasks/code/NONEXISTENT-999")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "no encontrada" in response.json()["detail"].lower()
