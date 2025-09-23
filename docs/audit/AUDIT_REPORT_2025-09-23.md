# Informe de Auditoría Integral — GRUPO_GAD (2025-09-23)

[Repo] https://github.com/eevans-d/GRUPO_GAD  
[Descripción] Backend/API para gestión operativa (usuarios, tareas, dashboard, bot)  
[Stack] Python 3.12, FastAPI, SQLAlchemy Async, Alembic, Pydantic v2, Uvicorn, Docker, Caddy, Redis, PostgreSQL, Poetry 2.x, GitHub Actions  
[Artefactos] API REST + WebSockets, migraciones Alembic, CI con lint/type/tests, Docker multi-stage, Compose, Caddyfile, pruebas unitarias/integración, reportes de estabilidad, documentación operativa.

## Resumen Ejecutivo

Salud global: 84/100
- Fortaleza: arquitectura limpia con FastAPI, separación de capas, DB async; WebSockets en tiempo real; CI con mypy/ruff/pytest; Docker reproducible; healthchecks y métricas básicas.  
- Riesgos clave (alta severidad): CORS permisivo con credenciales; cabeceras ProxyHeaders confiando en todos los hosts; tokens/SECRET_KEY vía entorno sin políticas y sin rotación; logging de URL completo (posible exposición de query con token); Compose con contraseñas por defecto expuestas; autenticación WS simulada sin validación JWT en handshake.
- Oportunidades: hardening de seguridad y cabeceras; tightening CORS; sanitización de logs; WS auth/claims; pruebas E2E de sockets; seguridad en CI (SCA/SAST/Container scan).  

KPIs actuales (estimados por configuración y CI):
- Cobertura mínima garantizada por CI: >=85% (threshold pytest --cov-fail-under=85).  
- Complejidad: no se observan módulos > 200 loc con alta complejidad ciclomática; manager de WebSockets mantiene SRP razonable; flag complexity>10: aislado a routers de negocio (pendiente medir con radon).  
- Dependencias: versions pinneadas en requirements.lock; sin CVEs críticas conocidas a priori; requiere verificación SCA.

Recomendación prioritaria (0–72h): aplicar hardening de CORS/proxy/headers, validar JWT en /ws/connect, rotar secretos y evitar defaults en Compose.

## Puntuación por Dimensión (1–10)
- Arquitectura: 9  ✅  
- Calidad de Código: 8  ✅  
- Seguridad: 6  ⚠️  
- Performance: 8  ✅  
- Testing: 8  ✅  
- DevOps/CI-CD: 8  ✅  
- Documentación: 9  ✅  

Salud global ponderada: 84/100

## 1) Arquitectura (SOLID, escalabilidad) — 9/10 ✅
Evidencia: FastAPI app con lifespan y middleware propios (`src/api/main.py`); routers segregados (`src/api/routers/*`); DB async con `create_async_engine` y sesiones `async_sessionmaker` (`src/core/database.py`); WebSockets con manager dedicado (`src/core/websockets.py`) y emisor/middleware (`src/api/middleware/websockets.py`); integrador con models (`src/core/websocket_integration.py`).
- Positivos:
  - Separación clara de responsabilidades: routers, core (db, security, websockets), middleware, settings.
  - Lifespan asíncrono coordina DB, WebSockets emitter e integrador; health endpoint y /metrics.
  - Docker multi-stage y reverse proxy con Caddy listos para despliegue.
- Mejora:
  - Consolidar configuración CORS/Proxy/Headers en settings por entorno.  
  - Reducir globales en integrador (inyectar dependencias en startup) para pruebas más aislables.

## 2) Calidad de Código (smells/duplicación) — 8/10 ✅
Evidencia: Ruff y mypy en CI; exclusiones mypy para nuevos módulos (websockets, middleware) marcadas como temporales (pyproject.toml). Tests pasan; ruff reporta issues menores (F541, F401, E501).
- Positivos:
  - Tipado estricto en la mayoría del árbol; helpers pydantic-settings sin side effects en import.
  - WebSocketManager con métodos send/broadcast/heartbeat bien definidos; uso de modelos Pydantic para mensajes.
