# 📦 Documentación Final - GRUPO GAD

[![CI](https://github.com/eevans-d/GRUPO_GAD/actions/workflows/ci.yml/badge.svg)](https://github.com/eevans-d/GRUPO_GAD/actions/workflows/ci.yml)

## 1. Descripción General
- Proyecto GRUPO GAD: API y backend para gestión de tareas, usuarios y operaciones de seguridad.
- Stack: Python 3.12+, FastAPI, SQLAlchemy Async, Alembic, Poetry 2.x, Docker.

## 2. Instalación y Setup

### Requisitos
- Python 3.12+
- Docker (opcional)
- Poetry 2.x

### Instalación
```bash
git clone https://github.com/eevans-d/GRUPO_GAD.git
cd GRUPO_GAD
poetry install
cp .env.example .env
```

### Migraciones
```bash
alembic upgrade head
```

### Tests
```bash
# Ejecución rápida local
pytest --disable-warnings -v

# Opcional: con cobertura como en la CI
pytest --disable-warnings -v --cov=src --cov-report=term-missing
```

## 3. Despliegue

### Local
```bash
uvicorn src.api.main:app --reload
```

### Desarrollo con Docker (recomendado)
Levantar entorno dev (Postgres, Redis, API, Bot, Caddy opcional):
```bash
docker compose up -d --build
```

Ver estado de servicios y healthchecks:
```bash
docker compose ps
```

Logs de la API:
```bash
docker logs -f gad_api_dev
```

Endpoints útiles:
- API: http://localhost:8000
- Métricas: http://localhost:8000/metrics
- Dashboard via Caddy (si está activo): http://localhost

Limpieza profunda y rebuild si algo se queda en mal estado (montajes, cache de build, etc.):
```bash
docker compose down -v
docker compose up -d --build
```


## 4. Endpoints Principales

- `/auth/login` - Autenticación de usuarios
- `/users/` - CRUD de usuarios
- `/tasks/` - CRUD de tareas
- `/dashboard/` - Panel de control

### Ejemplos de uso con cURL

**Login:**
```bash
curl -X POST "http://localhost:8000/auth/login" -d "username=usuario&password=contraseña"
```

**Crear usuario:**
```bash
curl -X POST "http://localhost:8000/users/" -H "Content-Type: application/json" -d '{"email":"test@test.com","password":"123456","nombre":"Test","apellido":"User"}'
```

**Crear tarea:**
```bash
curl -X POST "http://localhost:8000/tasks/" -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"titulo":"Nueva tarea","tipo":"PATRULLAJE","delegado_usuario_id":1,"inicio_programado":"2025-09-12T10:00:00"}'
```

### Ejemplo de uso en Python (requests)
```python
import requests

# Login
resp = requests.post("http://localhost:8000/auth/login", data={"username": "usuario", "password": "contraseña"})
token = resp.json()["access_token"]

# Crear tarea
headers = {"Authorization": f"Bearer {token}"}
data = {"titulo": "Nueva tarea", "tipo": "PATRULLAJE", "delegado_usuario_id": 1, "inicio_programado": "2025-09-12T10:00:00"}
resp = requests.post("http://localhost:8000/tasks/", headers=headers, json=data)
print(resp.json())
```

## 4.1. Preguntas Frecuentes (FAQ)

**¿Por qué no puedo conectarme a la base de datos?**
- Verifica la variable `DATABASE_URL` en tu `.env` y que el servicio esté activo.

**¿Cómo restauro la base de datos si algo sale mal?**
- Haz una copia de seguridad del archivo `dev.db` (SQLite) o usa herramientas de backup de PostgreSQL.

**¿Dónde encuentro los logs de errores?**
- Revisa la carpeta `logs/` si está configurada, o la salida de la terminal.

## 4.2. Mejores Prácticas Rápidas

- No subas archivos `.env` ni credenciales al repositorio.
- Ejecuta los tests antes de cada despliegue.
- Haz backup de la base de datos antes de cambios mayores.
- Usa Docker para producción si es posible.

## 5. Seguridad

- Validación de campos sensibles en actualizaciones
- Hash de contraseñas
- Tokens JWT para autenticación

## 6. Migraciones y Base de Datos

- Alembic configurado para SQLite y PostgreSQL
- Migraciones reproducibles y seguras

## 7. Auditoría y Calidad

- Linter: ruff
- Tipado: mypy
- Tests: pytest (umbral de cobertura en CI: 85%)
- Script de auditoría de seguridad incluido

### CI/CD

Este repositorio usa GitHub Actions con el workflow `CI`:
- Python 3.12 y Poetry 2.x con cache local del entorno (`.venv`).
- Lint con `ruff` y type-check con `mypy` (no bloqueante de momento).
- Pruebas con `pytest` y reporte de cobertura (HTML como artifact y `--cov-fail-under=85`).
- Base de datos en pruebas: `sqlite+aiosqlite:///:memory:` para velocidad y aislamiento.

El estado de la build se muestra en el badge superior. Puedes ver las ejecuciones y descargar el artifact de cobertura en la pestaña Actions.

## 8. Checklist de Entrega

- [x] Migraciones aplicadas y validadas
- [x] Tests en verde
- [x] Seguridad y robustez garantizadas
- [x] Documentación actualizada
- [x] Listo para producción

## 9. Troubleshooting Docker

- Caddy no levanta o muestra error de montaje: asegúrate que el archivo `Caddyfile` existe y tiene contenido válido. Si persiste, ejecuta `docker compose down -v` y vuelve a levantar.
- La API reinicia con exit code 3: revisa `docker logs gad_api_dev` para detectar dependencias faltantes o errores de import.
- La API no está healthy: verifica `http://localhost:8000/metrics` y que la base de datos esté healthy; espera el `start_period` del healthcheck.