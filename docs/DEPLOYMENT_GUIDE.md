# Guía de Despliegue – GRUPO_GAD

Esta guía describe cómo pasar a producción de forma reproducible y validar el sistema (incluyendo el endpoint de emergencias) con un seed mínimo.

## 1. Prerrequisitos

- Docker y Docker Compose instalados
- Dominio/puntos de entrada (Caddy/Nginx) con puertos 80/443
- Token del Bot de Telegram y `ADMIN_CHAT_ID`
- Acceso al repo y runners/host para desplegar

## 2. Preparar variables de entorno

Copiar el ejemplo y completar valores (NO versionar secretos):

```bash
cp docs/env/.env.production.example .env.production
# Edita .env.production con SECRET_KEY, DATABASE_URL, REDIS_PASSWORD, TELEGRAM_TOKEN, etc.
```

Recomendado: generar `SECRET_KEY` seguro (>=48 chars):

```bash
head -c 64 /dev/urandom | base64 | tr -d '\n' | cut -c1-64
```

## 3. Levantar servicios

Verificar sintaxis y subir:

```bash
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml up -d
```

## 4. Habilitar PostGIS y aplicar migraciones

Crear extensión (una sola vez) y migrar:

```bash
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Migraciones (si el contenedor API incluye alembic)
docker compose -f docker-compose.prod.yml exec -T api \
  alembic upgrade head
```

> **Alternativa local**: `poetry run alembic upgrade head` (con `DATABASE_URL` apuntando a la DB del compose).
> **Nota**: Si usas la estructura en `docker/`, el comando sería: `docker compose -f docker/docker-compose.prod.yml`

## 5. Semilla mínima de "efectivos"

Para probar proximidad en `/api/v1/tasks/emergency`, necesitas al menos 1–2 efectivos con `geom` (geography Point, SRID 4326):

```bash
bash scripts/seed_efectivos.sh   # Ejecuta el SQL vía stdin (funciona con imágenes sin volumes)
```

Alternativamente, ejecutar el SQL directamente:

```bash
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" << 'EOF'
UPDATE efectivos SET geom = ST_SetSRID(ST_MakePoint(-58.3816, -34.6037), 4326)::geography WHERE id = 1;
UPDATE efectivos SET geom = ST_SetSRID(ST_MakePoint(-99.1332, 19.4326), 4326)::geography WHERE id = 2;
EOF
```

> **Importante**: Ajusta los IDs (1, 2) a registros reales que existan en tu tabla "efectivos".

## 6. Pruebas de humo

API básica:

```bash
curl -fsS http://localhost:8000/api/v1/health
```

Emergencia (ejemplo):

```bash
curl -fsS -X POST "http://localhost:8000/api/v1/tasks/emergency" \
  -H "Content-Type: application/json" \
  -d '{"telegram_id":123,"lat":-34.6037,"lng":-58.3816}'
```

- Si no hay efectivos con `geom`: 404 esperado
- Con seed correcto: 200 y asignación más cercana

Bypass admin (requiere JWT de admin/superuser):

```bash
curl -fsS -X POST "http://localhost:8000/api/v1/admin/agent/command" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"command":"status"}'
```

## 7. Bot de Telegram

- Configurar `TELEGRAM_TOKEN` y `ADMIN_CHAT_ID` en `.env.production`
- Verificar que el bot puede alcanzar la API interna (hostname `api` o dominio)
- Probar `/start`, `/crear`, `/finalizar`

## 8. Proxy TLS (Caddy/Nginx)

- Apuntar el proxy a `127.0.0.1:8000` (API)
- Certificados ACME/Let's Encrypt operativos
- Endurecer headers (CSP, HSTS si aplica)

## 9. CI / Validaciones

Al abrir PRs contra `main`:

- `scripts/fast_gate_check.sh` (bloqueante P1)
- `scripts/validate_complete.sh` (no bloqueante)
- `pytest` best-effort

## 10. Troubleshooting

- DB no saludable: revisar logs de `db` y credenciales en `.env.production`
- Migraciones fallan: validar `DATABASE_URL`, extensión PostGIS creada, y permisos
- Emergencia 404: cargar/actualizar `geom` de efectivos
- Redis auth: verificar `REDIS_PASSWORD` y healthcheck con `-a ${REDIS_PASSWORD}`