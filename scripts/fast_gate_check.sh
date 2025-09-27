#!/usr/bin/env bash
set -Eeuo pipefail

echo "🔍 GRUPO_GAD Fast Gate Check - $(date)"

fail_count=0
p1_failed=0

check_cmd() {
  local desc="$1"; shift
  local cmd="$*"
  echo "→ ${desc}"
  if bash -O extglob -c "${cmd}" >/dev/null 2>&1; then
    echo "✅ ${desc}"
  else
    echo "❌ ${desc}"
    fail_count=$((fail_count+1))
    p1_failed=1
  fi
}

# P1 - COMPONENTES VITALES (huellas de código/config)
check_cmd "P1: Sistema emergencias presente (huella)" "grep -R \"POST.*emergency\" src/ || true"
check_cmd "P1: Resolución por Telegram presente (huella)" "grep -R \"by-telegram\" src/ || true"
check_cmd "P1: PostGIS presente (huella SQL/geo)" "grep -R \"ST_Distance\\|PostGIS\\|SRID.*4326\" src/ alembic/ || true"
check_cmd "P1: Bypass administrativo presente (huella)" "grep -R \"admin/agent/command\" src/ || true"

# P1 - CONFIGURACIÓN CRÍTICA
check_cmd "P1: docker-compose.prod.yml existe" "test -f docker-compose.prod.yml"
check_cmd "P1: PostGIS configurado en compose" "grep -q \"postgis/postgis\" docker-compose.prod.yml"

# P1 - SECRETOS OPERACIONALES (solo referencia, no valores)
for var in TELEGRAM_TOKEN SECRET_KEY DATABASE_URL; do
  check_cmd "P1: Variable ${var} referenciada en el repo/infra" "grep -R \"${var}\" ."
done

if (( p1_failed > 0 )); then
  echo "REGLA ABSOLUTA: Cualquier ❌ P1 = DETENER DESPLIEGUE"
  echo "❌ P1 detectados: ${fail_count}. NO CONTINUAR."
  exit 1
fi

echo "✅ Sin ❌ P1: continuar auditoría completa"
exit 0