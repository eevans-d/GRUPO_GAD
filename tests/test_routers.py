# tests/test_routers.py

import pytest
from src.api.main import app
from src.api.dependencies import get_current_active_user
from src.api.routers.dashboard import get_current_admin_user

# =======================
# Mock User Data
# =======================
class MockUser:
    def __init__(self, id, email, role="user"):
        self.id = id
        self.email = email
        self.role = role

mock_admin_user = {"id": 1, "username": "admin", "role": "admin"}
mock_normal_user = {"id": 2, "username": "testuser", "role": "user"}

API_PREFIX = "/api/v1"

# =======================
# Tests for Auth Router (/api/v1/auth)
# =======================
@pytest.mark.asyncio
async def test_auth_login_success(client, monkeypatch):
    """Test successful user login and token generation."""
    from src.api.services.auth import auth_service
    
    async def mock_authenticate(db, email, password):
        return MockUser(1, email)
        
    monkeypatch.setattr(auth_service, "authenticate", mock_authenticate)
    monkeypatch.setattr("src.api.routers.auth.create_access_token", lambda subject: "fake_token_123")
    
    response = await client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": "test@test.com", "password": "good_password"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "fake_token_123"
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_auth_login_invalid_credentials(client, monkeypatch):
    """Test login failure with invalid credentials."""
    from src.api.services.auth import auth_service
    
    async def mock_authenticate(db, email, password):
        return None
        
    monkeypatch.setattr(auth_service, "authenticate", mock_authenticate)
    
    response = await client.post(
        f"{API_PREFIX}/auth/login",
        data={"username": "test@test.com", "password": "wrong_password"},
    )
    
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json().get("detail")

@pytest.mark.asyncio
async def test_auth_login_missing_fields(client):
    """Test login failure with missing form fields."""
    response = await client.post(f"{API_PREFIX}/auth/login", data={"username": "test@test.com"})
    assert response.status_code == 422

# =======================
# Tests for Dashboard Router (/dashboard)
# =======================
@pytest.mark.asyncio
async def test_dashboard_unauthenticated(client):
    """Test that unauthenticated users cannot access the dashboard."""
    response = await client.get("/dashboard")
    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"

@pytest.mark.asyncio
async def test_dashboard_authenticated_admin(client):
    """Test that authenticated admin users can access the dashboard."""
    app.dependency_overrides[get_current_admin_user] = lambda: mock_admin_user
    response = await client.get("/dashboard")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

# =======================
# Tests for Users Router (/api/v1/users)
# =======================
@pytest.mark.asyncio
async def test_users_get_unauthenticated(client):
    response = await client.get(f"{API_PREFIX}/users/1")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_users_post_unauthenticated(client):
    response = await client.post(f"{API_PREFIX}/users/", json={})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_users_put_unauthenticated(client):
    response = await client.put(f"{API_PREFIX}/users/1", json={})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_users_get_not_found(client, monkeypatch, db_session):
    app.dependency_overrides[get_current_active_user] = lambda: mock_normal_user
    from src.api.crud.crud_usuario import usuario
    async def mock_get_user_none(db, id):
        return None
    monkeypatch.setattr(usuario, "get", mock_get_user_none)
    
    response = await client.get(f"{API_PREFIX}/users/999")
    app.dependency_overrides.clear()
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_users_put_not_found(client, monkeypatch, db_session):
    app.dependency_overrides[get_current_active_user] = lambda: mock_normal_user
    from src.api.crud.crud_usuario import usuario
    async def mock_get_user_none(db, id):
        return None
    monkeypatch.setattr(usuario, "get", mock_get_user_none)
    
    response = await client.put(
        f"{API_PREFIX}/users/999",
        json={
            "username": "nuevo",
            "nombre": "Test",
            "apellido": "User",
            "dni": "12345678A",
        },
    )
    app.dependency_overrides.clear()
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_users_post_email_exists(client, monkeypatch, db_session):
    app.dependency_overrides[get_current_active_user] = lambda: mock_admin_user
    from src.api.crud.crud_usuario import usuario
    async def mock_get_by_email_exists(db, email):
        return {"id": 1, "email": email}
    monkeypatch.setattr(usuario, "get_by_email", mock_get_by_email_exists)
    
    response = await client.post(f"{API_PREFIX}/users/", json={
        "email": "test@test.com", 
        "username": "test", 
        "password": "password123",
        "nombre": "Test", 
        "apellido": "User", 
        "dni": "12345678A"
    })
    app.dependency_overrides.clear()
    assert response.status_code == 400

# =======================
# Tests for Tasks Router (/api/v1/tasks)
# =======================
@pytest.mark.asyncio
async def test_tasks_get_unauthenticated(client):
    response = await client.get(f"{API_PREFIX}/tasks/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_tasks_put_unauthenticated(client):
    response = await client.put(f"{API_PREFIX}/tasks/1", json={})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_tasks_delete_unauthenticated(client):
    response = await client.delete(f"{API_PREFIX}/tasks/1")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_tasks_get_not_found(client, monkeypatch, db_session):
    app.dependency_overrides[get_current_active_user] = lambda: mock_normal_user
    from src.api.crud.crud_tarea import tarea
    async def mock_get_task_none(db, id):
        return None
    monkeypatch.setattr(tarea, "get", mock_get_task_none)
    
    response = await client.get(f"{API_PREFIX}/tasks/999")
    app.dependency_overrides.clear()
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_tasks_put_not_found(client, monkeypatch, db_session, override_cache_service):
    app.dependency_overrides[get_current_active_user] = lambda: mock_normal_user
    from src.api.crud.crud_tarea import tarea
    async def mock_get_task_none(db, id):
        return None
    monkeypatch.setattr(tarea, "get", mock_get_task_none)
    
    response = await client.put(f"{API_PREFIX}/tasks/999", json={"title": "New Title"})
    app.dependency_overrides.clear()
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_tasks_delete_not_found(client, monkeypatch, db_session, override_cache_service):
    app.dependency_overrides[get_current_active_user] = lambda: mock_normal_user
    from src.api.crud.crud_tarea import tarea
    async def mock_get_task_none(db, id):
        return None
    monkeypatch.setattr(tarea, "get", mock_get_task_none)
    
    response = await client.delete(f"{API_PREFIX}/tasks/999")
    app.dependency_overrides.clear()
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_tasks_get_success(client, monkeypatch, db_session):
    app.dependency_overrides[get_current_active_user] = lambda: mock_normal_user
    from src.api.crud.crud_tarea import tarea
    async def mock_get_multi_tasks(db, skip, limit):
        return [] # Return empty list for a clean DB
    monkeypatch.setattr(tarea, "get_multi", mock_get_multi_tasks)
    
    response = await client.get(f"{API_PREFIX}/tasks/")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []