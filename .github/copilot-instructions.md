# Guía para Agentes de IA en GRUPO_GAD

Esta guía resume el conocimiento esencial para contribuir de forma segura y productiva en este repositorio.

## Arquitectura en 60s
- Backend FastAPI con ciclo de vida central en `src/api/main.py`:
  - Lifespan arranca DB (`init_db`), WebSocketEventEmitter e integración WS-modelos; y detiene todo en shutdown.
  - Monta routers: API (`src/api/routers/__init__.py`), WebSockets (`src/api/routers/websockets.py`) y estáticos `/static`.
- Configuración: `config/settings.py` usa Pydantic Settings con proxy perezoso (`_LazySettingsProxy`).
  - `DATABASE_URL` se resuelve por prioridad: env `DATABASE_URL` > `DB_URL` legado > componentes `POSTGRES_*`.
  - CORS/Proxies y logging controlados por envs (`CORS_ALLOWED_ORIGINS`, `TRUSTED_PROXY_HOSTS`, `LOG_LEVEL`, `ENVIRONMENT`).
- Base de datos: SQLAlchemy Async + Alembic (ver `alembic/`, `alembic.ini`).
- Tiempo real:
  - Núcleo WS en `src/core/websockets.py` (WebSocketManager, `EventType`, `WSMessage`, heartbeat, métricas internas).
  - Router WS en `src/api/routers/websockets.py` (`/ws/connect`, `/ws/stats`, manejo de mensajes y JWT con `python-jose`).
  - Emisor y cola de eventos en `src/api/middleware/websockets.py`; integración con modelos en `src/core/websocket_integration.py`.

## Flujos de desarrollo (comandos típicos)
- App local (hot-reload): `uvicorn src.api.main:app --reload`.
- Docker dev: `docker compose up -d --build` (ver `docker/docker-compose.yml`).
- Migraciones: `alembic upgrade head` (usar `DATABASE_URL`).
- Tests (pytest.ini ya configura asyncio y paths):
  - Rápido: `pytest -q`.
  - Con cobertura: `pytest -q --cov=src --cov-report=term-missing`.

## Convenciones del proyecto que debes seguir
- Settings perezosos: evita instanciar `Settings()` en import global salvo que uses `get_settings()`; para URL usa `settings.assemble_db_url()` cuando aplique.
- WebSockets:
  - En producción (`ENVIRONMENT=production`) `/ws/connect` exige JWT válido; en dev/test se tolera sin token.
  - Métricas WS accesibles vía `websocket_manager.get_stats()` y HTTP en `/ws/stats`.
  - Si agregas tipos de evento, usa `EventType` y modela payloads con `WSMessage` (datetimes en ISO strings).
  - Para manejar mensajes de cliente, extiende `handle_client_message()` en `src/api/routers/websockets.py`.
- Logging estructurado: usa `src/core/logging.get_logger()` o `setup_logging()`; no loguees datos sensibles; ya se redactan querystrings.
- Rutas API: agrega routers en `src/api/routers/__init__.py` con prefijo/tag; evita romper prefijos existentes.
- Estáticos y pruebas WS: UI simple en `dashboard/static/websocket_test.html`; script de cliente de prueba en `scripts/test_websockets.py`.

## Integraciones y límites
- JWT: `python-jose` con `HS256`, claim `sub` para user_id y opcional `role/email`.
- Proxy y CORS: `uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware` con `TRUSTED_PROXY_HOSTS`. Configura orígenes permitidos en env.
- Métricas HTTP: `/metrics` expone `app_uptime_seconds` (Prometheus simple); Prometheus ampliado está diseñado en `docs/PROMETHEUS_METRICAS_DISENO.md` (no intrusivo aún).

## Patrones de pruebas relevantes
- `tests/` incluye E2E y unitarios para WS: handshake, broadcast, métricas y tolerancia de shutdown.
- Fixture `token_factory` en `tests/conftest.py` genera JWT válidos para los tests WS.
- Política de token: prueba tolerante a entorno (producción vs no-producción) y a mutaciones de `ENVIRONMENT` en runtime.

## Puntos de referencia rápidos
- Entrada app: `src/api/main.py`.
- Router WS: `src/api/routers/websockets.py` (endpoints `/ws/connect`, `/ws/stats`).
- Manager WS: `src/core/websockets.py` (métricas: `total_messages_sent`, `total_broadcasts`, `total_send_errors`, `last_broadcast_at`).
- Config/envs: `config/settings.py` y ejemplo `docs/env/.env.production.example`.
- Documentación guía: `README.md`, `WEBSOCKET_SYSTEM_STATUS.md`, `docs/INDEX.md`.

## Qué NO hacer (guardrails)
- No exponer en producción endpoints de prueba como `POST /ws/_test/broadcast` (sólo dev/test).
- No introducir cambios funcionales de alto riesgo sin tests y docs; prioriza patrones ya existentes y bajo acoplamiento.

¿Algo ambiguo o faltante para tu tarea actual? Indica el archivo/patrón y lo aclaramos o ampliamos esta guía.
