#!/usr/bin/env bash
set -Eeuo pipefail

# Despliegue idempotente de GRUPO_GAD (producción)
# Requisitos: Docker/Compose, .env.production completo en el host.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

# Cargar variables si existen
if [ -f .env.production ]; then
  set -a; source .env.production; set +a
fi

require() { var="$1"; if [ -z "${!var:-}" ]; then echo "Falta variable: $var"; exit 1; fi; }
require POSTGRES_USER
require POSTGRES_DB

echo "===> Fast Gate P1"
chmod +x scripts/fast_gate_check.sh scripts/validate_complete.sh || true
bash scripts/fast_gate_check.sh

echo "===> Validación de compose"
docker compose -f docker-compose.prod.yml config >/dev/null

echo "===> Levantando servicios"
docker compose -f docker-compose.prod.yml up -d

echo "===> Habilitar PostGIS"
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis;"

echo "===> Migraciones Alembic"
docker compose -f docker-compose.prod.yml exec -T api bash -lc 'alembic upgrade head || true'

echo "===> Validación completa (no bloqueante)"
bash scripts/validate_complete.sh || true

echo "===> Hecho. Ejecuta seed_efectivos.sh si necesitas datos de prueba."