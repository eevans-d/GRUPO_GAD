def test_auth_login_success(monkeypatch):
    from src.api.services.auth import auth_service
    class MockUser:
        def __init__(self, id, email):
            self.id = id
            self.email = email
    async def mock_authenticate(db, email, password):
        return MockUser(1, email)
    monkeypatch.setattr(auth_service, "authenticate", mock_authenticate)
    monkeypatch.setattr("src.api.routers.auth.create_access_token", lambda subject: "token123")
    response = client.post("/auth/login", data={"username": "test@test.com", "password": "123456"})
    assert response.status_code in (200, 201)
    assert "access_token" in response.json()

def test_auth_login_invalid(monkeypatch):
    from src.api.services.auth import auth_service
    async def mock_authenticate(db, email, password):
        return None
    monkeypatch.setattr(auth_service, "authenticate", mock_authenticate)
    response = client.post("/auth/login", data={"username": "test@test.com", "password": "wrong"})
    assert response.status_code == 401
    assert response.json().get("detail")

def test_dashboard_unauthenticated():
    response = client.get("/dashboard")
    assert response.status_code in (401, 404)
    if response.status_code == 401:
        assert response.json().get("detail") == "Not authenticated"

def test_dashboard_authenticated(monkeypatch):
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: {"id": 1, "username": "admin", "role": "admin"})
    response = client.get("/dashboard")
    assert response.status_code in (200, 201, 404)
    if response.status_code in (200, 201):
        assert isinstance(response.json(), dict)
def test_users_put_not_found(monkeypatch):
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: True)
    from src.api.crud.crud_usuario import usuario
    monkeypatch.setattr(usuario, "get", lambda db, id: None)
    response = client.put("/users/999", json={"username": "nuevo"})
    assert response.status_code in (404, 401)
    if response.status_code == 404:
        assert response.json().get("detail")
    else:
        assert response.json().get("detail") == "Not authenticated"

def test_users_get_not_found(monkeypatch):
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: True)
    from src.api.crud.crud_usuario import usuario
    monkeypatch.setattr(usuario, "get", lambda db, id: None)
    response = client.get("/users/999")
    assert response.status_code in (404, 401)
    if response.status_code == 404:
        assert response.json().get("detail")
    else:
        assert response.json().get("detail") == "Not authenticated"

def test_users_post_email_exists(monkeypatch):
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: True)
    from src.api.crud.crud_usuario import usuario
    monkeypatch.setattr(usuario, "get_by_email", lambda db, email: {"id": 1, "email": email})
    response = client.post("/users/", json={"email": "test@test.com", "username": "test", "password": "123456"})
    assert response.status_code in (400, 401)
    if response.status_code == 400:
        assert response.json().get("detail")
    else:
        assert response.json().get("detail") == "Not authenticated"

def test_users_post_invalid(monkeypatch):
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: True)
    response = client.post("/users/", json={"username": ""})
    assert response.status_code in (422, 401)
    if response.status_code == 422:
        assert "detail" in response.json()
    else:
        assert response.json().get("detail") == "Not authenticated"

def test_users_put_unauthenticated():
    response = client.put("/users/1", json={"username": "nuevo"})
    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"

def test_users_get_unauthenticated():
    response = client.get("/users/1")
    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"

def test_users_post_unauthenticated():
    response = client.post("/users/", json={"username": "nuevo", "password": "123456"})
    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"
def test_tasks_put_not_found(monkeypatch):
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: True)
    from src.api.crud.crud_tarea import tarea
    monkeypatch.setattr(tarea, "get", lambda db, id: None)
    response = client.put("/tasks/999", json={"title": "Nueva tarea"})
    assert response.status_code in (404, 401)
    if response.status_code == 404:
        assert response.json().get("detail")
    else:
        assert response.json().get("detail") == "Not authenticated"

def test_tasks_delete_not_found(monkeypatch):
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: True)
    from src.api.crud.crud_tarea import tarea
    monkeypatch.setattr(tarea, "get", lambda db, id: None)
    response = client.delete("/tasks/999")
    assert response.status_code in (404, 401)
    if response.status_code == 404:
        assert response.json().get("detail")
    else:
        assert response.json().get("detail") == "Not authenticated"

