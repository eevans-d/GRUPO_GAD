#!/usr/bin/env bash
set -euo pipefail

# Auditoría reproducible para GRUPO_GAD
# Requisitos: bash, python3, pipx o pip, docker (opcional)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

echo "===> 1) Entorno Python / Dependencias"
if command -v poetry >/dev/null 2>&1; then
  echo "Usando Poetry"
  poetry install --with dev -q
  PFX="poetry run"
else
  echo "Poetry no instalado; usando pip"
  python3 -m pip install -U pip -q
  python3 -m pip install -r requirements.lock -q || true
  python3 -m pip install ruff mypy pytest pytest-cov pip-audit safety -q
  PFX="python3 -m"
fi

echo "===> 2) Lint / Type / Tests con cobertura"
$PFX ruff check . || true
$PFX mypy || true
DATABASE_URL="sqlite+aiosqlite:///:memory:" $PFX pytest --disable-warnings -q --cov=src --cov-report=term-missing || true

echo "===> 3) SCA: pip-audit y safety"
$PFX pip_audit -r requirements.lock || true
$PFX safety check -r requirements.lock --full-report || true

echo "===> 4) Container scan (opcional con Trivy)"
if command -v trivy >/dev/null 2>&1; then
  echo "Escaneando imagen local api si existe..."
  trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 0 ghcr.io/eevans-d/grupo_gad/api:latest || true
else
  echo "Trivy no instalado (opcional)"
fi

echo "===> 5) Resumen"
echo "Revisa docs/audit/AUDIT_REPORT_*.md y docs/audit/metadata_*.json"
