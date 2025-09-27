#!/usr/bin/env bash
set -euo pipefail

# Complete Validation - Post-deployment health checks
echo "===> Validación completa: Health checks"

# Wait a bit for services to stabilize
echo "Esperando servicios..."
sleep 10

# Check service health
services=("db" "redis" "api" "bot")
for service in "${services[@]}"; do
    if docker compose -f docker-compose.prod.yml ps "$service" | grep -q "Up\|healthy"; then
        echo "✅ $service: OK"
    else
        echo "⚠️  $service: Posibles problemas (no bloqueante)"
    fi
done

# Try to check API health endpoint
if curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    echo "✅ API health endpoint: OK"
else
    echo "⚠️  API health endpoint: No responde (verificar manualmente)"
fi

echo "✅ Validación completa finalizada"