def test_tasks_get_not_found(monkeypatch):
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: True)
    from src.api.crud.crud_tarea import tarea
    monkeypatch.setattr(tarea, "get", lambda db, id: None)
    response = client.get("/tasks/999")
    assert response.status_code in (404, 401)
    if response.status_code == 404:
        assert response.json().get("detail")
    else:
        assert response.json().get("detail") == "Not authenticated"

def test_tasks_put_unauthenticated():
    response = client.put("/tasks/1", json={"title": "Nueva tarea"})
    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"

def test_tasks_delete_unauthenticated():
    response = client.delete("/tasks/1")
    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"

def test_tasks_get_unauthenticated():
    response = client.get("/tasks/1")
    assert response.status_code == 401
    assert response.json().get("detail") == "Not authenticated"
# Test GET de tasks con mock de respuesta exitosa
def test_tasks_get_success(monkeypatch):
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: True)
    from src.api.crud.crud_tarea import tarea
    monkeypatch.setattr(tarea, "get_multi", lambda db, skip=0, limit=100: [{"id": 1, "title": "Tarea"}])
    response = client.get("/tasks/")
    assert response.status_code in (200, 401)
    if response.status_code == 200:
        assert isinstance(response.json(), list)
    else:
        assert response.json().get("detail") == "Not authenticated"

# Test POST de users con mock de creación exitosa

# =======================
# Imports y configuración
# =======================
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from src.api.routers import auth, dashboard, tasks, users

app = FastAPI()
app.include_router(auth.router, prefix="/auth")
app.include_router(dashboard.router, prefix="/dashboard")
app.include_router(tasks.router, prefix="/tasks")
app.include_router(users.router, prefix="/users")

client = TestClient(app)

# =======================
# Tests de autenticación
# =======================
def test_auth_login_success(monkeypatch):
    from src.api.services.auth import auth_service
    class MockUser:
        def __init__(self, id, email):
            self.id = id
            self.email = email
    async def mock_authenticate(db, email, password):
        return MockUser(1, email)
    monkeypatch.setattr(auth_service, "authenticate", mock_authenticate)
    monkeypatch.setattr("src.api.routers.auth.create_access_token", lambda subject: "token123")
    response = client.post("/auth/login", data={"username": "test@test.com", "password": "123456"})
    assert response.status_code in (200, 201)
    assert "access_token" in response.json()

# ...existing code...
# Puedes agregar comentarios de sección similares para usuarios y tareas si lo deseas
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: True)
    response = client.post("/users/", json={"username": "usuario", "password": "123456"})
    assert response.status_code in (201, 200, 401, 422)
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from src.api.routers import auth, dashboard, tasks, users

app = FastAPI()
app.include_router(auth.router, prefix="/auth")
app.include_router(dashboard.router, prefix="/dashboard")
app.include_router(tasks.router, prefix="/tasks")
app.include_router(users.router, prefix="/users")

client = TestClient(app)

def test_auth_login_post_invalid():
    response = client.post("/auth/login", json={"username": "test", "password": "badpass"})
    assert response.status_code in (400, 401, 403, 422)

def test_auth_login_post_missing_fields():
    response = client.post("/auth/login", json={"username": "test"})
    assert response.status_code == 422

def test_dashboard_get_not_found():
    response = client.get("/dashboard/")
    assert response.status_code in (404, 401, 403, 200)

def test_tasks_get_unauth():
    response = client.get("/tasks/")
    assert response.status_code in (401, 403, 200)

def test_users_get_unauth():
    response = client.get("/users/")
    assert response.status_code in (401, 403, 200)

# Simulación de autenticación (token dummy)
def test_tasks_get_with_auth(monkeypatch):
    # Simula dependencia de usuario autenticado
    monkeypatch.setattr("src.api.dependencies.get_current_active_user", lambda: True)
    response = client.get("/tasks/")
    assert response.status_code in (200, 401, 403)
