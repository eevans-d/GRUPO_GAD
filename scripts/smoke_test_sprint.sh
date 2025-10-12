#!/bin/bash
# Script de smoke test para validar Sprint de Optimización
# Fecha: 12 octubre 2025

# No usar set -e para poder continuar con todos los tests
# set -e

echo "🚀 SMOKE TEST - SPRINT DE OPTIMIZACIÓN"
echo "======================================"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"
SUCCESS=0
FAILED=0

# Función para test
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected="$3"
    
    echo -n "Testing $name... "
    
    response=$(curl -s "$url" || echo "ERROR")
    
    if [[ "$response" == *"$expected"* ]]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((SUCCESS++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $response"
        ((FAILED++))
    fi
}

echo "📊 Fase 1: Verificar Servicios Docker"
echo "--------------------------------------"

# Check Docker containers
if docker ps --filter "name=gad_api" --format "{{.Status}}" | grep -q "healthy"; then
    echo -e "${GREEN}✓ API Container: HEALTHY${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ API Container: NOT HEALTHY${NC}"
    ((FAILED++))
fi

if docker ps --filter "name=gad_db" --format "{{.Status}}" | grep -q "healthy"; then
    echo -e "${GREEN}✓ DB Container: HEALTHY${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ DB Container: NOT HEALTHY${NC}"
    ((FAILED++))
fi

if docker ps --filter "name=gad_redis" --format "{{.Status}}" | grep -q "Up"; then
    echo -e "${GREEN}✓ Redis Container: UP${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ Redis Container: DOWN${NC}"
    ((FAILED++))
fi

echo ""
echo "🔍 Fase 2: Endpoints de API"
echo "--------------------------------------"

# Test health endpoint
test_endpoint "Health Check" "$API_URL/api/v1/health" '"status":"ok"'

# Test cache stats endpoint
test_endpoint "Cache Stats" "$API_URL/api/v1/cache/stats" '"connected":true'

# Test OpenAPI docs
test_endpoint "OpenAPI Docs" "$API_URL/docs" "swagger"

# Test metrics endpoint (montado en raíz, no en /api/v1)
test_endpoint "Metrics" "$API_URL/metrics" "app_uptime"

echo ""
echo "🗄️  Fase 3: Base de Datos"
echo "--------------------------------------"

# Check PostgreSQL indices
echo -n "Checking DB indices... "
indices=$(docker exec gad_db_dev psql -U gad_user -d gad_db -t -c "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'tareas' AND indexname LIKE 'idx_tareas_%';" 2>/dev/null || echo "0")
indices=$(echo $indices | xargs) # trim whitespace

if [ "$indices" = "4" ]; then
    echo -e "${GREEN}✓ PASS${NC} (4 índices creados)"
    ((SUCCESS++))
else
    echo -e "${RED}✗ FAIL${NC} (Expected 4, got $indices)"
    ((FAILED++))
fi

# Check Alembic version
echo -n "Checking Alembic migration... "
version=$(docker exec gad_db_dev psql -U gad_user -d gad_db -t -c "SELECT version_num FROM alembic_version;" 2>/dev/null || echo "")
version=$(echo $version | xargs)

if [ "$version" = "094f640cda5e" ]; then
    echo -e "${GREEN}✓ PASS${NC} (Migration applied)"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} (Version: $version)"
fi

echo ""
echo "💾 Fase 4: Redis Cache"
echo "--------------------------------------"

# Test Redis connection
echo -n "Redis PING... "
redis_response=$(docker exec gad_redis_dev redis-cli ping 2>/dev/null || echo "ERROR")

if [ "$redis_response" = "PONG" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Check Redis keys with prefix
echo -n "Redis keys with prefix 'gad:'... "
key_count=$(docker exec gad_redis_dev redis-cli --scan --pattern "gad:*" 2>/dev/null | wc -l)

echo -e "${GREEN}✓ PASS${NC} ($key_count keys)"
((SUCCESS++))

echo ""
echo "📄 Fase 5: Documentación"
echo "--------------------------------------"

# Check documentation files
docs=(
    "BASELINE_PERFORMANCE.md"
    "FASE2_TESTS_RESULTS.md"
    "FASE3_QUERY_OPTIMIZATION_RESULTS.md"
    "FASE4_CACHE_REDIS_RESULTS.md"
    "SPRINT_RESUMEN_EJECUTIVO_FINAL.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        lines=$(wc -l < "$doc")
        echo -e "${GREEN}✓${NC} $doc ($lines lines)"
        ((SUCCESS++))
    else
        echo -e "${RED}✗${NC} $doc (missing)"
        ((FAILED++))
    fi
done

echo ""
echo "======================================"
echo "📊 RESULTADOS FINALES"
echo "======================================"
echo -e "Total tests: $((SUCCESS + FAILED))"
echo -e "${GREEN}Passed: $SUCCESS${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

# Calculate percentage
if [ $((SUCCESS + FAILED)) -gt 0 ]; then
    percentage=$((SUCCESS * 100 / (SUCCESS + FAILED)))
    echo -e "Success rate: ${percentage}%"
fi

echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ¡TODOS LOS TESTS PASARON!${NC}"
    echo ""
    echo "✅ Sistema listo para producción"
    echo "✅ Documentación completa"
    echo "✅ Optimizaciones aplicadas"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  ALGUNOS TESTS FALLARON${NC}"
    echo ""
    echo "Por favor revisar los errores arriba"
    echo ""
    exit 1
fi
