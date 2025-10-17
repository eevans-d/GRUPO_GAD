# Guía para Agentes de IA en GRUPO_GAD

Conoce lo mínimo imprescindible para ser productivo y seguro en este repo.

## Arquitectura (vista express)
- FastAPI en `src/api/main.py` con lifespan: inicia DB (`init_db`), WS emitter/integración y los detiene en shutdown; monta routers API/WS/estáticos.
- Settings en `config/settings.py` (Pydantic + proxy perezoso). Prioridad `DATABASE_URL` > `DB_URL` > `POSTGRES_*`. No instancies `Settings()` directo; usa `get_settings()`.
- DB: SQLAlchemy Async + Alembic (`alembic/`). Para URL compuesta, usa `settings.assemble_db_url()`.
- WebSockets: `src/core/websockets.py` (WebSocketManager, `EventType`, `WSMessage`, heartbeat). ACK se envía antes del heartbeat; métricas ignoran ACK/PING; `broadcast()` incrementa `total_broadcasts`.
- Router WS: `src/api/routers/websockets.py` expone `/ws/connect`, `/ws/stats` y (solo dev/test) `POST /ws/_test/broadcast`.

## Flujos de desarrollo
- Ejecutar local: `make up` (o `docker compose up -d --build`; uvicorn solo para dev rápido sin DB).
- Migraciones: `alembic upgrade head` (requiere `DATABASE_URL`). Production: `make prod-migrate`.
- Tests: `make test` (o `pytest -q`) • Cobertura: `make test-cov` • Smoke tests: `make smoke` (HTTP), `make ws-smoke` (WebSockets).
- Deploy a Railway: Lee `RAILWAY_DEPLOYMENT_GUIDE.md` (6 pasos, 15 min). DB/Redis provisionados automáticamente.

## Convenciones clave (haz esto así aquí)
- Dependencias/Settings: accede vía helpers perezosos. Evita side effects en import.
- Validación: handler custom devuelve `{detail: "Validation Error", errors: [...]}` (Pydantic v2). Ajusta tests a esa forma.
- Logging estructurado: usa `src/core/logging.get_logger()`; decoradores en `src/api/utils/logging.py` preservan firmas (compatibles con FastAPI).
- Routers: registra en `src/api/routers/__init__.py` con prefijo/tag coherente; no rompas prefijos existentes.
- Performance: límite productivo ~30 RPS (bottleneck: pool DB). Para mejoras: revisa `PERFORMANCE_OPTIMIZATION_FINAL_REPORT.md` (roadmap 5-7x).

## WebSockets: patrones prácticos
- Conexión: en producción `ENVIRONMENT=production` exige JWT. `get_user_from_token()` usa `python-jose` (HS256; claim `sub`, opcionales `role/email`).
- Orden garantizado: `CONNECTION_ACK` se envía antes de cualquier `PING` de heartbeat.
- Métricas: `websocket_manager.get_stats()` expone `total_messages_sent` (sin ACK/PING), `total_broadcasts`, `total_send_errors`, `last_broadcast_at`.
- Extender eventos: añade a `EventType`, modela con `WSMessage` (timestampts ISO), y maneja en `handle_client_message()`.
- Broadcast desde código: `await websocket_manager.broadcast(WSMessage(event_type=EventType.NOTIFICATION, data={...}))`.
- Guardrail: no habilites `POST /ws/_test/broadcast` en producción.

## Testing eficaz (lo que funciona aquí)
- Para endpoints que tocan DB, usa `app.dependency_overrides[get_db_session]` y yield de una sesión fake (que responda a `execute().scalars().first()`).
- WebSockets E2E: consume `CONNECTION_ACK` inicial y tolera `PING` intercalado.
- CI/CD: 9 workflows en `.github/workflows/` (main: `ci-cd.yml`). Configurar 15 secrets en GitHub UI para activar (ver `GITHUB_SECRETS_QUICK_START.md`).

## Referencias rápidas
- Entrada app: `src/api/main.py` • WS Manager: `src/core/websockets.py` • Router WS: `src/api/routers/websockets.py`
- Settings/env: `config/settings.py` • Métricas HTTP: `/metrics` • UI WS simple: `dashboard/static/websocket_test.html`

¿Algo ambiguo o faltante para tu tarea? Dinos el archivo/patrón y lo documentamos aquí.