- Smells menores:
  - Exclusiones mypy en módulos clave (websockets) — plan de reducción sugerido.
  - Logging con f-strings redundantes y líneas largas; limpiar para ruff green.

## 3) Seguridad (OWASP, secretos) — 6/10 ⚠️
Evidencia:
- `CORSMiddleware` con `allow_origins = ALLOWED_HOSTS` y `allow_credentials=True` por defecto; `ALLOWED_HOSTS` = ["*"] (`config/settings.py:110`); riesgo: credenciales + wildcard no recomendado.  
- `ProxyHeadersMiddleware` confiando en `trusted_hosts=["*"]` (`src/api/main.py`), abre spoofing de IP a través de X-Forwarded-* si no hay hardening en proxy.  
- Logging de URL completo en `log_requests` incluye query string; el WS `websockets.py` acepta `token` por query, lo que podría aparecer en logs.  
- `docker-compose.yml` define `POSTGRES_PASSWORD` por defecto (gad_password) y construye `DATABASE_URL` interpolando credenciales; riesgo de despliegue accidental con defaults.  
- WebSockets: `get_user_from_token` con TODO — no valida JWT real en handshake; permite conexiones no autenticadas si no se envía token.  
- Secretos gestionados vía entorno sin rotación ni escaneo SOPS/secret manager.
Acciones:
- CORS: fijar allow_origins explícitos en producción; desactivar allow_credentials o limitarlo a dominios de confianza.
- Proxy headers: limitar trusted_hosts y/o confiar solo en Caddy/Nginx; en Caddy, set headers estándar y quitar hop-by-hop; activar TLS en producción.
- Sanitizar logs: no loggear query completa; redactar parámetros sensibles (token, Authorization).  
- WS: exigir JWT por subprotocol/Authorization header o query firmada; validar con jose y claims (exp, aud).  
- Compose: eliminar defaults de secretos en prod; usar env_file .env.production y variables required; añadir ejemplos en docs.

## 4) Performance (Big O, cuellos) — 8/10 ✅
Evidencia: DB pooling configurado; circuit breaker para sesiones; StaticPool para sqlite en tests; heartbeat WS cada 30s; endpoints ligeros.  
- Riesgos: broadcast serial por conexión (await secuencial) puede ser cuello con N alto; usar gather con límites; backpressure para colas de eventos.  
- Mejoras: parametrizar heartbeat_interval; métricas Prometheus (conteos WS, latencias) — actualmente /metrics es básico.

## 5) Testing (cobertura, AAA) — 8/10 ✅
Evidencia: pytest con cov>=85% fail-under; múltiples tests unit e integración; `tests/test_health_and_metrics.py` usa ASGITransport.  
- Faltan: pruebas E2E para WebSockets (con websockets/lib) y auth WS; tests de seguridad (CORS, headers).  
- Acción: añadir test de handshake WS con JWT, ping/pong, y broadcasting; mocks de DB para integrador.

## 6) DevOps/CI-CD — 8/10 ✅
Evidencia: GitHub Actions (ci.yml y stability.yml), cache .venv, ruff, mypy, pytest, semgrep básico, upload de htmlcov; Dockerfile.api multi-stage con non-root y HEALTHCHECK; Compose con healthchecks para db, redis y api; Caddy reverse_proxy.  
- Pendiente: SCA con pip-audit o safety; Trivy para imágenes; CodeQL; matrix Python 3.12/3.13; retención de artifacts de cobertura; gates para main con branch protection.  
- Infra prod: TLS en Caddy; rate limiting; WAF opcional; logs centralizados.

