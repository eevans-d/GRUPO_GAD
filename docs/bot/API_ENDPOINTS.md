# 🔌 API Endpoints - Bot de Telegram GRUPO_GAD

## 📋 Información General

**Fecha de creación:** 11 de octubre de 2025  
**Autor:** Sistema de Documentación Automática  
**Versión de API:** v1  
**Base URL:** `http://localhost:8000/api/v1` (desarrollo) | `https://api.grupogad.gob.ec/api/v1` (producción)

---

## 🎯 Resumen de Endpoints Utilizados por el Bot

El bot de Telegram consume los siguientes endpoints de la API REST:

| # | Endpoint | Método | Estado | Descripción | Usado por |
|---|----------|--------|--------|-------------|-----------|
| 1 | `/auth/{telegram_id}` | GET | ⚠️ **MOCK** | Obtener nivel de autenticación de usuario | `api_service.py` |
| 2 | `/tasks/create` | POST | ⚠️ **MOCK** | Crear nueva tarea | Wizard - Paso Final |
| 3 | `/tasks/finalize` | POST | ⚠️ **MOCK** | Finalizar tarea por código | Botón "Finalizar Tarea" |
| 4 | `/tasks/user/telegram/{telegram_id}` | GET | ⚠️ **MOCK** | Obtener tareas pendientes de usuario | Lista de tareas |
| 5 | `/users` | GET | ✅ **REAL** | Obtener lista de usuarios | Selección de delegados/agentes |
| 6 | `/tasks/` | POST | ✅ **REAL** | Crear tarea (endpoint estándar) | Alternativa a `/tasks/create` |
| 7 | `/tasks/{task_id}` | GET | ✅ **REAL** | Obtener tarea por ID | Consultas individuales |

### ⚠️ Endpoints MOCK (No Implementados)

Los siguientes endpoints **NO están implementados** en la API real y requieren implementación:

1. **`GET /auth/{telegram_id}`** - Autenticación por Telegram ID
2. **`POST /tasks/create`** - Crear tarea (versión específica del bot)
3. **`POST /tasks/finalize`** - Finalizar tarea por código
4. **`GET /tasks/user/telegram/{telegram_id}`** - Tareas por Telegram ID

**Solución temporal:** El bot maneja estas respuestas con lógica local simulada. Para producción, estos endpoints **deben implementarse en la API**.

---

## 📚 Detalle de Endpoints

### 1. Autenticación - GET `/auth/{telegram_id}`

**Estado:** ⚠️ **NO IMPLEMENTADO** (Mock en el bot)

**Descripción:** Verifica el nivel de autenticación de un usuario basándose en su Telegram ID.

**Request:**
```http
GET /api/v1/auth/123456789
Authorization: Bearer <token> (opcional)
```

**Response esperado (200):**
```json
{
  "telegram_id": 123456789,
  "nivel": "admin",
  "nombre": "Juan Pérez",
  "autorizado": true
}
```

**Niveles posibles:**
- `admin` - Administrador con permisos completos
- `supervisor` - Supervisor de operaciones
- `agente` - Agente operativo estándar
- `ciudadano` - Usuario ciudadano sin permisos especiales

**Response error (404):**
```json
{
  "detail": "Usuario no encontrado"
}
```

**Uso en el bot:**
```python
from src.bot.services.api_service import ApiService

api_service = ApiService(settings.API_V1_STR)
nivel = api_service.get_user_auth_level(telegram_id=123456789)
```

**Estado actual:** El bot maneja la falta de este endpoint retornando `None` y asumiendo permisos básicos.

---

### 2. Crear Tarea - POST `/tasks/create`

**Estado:** ⚠️ **NO IMPLEMENTADO** (Alternativa: `POST /tasks/`)

**Descripción:** Crea una nueva tarea desde el bot de Telegram.

**Request:**
```http
POST /api/v1/tasks/create
Content-Type: application/json
Authorization: Bearer <token> (opcional)

{
  "tipo": "operativo",
  "codigo": "T-2025-001",
  "titulo": "Patrullaje Sector Norte",
  "descripcion": "Realizar patrullaje preventivo en el sector norte de la ciudad",
  "estado": "pending",
  "prioridad": "media",
  "delegado_id": 5,
  "asignados": [10, 15, 20]
}
```

**Response esperado (201):**
```json
{
  "id": 42,
  "tipo": "operativo",
  "codigo": "T-2025-001",
  "titulo": "Patrullaje Sector Norte",
  "descripcion": "Realizar patrullaje preventivo en el sector norte de la ciudad",
  "estado": "pending",
  "prioridad": "media",
  "delegado_id": 5,
  "asignados": [10, 15, 20],
  "creado_por": 1,
  "fecha_creacion": "2025-10-11T10:30:00Z",
  "fecha_actualizacion": "2025-10-11T10:30:00Z"
}
```

**Validaciones:**
- `codigo` debe ser único
- `tipo` debe ser uno de: `operativo`, `administrativo`, `emergencia`
- `prioridad` debe ser uno de: `baja`, `media`, `alta`, `critica`
- `delegado_id` debe existir y tener rol `delegado`
- `asignados` deben existir y tener rol `agente`

**Response error (400):**
```json
{
  "detail": "Validation Error",
  "errors": [
    {
      "field": "codigo",
      "message": "El código de tarea ya existe"
    }
  ]
}
```

**Uso en el bot:**
```python
from src.bot.services.api_service import ApiService
from src.schemas.tarea import TareaCreate

task_data = TareaCreate(
    tipo="operativo",
    codigo="T-2025-001",
    titulo="Patrullaje Sector Norte",
    descripcion="Realizar patrullaje...",
    estado="pending",
    prioridad="media",
    delegado_id=5,
    asignados=[10, 15, 20]
)

api_service = ApiService(settings.API_V1_STR)
tarea = api_service.create_task(task_data)
```

**Alternativa actual:** Se puede usar `POST /tasks/` (endpoint estándar) con el mismo payload.

---

### 3. Finalizar Tarea - POST `/tasks/finalize`

**Estado:** ⚠️ **NO IMPLEMENTADO**

**Descripción:** Finaliza una tarea utilizando su código y el ID de Telegram del usuario.

**Request:**
```http
POST /api/v1/tasks/finalize
Content-Type: application/json
Authorization: Bearer <token> (opcional)

{
  "task_code": "T-2025-001",
  "telegram_id": 123456789,
  "notas": "Patrullaje completado sin incidentes"
}
```

**Response esperado (200):**
```json
{
  "id": 42,
  "tipo": "operativo",
  "codigo": "T-2025-001",
  "titulo": "Patrullaje Sector Norte",
  "estado": "completed",
  "finalizado_por": 10,
  "fecha_finalizacion": "2025-10-11T14:30:00Z",
  "notas_finalizacion": "Patrullaje completado sin incidentes"
}
```

**Response error (404):**
```json
{
  "detail": "Tarea no encontrada"
}
```

**Response error (403):**
```json
{
  "detail": "Usuario no autorizado para finalizar esta tarea"
}
```

**Uso en el bot:**
```python
from src.bot.services.api_service import ApiService

api_service = ApiService(settings.API_V1_STR)
tarea = api_service.finalize_task(
    task_code="T-2025-001",
    telegram_id=123456789
)
```

**Estado actual:** El bot maneja la falta de este endpoint con mensaje de error genérico.

---

### 4. Tareas por Usuario Telegram - GET `/tasks/user/telegram/{telegram_id}`

**Estado:** ⚠️ **NO IMPLEMENTADO**

**Descripción:** Obtiene todas las tareas pendientes asignadas a un usuario identificado por su Telegram ID.

**Request:**
```http
GET /api/v1/tasks/user/telegram/123456789?status=pending
Authorization: Bearer <token> (opcional)
```

**Query Parameters:**
- `status` (opcional): Filtrar por estado (`pending`, `in_progress`, `completed`, `cancelled`)
- `limit` (opcional): Número máximo de resultados (default: 100)
- `offset` (opcional): Offset para paginación (default: 0)

**Response esperado (200):**
```json
[
  {
    "id": 42,
    "tipo": "operativo",
    "codigo": "T-2025-001",
    "titulo": "Patrullaje Sector Norte",
    "descripcion": "Realizar patrullaje preventivo...",
    "estado": "pending",
    "prioridad": "media",
    "delegado_id": 5,
    "asignados": [10],
    "fecha_creacion": "2025-10-11T10:30:00Z"
  },
  {
    "id": 45,
    "tipo": "administrativo",
    "codigo": "T-2025-004",
    "titulo": "Actualizar reporte mensual",
    "descripcion": "Completar reporte de actividades del mes",
    "estado": "in_progress",
    "prioridad": "alta",
    "delegado_id": 5,
    "asignados": [10, 15],
    "fecha_creacion": "2025-10-11T09:00:00Z"
  }
]
```

**Response vacío (200):**
```json
[]
```

**Uso en el bot:**
```python
from src.bot.services.api_service import ApiService

api_service = ApiService(settings.API_V1_STR)
tareas = api_service.get_user_pending_tasks(telegram_id=123456789)

# tareas es una lista de objetos Tarea
for tarea in tareas:
    print(f"{tarea.codigo}: {tarea.titulo}")
```

**Estado actual:** El bot maneja la falta de este endpoint retornando una lista vacía `[]`.

---

### 5. Listar Usuarios - GET `/users`

**Estado:** ✅ **IMPLEMENTADO**

**Descripción:** Obtiene lista de usuarios del sistema, opcionalmente filtrados por rol.

**Request:**
```http
GET /api/v1/users?role=delegado
Authorization: Bearer <token>
```

**Query Parameters:**
- `role` (opcional): Filtrar por rol (`admin`, `supervisor`, `delegado`, `agente`, `ciudadano`)
- `skip` (opcional): Offset para paginación (default: 0)
- `limit` (opcional): Límite de resultados (default: 100)

**Response (200):**
```json
[
  {
    "id": 5,
    "nombre": "María González",
    "email": "maria.gonzalez@grupogad.gob.ec",
    "role": "delegado",
    "is_active": true,
    "telegram_id": 987654321
  },
  {
    "id": 8,
    "nombre": "Carlos Ramírez",
    "email": "carlos.ramirez@grupogad.gob.ec",
    "role": "delegado",
    "is_active": true,
    "telegram_id": 123123123
  }
]
```

**Uso en el bot:**
```python
from src.bot.services.api_service import ApiService

api_service = ApiService(settings.API_V1_STR)

# Obtener todos los delegados
delegados = api_service.get_users(role="delegado")

# Obtener todos los agentes
agentes = api_service.get_users(role="agente")
```

**Referencia:** `src/api/routers/users.py:26`

---

### 6. Crear Tarea (Estándar) - POST `/tasks/`

**Estado:** ✅ **IMPLEMENTADO**

**Descripción:** Endpoint estándar para crear tareas (alternativa a `/tasks/create`).

**Request:**
```http
POST /api/v1/tasks/
Content-Type: application/json
Authorization: Bearer <token>

{
  "tipo": "operativo",
  "codigo": "T-2025-001",
  "titulo": "Patrullaje Sector Norte",
  "descripcion": "Realizar patrullaje preventivo...",
  "estado": "pending",
  "prioridad": "media"
}
```

**Response (200):**
```json
{
  "id": 42,
  "tipo": "operativo",
  "codigo": "T-2025-001",
  "titulo": "Patrullaje Sector Norte",
  "estado": "pending",
  "prioridad": "media",
  "fecha_creacion": "2025-10-11T10:30:00Z"
}
```

**Referencia:** `src/api/routers/tasks.py:53`

---

### 7. Obtener Tarea por ID - GET `/tasks/{task_id}`

**Estado:** ✅ **IMPLEMENTADO**

**Descripción:** Obtiene una tarea específica por su ID.

**Request:**
```http
GET /api/v1/tasks/42
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": 42,
  "tipo": "operativo",
  "codigo": "T-2025-001",
  "titulo": "Patrullaje Sector Norte",
  "descripcion": "Realizar patrullaje preventivo...",
  "estado": "pending",
  "prioridad": "media",
  "delegado_id": 5,
  "asignados": [10, 15],
  "fecha_creacion": "2025-10-11T10:30:00Z",
  "fecha_actualizacion": "2025-10-11T10:30:00Z"
}
```

**Response (404):**
```json
{
  "detail": "The task with this id does not exist in the system"
}
```

**Referencia:** `src/api/routers/tasks.py:158`

---

## 🔧 Configuración del Cliente API

### Inicialización

```python
from config.settings import settings
from src.bot.services.api_service import ApiService

# Sin autenticación (endpoints públicos)
api_service = ApiService(api_url=settings.API_V1_STR)

# Con autenticación JWT (endpoints protegidos)
api_service = ApiService(
    api_url=settings.API_V1_STR,
    token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
)
```

### Timeout y Reintentos

El cliente API tiene configurado:
- **Timeout:** 10 segundos por request
- **Reintentos:** No implementados (error inmediato)

