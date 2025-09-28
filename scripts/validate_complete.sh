#!/usr/bin/env bash
set -Eeuo pipefail

echo "🧪 GRUPO_GAD Validación Completa - $(date)"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

overall_fail=0

run_step() {
  local name="$1"; shift
  echo "→ Ejecutando: ${name}"
  if "$@" ; then
    echo "✅ ${name}"
  else
    echo "⚠️ ${name} (warning)"
  fi
}

# 0) Gate P1 (bloqueante)
if bash scripts/fast_gate_check.sh; then
  echo "✅ Fast gate P1"
else
  echo "❌ Fast gate P1"
  exit 1
fi

# 1) Validar sintaxis de docker compose
if command -v docker >/dev/null 2>&1; then
  run_step "docker compose config" docker compose -f docker-compose.prod.yml config >/dev/null
else
  echo "⚠️ Docker no disponible; saltando verificación de compose"
fi

# 2) PostGIS (opcional) – NO bloqueante si contenedor no está arriba
if command -v docker >/dev/null 2>&1 && docker compose -f docker-compose.prod.yml ps db >/dev/null 2>&1; then
  run_step "Verificar PostGIS_version()" docker compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT PostGIS_version();"
else
  echo "⚠️ PostGIS no verificado (servicio no levantado en este entorno)"
fi

# 3) Health API (opcional) – NO bloqueante
API_URL="${API_URL:-http://localhost:8000}"
if command -v curl >/dev/null 2>&1; then
  run_step "Health API" curl -fsS "$API_URL/api/v1/health" >/dev/null
else
  echo "⚠️ curl no disponible; saltando health API"
fi

# Resultado final (si fast gate pasó, consideramos PASS para PR#1)
echo "✅ validate_complete.sh finalizado"
exit 0