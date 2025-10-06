# -*- coding: utf-8 -*-
"""
Tests completos para src/api/routers/tasks.py
Objetivo: Aumentar cobertura del 51% al 85%
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient

from src.api.models.tarea import Tarea as TareaModel
from src.api.models.usuario import Usuario
from src.shared.constants import TaskStatus, TaskType, TaskPriority


# =======================
# Fixtures
# =======================

@pytest_asyncio.fixture
async def mock_user(db_session):
    """Fixture para usuario de prueba."""
    user = Usuario(
        dni="1234567890",
        nombre="Test",
        apellido="User",
        email="test@example.com",
        hashed_password="hashed_password",
        nivel=1,
        verificado=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def mock_task(db_session, mock_user):
    """Fixture para tarea de prueba."""
    task = TareaModel(
        codigo="TASK001",
        titulo="Tarea de prueba",
        descripcion="Descripción de prueba",
        estado=TaskStatus.PROGRAMMED,
        tipo=TaskType.PATRULLAJE,
        prioridad=TaskPriority.MEDIUM,
        inicio_programado=datetime.now(),
        delegado_usuario_id=mock_user.id,
        creado_por_usuario_id=mock_user.id,
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest.fixture
def auth_headers(token_factory, mock_user):
    """Fixture para headers de autenticación."""
    token = token_factory(mock_user.id)
    return {"Authorization": f"Bearer {token}"}


# =======================
# Tests para GET /tasks/
# =======================

@pytest.mark.asyncio
async def test_read_tasks_list(client: AsyncClient, mock_task, auth_headers):
    """
    Test GET /tasks/ debe retornar lista de tareas.
    """
    response = await client.get("/api/v1/tasks/", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["codigo"] == "TASK001"


@pytest.mark.asyncio
async def test_read_tasks_with_pagination(client: AsyncClient, mock_task, auth_headers):
    """
    Test GET /tasks/ con paginación debe respetar skip y limit.
    """
    response = await client.get(
        "/api/v1/tasks/",
        params={"skip": 0, "limit": 10},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10


@pytest.mark.asyncio
async def test_read_tasks_without_auth_fails(client: AsyncClient):
    """
    Test GET /tasks/ sin autenticación debe fallar con 401/403.
    """
    response = await client.get("/api/v1/tasks/")
    
    assert response.status_code in [401, 403]


# =======================
# Tests para GET /tasks/{id}
# =======================

@pytest.mark.asyncio
async def test_read_task_by_id_success(client: AsyncClient, mock_task, auth_headers):
    """
    Test GET /tasks/{id} debe retornar tarea específica.
    """
    response = await client.get(
        f"/api/v1/tasks/{mock_task.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == mock_task.id
    assert data["codigo"] == "TASK001"
    assert data["titulo"] == "Tarea de prueba"


@pytest.mark.asyncio
async def test_read_task_by_id_not_found(client: AsyncClient, auth_headers):
    """
    Test GET /tasks/{id} con ID inexistente debe retornar 404.
    """
    response = await client.get(
        "/api/v1/tasks/99999",
        headers=auth_headers
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "not exist" in data["detail"].lower()


# =======================
# Tests para POST /tasks/
# =======================

@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient, mock_user, auth_headers):
    """
    Test POST /tasks/ debe crear nueva tarea con datos válidos.
    """
    task_data = {
        "codigo": "TASK002",
        "titulo": "Nueva tarea",
        "descripcion": "Descripción de nueva tarea",
        "tipo": TaskType.INVESTIGACION.value,
        "prioridad": TaskPriority.HIGH.value,
        "inicio_programado": (datetime.now() + timedelta(hours=1)).isoformat(),
        "delegado_usuario_id": mock_user.id,
        "creado_por_usuario_id": mock_user.id,
    }
    
    response = await client.post(
        "/api/v1/tasks/",
        json=task_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["codigo"] == "TASK002"
    assert data["titulo"] == "Nueva tarea"
    assert data["tipo"] == TaskType.INVESTIGACION.value


@pytest.mark.asyncio
async def test_create_task_invalid_data_fails(client: AsyncClient, auth_headers):
    """
    Test POST /tasks/ con datos inválidos debe retornar 422.
    """
    # Datos incompletos (falta campos requeridos)
    task_data = {
        "titulo": "Tarea incompleta",
    }
    
    response = await client.post(
        "/api/v1/tasks/",
        json=task_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_without_auth_fails(client: AsyncClient):
    """
    Test POST /tasks/ sin autenticación debe fallar con 401/403.
    """
    task_data = {
        "codigo": "TASK003",
        "titulo": "Nueva tarea",
        "tipo": TaskType.PATRULLAJE.value,
        "inicio_programado": datetime.now().isoformat(),
        "delegado_usuario_id": 1,
        "creado_por_usuario_id": 1,
    }
    
    response = await client.post("/api/v1/tasks/", json=task_data)
    
    assert response.status_code in [401, 403]


# =======================
# Tests para PUT /tasks/{id}
# =======================

@pytest.mark.asyncio
async def test_update_task_success(client: AsyncClient, mock_task, auth_headers):
    """
    Test PUT /tasks/{id} debe actualizar tarea existente.
    """
    update_data = {
        "titulo": "Tarea actualizada",
        "descripcion": "Descripción actualizada",
        "estado": TaskStatus.IN_PROGRESS.value,
    }
    
    response = await client.put(
        f"/api/v1/tasks/{mock_task.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["titulo"] == "Tarea actualizada"
    assert data["descripcion"] == "Descripción actualizada"
    assert data["estado"] == TaskStatus.IN_PROGRESS.value


@pytest.mark.asyncio
async def test_update_task_not_found(client: AsyncClient, auth_headers):
    """
    Test PUT /tasks/{id} con ID inexistente debe retornar 404.
    """
    update_data = {
        "titulo": "Actualización inexistente",
    }
    
    response = await client.put(
        "/api/v1/tasks/99999",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_task_partial_update(client: AsyncClient, mock_task, auth_headers):
    """
    Test PUT /tasks/{id} debe permitir actualización parcial.
    """
    # Solo actualizar prioridad
    update_data = {
        "prioridad": TaskPriority.URGENT.value,
    }
    
    response = await client.put(
        f"/api/v1/tasks/{mock_task.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["prioridad"] == TaskPriority.URGENT.value
    # El título original debe permanecer
    assert data["titulo"] == "Tarea de prueba"


# =======================
# Tests para DELETE /tasks/{id}
# =======================

@pytest.mark.asyncio
async def test_delete_task_success(client: AsyncClient, mock_task, auth_headers):
    """
    Test DELETE /tasks/{id} debe eliminar tarea existente.
    """
    task_id = mock_task.id
    
    response = await client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    
    # Verificar que la tarea fue eliminada
    get_response = await client.get(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_not_found(client: AsyncClient, auth_headers):
    """
    Test DELETE /tasks/{id} con ID inexistente debe retornar 404.
    """
    response = await client.delete(
        "/api/v1/tasks/99999",
        headers=auth_headers
    )
    
    assert response.status_code == 404


# =======================
# Tests para POST /tasks/emergency
# =======================

@pytest.mark.asyncio
async def test_create_emergency_with_mock(client: AsyncClient, auth_headers, monkeypatch):
    """
    Test POST /tasks/emergency debe crear emergencia y asignar efectivo.
    """
    # Mock find_nearest_efectivo para retornar efectivo cercano
    async def mock_find_nearest(db, lat, lng, limit):
        return [{"efectivo_id": 1, "distance_m": 150.5}]
    
    monkeypatch.setattr(
        "src.api.routers.tasks.find_nearest_efectivo",
        mock_find_nearest
    )
    
    emergency_data = {
        "telegram_id": 123456,
        "lat": -0.180653,
        "lng": -78.467838,
    }
    
    response = await client.post(
        "/api/v1/tasks/emergency",
        json=emergency_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["assigned_efectivo_id"] == 1
    assert data["distance_m"] == 150.5
    assert data["status"] == "assigned"
    assert "received_at" in data


@pytest.mark.asyncio
async def test_create_emergency_no_efectivos_available(client: AsyncClient, auth_headers, monkeypatch):
    """
    Test POST /tasks/emergency sin efectivos disponibles debe retornar 404.
    """
    # Mock find_nearest_efectivo para retornar lista vacía
    async def mock_find_nearest_empty(db, lat, lng, limit):
        return []
    
    monkeypatch.setattr(
        "src.api.routers.tasks.find_nearest_efectivo",
        mock_find_nearest_empty
    )
    
    emergency_data = {
        "telegram_id": 123456,
        "lat": -0.180653,
        "lng": -78.467838,
    }
    
    response = await client.post(
        "/api/v1/tasks/emergency",
        json=emergency_data,
        headers=auth_headers
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "efectivos" in data["detail"].lower()


@pytest.mark.asyncio
async def test_create_emergency_invalid_coordinates(client: AsyncClient, auth_headers):
    """
    Test POST /tasks/emergency con coordenadas inválidas debe retornar 422.
    """
    # Latitud fuera de rango
    emergency_data = {
        "telegram_id": 123456,
        "lat": 95.0,  # Inválido (debe estar entre -90 y 90)
        "lng": -78.467838,
    }
    
    response = await client.post(
        "/api/v1/tasks/emergency",
        json=emergency_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_emergency_service_error(client: AsyncClient, auth_headers, monkeypatch):
    """
    Test POST /tasks/emergency con error del servicio debe retornar 500.
    """
    # Mock find_nearest_efectivo para lanzar excepción
    async def mock_find_nearest_error(db, lat, lng, limit):
        raise Exception("Service error")
    
    monkeypatch.setattr(
        "src.api.routers.tasks.find_nearest_efectivo",
        mock_find_nearest_error
    )
    
    emergency_data = {
        "telegram_id": 123456,
        "lat": -0.180653,
        "lng": -78.467838,
    }
    
    response = await client.post(
        "/api/v1/tasks/emergency",
        json=emergency_data,
        headers=auth_headers
    )
    
    assert response.status_code == 500
    data = response.json()
    assert "error" in data["detail"].lower()


# =======================
# Tests adicionales de validación
# =======================

@pytest.mark.asyncio
async def test_create_task_with_invalid_type(client: AsyncClient, auth_headers):
    """
    Test POST /tasks/ con tipo inválido debe retornar 422.
    """
    task_data = {
        "codigo": "TASK004",
        "titulo": "Tarea con tipo inválido",
        "tipo": "tipo_invalido",  # No es un TaskType válido
        "inicio_programado": datetime.now().isoformat(),
        "delegado_usuario_id": 1,
        "creado_por_usuario_id": 1,
    }
    
    response = await client.post(
        "/api/v1/tasks/",
        json=task_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_task_with_invalid_status(client: AsyncClient, mock_task, auth_headers):
    """
    Test PUT /tasks/{id} con estado inválido debe retornar 422.
    """
    update_data = {
        "estado": "estado_invalido",  # No es un TaskStatus válido
    }
    
    response = await client.put(
        f"/api/v1/tasks/{mock_task.id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422
