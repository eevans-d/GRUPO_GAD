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


### Atajos con Makefile (dev)
```bash
# Servicios
make up            # levanta db, redis, api
make ps            # estado de contenedores
make logs-api      # logs de la API
make migrate       # alembic upgrade head en el contenedor api

# Validaciones
make smoke         # /metrics y /api/v1/health
make ws-smoke      # prueba E2E de WebSocket broadcast

# Calidad
make test          # pytest
make test-cov      # pytest con cobertura
make lint          # ruff
make type          # mypy
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


## 7. Auditoría y Calidad


### CI/CD

## Estado del Proyecto

### Estado actual

COMPLETADO ⚪ — Barco anclado (2025-09-23).

- Hardening aplicado hoy (no intrusivo): CORS/Proxies/Logs y autenticación WS en producción.
- Modo anclado: sin cambios funcionales; sólo documentación/CI/seguridad de bajo riesgo.

Referencias:
- Cierre de jornada: `docs/daily/2025-09-23-CIERRE.md`
- Informe de auditoría: `docs/audit/AUDIT_REPORT_2025-09-23.md`
- Resumen de estabilidad: `docs/stability-report-2025-09-23.md`

Este repositorio usa GitHub Actions con el workflow `CI`:
- Python 3.12 y Poetry 2.x con cache local del entorno (`.venv`).
- Chequeo de seguridad básico con Semgrep (`p/security-audit`).
- Base de datos en pruebas: `sqlite+aiosqlite:///:memory:` para velocidad y aislamiento.

El estado de la build se muestra en el badge superior. Puedes ver las ejecuciones y descargar el artifact de cobertura en la pestaña Actions.

## 7.1. Producción (Docker)

- Imagen: el Dockerfile de la API (`docker/Dockerfile.api`) instala dependencias desde `requirements.lock` (pin de versiones) para builds reproducibles.
- Orquestación: usa `docker/docker-compose.prod.yml` con un `.env.production`.
 - Arranque de la API: `scripts/start.sh` ejecuta Uvicorn y calcula dinámicamente el número de workers (1 en dev; en prod (2xCPU)+1, mínimo 3, configurable con `UVICORN_WORKERS`).
 - Imagen publicada en GHCR: `ghcr.io/eevans-d/grupo_gad/api:v1.0.0` (también `:latest`).

### WebSockets en Producción (cross-worker)

Para que los broadcasts WebSocket lleguen a todos los clientes en escenarios multi-worker, se habilitó integración con Redis Pub/Sub.

- Variables (en `.env.production`):
	- `REDIS_HOST=redis`
	- `REDIS_PORT=6379` (opcional)
	- `REDIS_DB=0` (opcional)
	- `REDIS_PASSWORD=` (opcional)

Con estas variables, la app publica en un canal Redis y todos los workers lo consumen, reenviando a sus conexiones locales. No se re-publican PING.

Si no defines REDIS_HOST, el sistema opera localmente (un solo proceso recomendado o sesiones sticky).

Desplegar con Docker Compose (producción):

```bash
docker compose -f docker/docker-compose.prod.yml up -d --build
```

Atajos con Makefile (prod):
```bash
make prod-up         # levanta stack de producción local
make prod-ps         # estado
make prod-logs-api   # logs de API
make prod-migrate    # alembic upgrade head
make prod-smoke      # /metrics y /api/v1/health
```

Stack de producción local (construcción local de la imagen y puerto 8001):
```bash
make prod-down-local
make prod-up-local
make prod-ps
make prod-smoke-local
```

Usar imagen publicada en GHCR (opcional, tras merge/tag):

1) Autenticarse (si es necesario):
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u <usuario_github> --password-stdin
```

2) Referenciar la imagen en tu Compose/infra:
```yaml
services:
	api:
		image: ghcr.io/eevans-d/grupo_gad/api:v1.0.0 # o :latest
		env_file:
			- .env.production
		# ...
```

Ejemplo docker run (sin Compose):
```bash
docker run -d \
  --name gad_api \
  --env-file .env.production \
  -p 8000:8000 \
  ghcr.io/eevans-d/grupo_gad/api:v1.0.0
```

Notas:
- Mantén `requirements.lock` actualizado cuando cambies dependencias (regenera y commitea).
- No incluyas secretos en el repositorio; utiliza `.env.production` en el servidor.
- Template de variables de producción disponible en `docs/env/.env.production.example`.
 - Para WebSockets con múltiples workers, define `REDIS_HOST` para habilitar Pub/Sub y difusión global.

## 8. Checklist de Entrega

- [x] Migraciones aplicadas y validadas
- [x] Tests en verde
- [x] Seguridad y robustez garantizadas
- [x] Documentación actualizada
- [x] Listo para producción

## 10. Playbook de Finalización

Se ha incorporado un Playbook universal para cerrar la “última milla” de proyectos:

- Documento principal: `docs/PLAYBOOK_FINALIZACION.md`
- Complementos relacionados: `docs/CHECKLIST_PRE_DEPLOY.md`, `docs/COBERTURA_NOTAS.md`, `docs/PROMETHEUS_METRICAS_DISENO.md`
	- Nuevos artefactos: `docs/PLAYBOOK_TRIAGE_MATRIX.md`, `docs/PLAYBOOK_RISK_SCORE_TEMPLATE.md`, `docs/PLAYBOOK_ROLLBACK_RUNBOOK.md`
	- Índice general de documentación: `docs/INDEX.md`
	- Ejemplos: `docs/risk_score_example.json`, `docs/triage_example.json`

Objetivo: acelerar transición de “casi listo” → “en producción y aprendiendo”, con foco en triage brutal, decisiones data-driven y reversibilidad.

Próximos artefactos sugeridos (no aún presentes): matrices de triage, plantilla de risk score y runbook de rollback.


## 9. Troubleshooting Docker

- Caddy no levanta o muestra error de montaje: asegúrate que el archivo `Caddyfile` existe y tiene contenido válido. Si persiste, ejecuta `docker compose down -v` y vuelve a levantar.
- La API reinicia con exit code 3: revisa `docker logs gad_api_dev` para detectar dependencias faltantes o errores de import.
- La API no está healthy: verifica `http://localhost:8000/metrics` y que la base de datos esté healthy; espera el `start_period` del healthcheck.