**Recomendación:** Para producción, implementar lógica de reintentos:

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
```

---

## 📊 Mapeo de Funcionalidades Bot → API

| Funcionalidad del Bot | Endpoint Usado | Estado |
|-----------------------|----------------|--------|
| Inicio de sesión | `GET /auth/{telegram_id}` | ⚠️ MOCK |
| Verificar permisos | `GET /auth/{telegram_id}` | ⚠️ MOCK |
| Crear nueva tarea (wizard) | `POST /tasks/create` | ⚠️ MOCK (alternativa: `POST /tasks/`) |
| Listar mis tareas | `GET /tasks/user/telegram/{id}` | ⚠️ MOCK |
| Finalizar tarea | `POST /tasks/finalize` | ⚠️ MOCK |
| Seleccionar delegado | `GET /users?role=delegado` | ✅ REAL |
| Seleccionar agentes | `GET /users?role=agente` | ✅ REAL |
| Ver detalle de tarea | `GET /tasks/{task_id}` | ✅ REAL |

---

## ⚠️ Plan de Implementación de Endpoints Faltantes

### Prioridad Alta (P0)

1. **`POST /tasks/finalize`** - Finalizar tareas desde el bot
   - **Ubicación sugerida:** `src/api/routers/tasks.py`
   - **Estimación:** 2 horas
   - **Bloqueante:** Sí (funcionalidad crítica)

2. **`GET /tasks/user/telegram/{telegram_id}`** - Listar tareas por usuario
   - **Ubicación sugerida:** `src/api/routers/tasks.py`
   - **Estimación:** 2 horas
   - **Bloqueante:** Sí (lista de tareas no funciona)

### Prioridad Media (P1)

3. **`GET /auth/{telegram_id}`** - Autenticación por Telegram ID
   - **Ubicación sugerida:** `src/api/routers/auth.py`
   - **Estimación:** 3 horas
   - **Bloqueante:** No (puede usar lógica local temporalmente)

4. **`POST /tasks/create`** - Crear tarea (versión bot-specific)
   - **Ubicación sugerida:** `src/api/routers/tasks.py`
   - **Estimación:** 1 hora
   - **Bloqueante:** No (alternativa: `POST /tasks/` funciona)

---

## 🧪 Testing de Endpoints

### Endpoint de Health Check

Verificar que la API esté disponible:

```bash
curl http://localhost:8000/health
```

**Response esperado:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Script de Prueba Completo

```python
#!/usr/bin/env python3
"""
Script para probar endpoints del bot.
Ejecutar: python scripts/test_api_endpoints.py
"""

import requests
from config.settings import settings

API_BASE = settings.API_V1_STR or "http://localhost:8000/api/v1"

def test_endpoint(method: str, endpoint: str, **kwargs):
    """Prueba un endpoint y muestra el resultado."""
    url = f"{API_BASE}{endpoint}"
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        status = "✅" if response.status_code < 400 else "❌"
        print(f"{status} {method} {endpoint} -> {response.status_code}")
        return response
    except Exception as e:
        print(f"❌ {method} {endpoint} -> Error: {e}")
        return None

# Test endpoints implementados
print("🧪 Testing Endpoints Implementados:")
test_endpoint("GET", "/users")
test_endpoint("GET", "/tasks/")
test_endpoint("GET", "/health")

# Test endpoints mock (esperamos errores)
print("\n🧪 Testing Endpoints Mock (esperamos 404):")
test_endpoint("GET", "/auth/123456789")
test_endpoint("GET", "/tasks/user/telegram/123456789")
test_endpoint("POST", "/tasks/create", json={"tipo": "test"})
test_endpoint("POST", "/tasks/finalize", json={"task_code": "T-001"})
```

---

## 📚 Referencias

- **Cliente API Bot:** `src/bot/services/api_service.py`
- **Routers API:** `src/api/routers/`
  - `tasks.py` - Gestión de tareas
  - `users.py` - Gestión de usuarios
  - `auth.py` - Autenticación
- **Schemas:** `src/schemas/tarea.py`, `src/schemas/usuario.py`
- **Documentación OpenAPI:** `http://localhost:8000/docs` (cuando API esté corriendo)

---

## ✅ Checklist de Validación

Para Testing Manual, verificar:

- [ ] API está corriendo (`GET /health` retorna 200)
- [ ] Endpoint `/users` retorna lista de usuarios
- [ ] Endpoint `/tasks/` permite crear tareas
- [ ] Endpoints mock retornan error graceful (no crash del bot)
- [ ] Bot maneja correctamente errores 404/500 de la API
- [ ] Timeout de 10s está configurado correctamente
- [ ] Variables de entorno `API_V1_STR` configurada

---

**Última actualización:** 11 de octubre de 2025  
**Mantenedor:** Equipo de Desarrollo GRUPO_GAD  
**Contacto:** dev@grupogad.gob.ec
