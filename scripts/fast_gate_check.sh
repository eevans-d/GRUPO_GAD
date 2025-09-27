#!/usr/bin/env bash
set -euo pipefail

# Fast Gate Check - Basic validations before deployment
echo "===> Fast Gate: Validaciones básicas"

# Check if required files exist
if [ ! -f ".env.production" ]; then
    echo "❌ ERROR: .env.production no encontrado"
    exit 1
fi

if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ ERROR: docker-compose.prod.yml no encontrado"
    exit 1
fi

# Check Docker is available
if ! docker --version >/dev/null 2>&1; then
    echo "❌ ERROR: Docker no disponible"
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "❌ ERROR: Docker Compose no disponible"
    exit 1
fi

# Basic compose file validation
if ! docker compose -f docker-compose.prod.yml config >/dev/null 2>&1; then
    echo "❌ ERROR: docker-compose.prod.yml inválido"
    exit 1
fi

echo "✅ Fast Gate: Validaciones básicas pasadas"