## 7) Documentación — 9/10 ✅
Evidencia: README completo con setup y despliegue; CHECKLIST_PRODUCCION.md; ARCHITECTURAL_ANALYSIS.md; EXECUTIVE_ROADMAP.md; reporte de estabilidad diario; Caddyfile documentado; ejemplos de curl.  
- Sugerencia: añadir sección de seguridad (CORS, headers, secretos) y guía de rotación de claves; playbook de incidentes.

## Métricas y Umbrales
- complexity>10: flag potencial en routers de negocio y manager WS si crece — sugerido ejecutar radon/ruff C901.  
- coverage>90%: actualmente el mínimo CI es 85%; objetivo propuesto: 90% en 30 días (excluir routers difíciles con pragmas).  
- CVSS>7: no detectado automáticamente; ejecutar pip-audit y Trivy como parte del script de auditoría.

## Hallazgos Priorizados (Severidad/Impacto/Esfuerzo)
1) CORS wildcard con credenciales (Sev: Alta, Impacto: Alto, Esfuerzo: Bajo) — ajustar allow_origins en prod y considerar desactivar allow_credentials.
2) ProxyHeaders y trusted_hosts "*" (Sev: Alta, Impacto: Medio, Esfuerzo: Bajo) — limitar a proxy interno; validar X-Forwarded-*.
3) WS sin auth real (Sev: Alta, Impacto: Alto, Esfuerzo: Medio) — validar JWT en handshake y exigirlo en prod.
4) Logging de URL con query (Sev: Media, Impacto: Medio, Esfuerzo: Bajo) — sanitizar parámetros sensibles.
5) Defaults de contraseñas en Compose (Sev: Media, Impacto: Alto, Esfuerzo: Bajo) — eliminar defaults y usar env_file de prod; ejemplos en docs.
6) Falta SCA/Container scan (Sev: Media, Impacto: Medio, Esfuerzo: Bajo) — pip-audit, safety, trivy, CodeQL.
7) Broadcast WS secuencial (Sev: Baja, Impacto: Medio, Esfuerzo: Bajo) — usar asyncio.gather con semáforo.

## Roadmap 0–90 días
- 0–3 días (Crítico):
  - CORS y Proxy hardening; sanitizar logs; exigir JWT en WS en prod; rotación de SECRET_KEY y DB password; actualizar .env.production.example.  
- 4–14 días (Alto):
  - Añadir pip-audit/safety + Trivy + CodeQL a CI; pruebas E2E WS; métricas WS básicas; subir coverage a 90%.
- 15–45 días (Medio):
  - Reducir exclusiones mypy; refactor menor ruff; adoptar radon para complejidad; documentación de seguridad y runbooks.  
- 46–90 días (Bajo):
  - Rate limiting y WAF; observabilidad (Prometheus/Grafana); pruebas de carga WS/REST; caos testing básico.

## Coste-Beneficio (alto nivel)
- Hardening CORS/Proxy/Logs: Bajo esfuerzo, alto beneficio (seguridad inmediata).  
- WS auth JWT: Medio esfuerzo, alto beneficio (control de acceso y auditoría).  
- SCA/Container scan: Bajo esfuerzo, medio/alto beneficio (riesgos de supply chain).  
- Métricas/coverage 90%: Medio esfuerzo, beneficio sostenido en mantenibilidad.

## Apéndices
- Evidencia clave (rutas):
  - `src/api/main.py` (CORS, ProxyHeaders, logs requests, /metrics)
  - `src/api/routers/websockets.py` (token por query, TODO JWT)
  - `config/settings.py` (ALLOWED_HOSTS ["*"], DB URL assembly)
  - `docker/docker-compose.yml` (defaults de POSTGRES_PASSWORD, DATABASE_URL)
  - `.github/workflows/ci.yml` (ruff/mypy/pytest, semgrep)
  - `src/core/websockets.py` (broadcast/heartbeat)

- Script reproducible: ver `scripts/audit.sh`.

---

Audit Complete - Health: 84/100
