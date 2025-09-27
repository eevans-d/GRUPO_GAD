# Checklist GO/NO-GO – GRUPO_GAD

Marcar cada ítem antes del despliegue a producción.

## 1. Código y PRs
- [ ] PR #1 (Seguridad/Infra) fusionado
- [ ] PR #1 Complemento (Redis + CI) fusionado  
- [ ] PR #2 (Funcionalidades críticas) fusionado
- [ ] PR Docs & Seed fusionado

## 2. Entorno y secretos
- [ ] `.env.production` creado en el servidor con valores reales (no versionado)
- [ ] `SECRET_KEY` generado (≥48 chars)
- [ ] `DATABASE_URL` apunta a Postgres con PostGIS
- [ ] `REDIS_PASSWORD` definido y coincide con compose
- [ ] `TELEGRAM_TOKEN` y `ADMIN_CHAT_ID` definidos

## 3. Infraestructura (Docker)
- [ ] `docker compose -f docker-compose.prod.yml config` sin errores
- [ ] `docker compose up -d` levanta db/redis/api/bot/caddy
- [ ] Healthchecks verdes para db/redis/api/bot

## 4. Base de datos
- [ ] `CREATE EXTENSION IF NOT EXISTS postgis;` ejecutado
- [ ] `alembic upgrade head` ejecutado sin errores
- [ ] Al menos 1–2 efectivos con `geom geography(Point,4326)` cargados (seed)

## 5. Validaciones funcionales
- [ ] `GET /api/v1/health` devuelve 200
- [ ] `POST /api/v1/tasks/emergency` → 200 con asignación (o 404 si aún sin efectivos)
- [ ] `POST /api/v1/admin/agent/command` → 403 (no admin), 202 (admin)
- [ ] Bot Telegram responde `/start` y comandos básicos, y puede alcanzar la API

## 6. Proxy y TLS
- [ ] Caddy/Nginx proxea a `127.0.0.1:8000`
- [ ] Certificados válidos (Let's Encrypt u otros)
- [ ] Headers de seguridad (HSTS, X-Frame-Options, X-Content-Type-Options, CSP básica)

## 7. Observabilidad y backups
- [ ] `/metrics` accesible y monitoreado
- [ ] Backups de Postgres programados (pg_dump) y restauración probada

## 8. CI (recomendado)
- [ ] Workflow `Validate` corre en PRs: fast gate + validate_complete + pytest (best-effort)

## 9. Decisión final
- [ ] Riesgos conocidos documentados
- [ ] Ventana de despliegue y plan de reversa definidos
- [ ] GO aprobado por el responsable