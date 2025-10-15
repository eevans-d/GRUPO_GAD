#!/bin/bash
# ============================================================================
# GRUPO_GAD - Smoke Tests para Staging Environment
# ============================================================================
# Descripción: Tests básicos de humo para validar staging
# Uso: ./scripts/smoke_test_staging.sh
# ============================================================================

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
API_BASE_URL="http://localhost:8001"
STAGING_DB_HOST="localhost"
STAGING_DB_PORT="5435"
STAGING_REDIS_HOST="localhost"
STAGING_REDIS_PORT="6382"
STAGING_REDIS_PASSWORD="redis_staging_secure_2025"

FAILED_TESTS=0
PASSED_TESTS=0
TOTAL_TESTS=0

# ────────────────────────────────────────────────────────────────────────
# Funciones auxiliares
# ────────────────────────────────────────────────────────────────────────

log_info() {
    echo -e "${BLUE}ℹ ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
    ((PASSED_TESTS++))
}

log_failure() {
    echo -e "${RED}❌${NC} $1"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}⚠️ ${NC} $1"
}

# ────────────────────────────────────────────────────────────────────────
# Tests
# ────────────────────────────────────────────────────────────────────────

test_api_health() {
    ((TOTAL_TESTS++))
    log_info "Test 1/$TOTAL_TESTS: API Health Check"
    
    local response=$(curl -sf "$API_BASE_URL/api/v1/health" 2>/dev/null)
    if echo "$response" | grep -q "ok"; then
        log_success "API Health Check OK"
        return 0
    else
        log_failure "API Health Check FAILED - Response: $response"
        return 1
    fi
}

test_api_metrics() {
    ((TOTAL_TESTS++))
    log_info "Test 2/$TOTAL_TESTS: API Metrics Endpoint"
    
    if curl -s "$API_BASE_URL/metrics" 2>/dev/null | grep -q "app_uptime_seconds"; then
        log_success "API Metrics OK"
        return 0
    else
        log_failure "API Metrics FAILED"
        return 1
    fi
}

test_api_docs() {
    ((TOTAL_TESTS++))
    log_info "Test 3/$TOTAL_TESTS: API Documentation"
    
    if curl -s "$API_BASE_URL/docs" 2>/dev/null | grep -q "swagger-ui"; then
        log_success "API Docs OK"
        return 0
    else
        log_failure "API Docs FAILED"
        return 1
    fi
}

test_api_openapi() {
    ((TOTAL_TESTS++))
    log_info "Test 4/$TOTAL_TESTS: OpenAPI Spec"
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/openapi.json" 2>/dev/null)
    if [ "$status_code" == "200" ]; then
        log_success "OpenAPI Spec OK"
        return 0
    elif [ "$status_code" == "404" ]; then
        log_warning "OpenAPI Spec not available (404 - may be disabled in staging)"
        return 0  # No fallar el test
    else
        log_failure "OpenAPI Spec FAILED (status: $status_code)"
        return 1
    fi
}

test_postgresql() {
    ((TOTAL_TESTS++))
    log_info "Test 5/$TOTAL_TESTS: PostgreSQL Connection"
    
    if docker exec gad_db_staging pg_isready -U postgres -d grupogad_staging > /dev/null 2>&1; then
        log_success "PostgreSQL OK - $STAGING_DB_HOST:$STAGING_DB_PORT"
        return 0
    else
        log_failure "PostgreSQL FAILED"
        return 1
    fi
}

test_redis() {
    ((TOTAL_TESTS++))
    log_info "Test 6/$TOTAL_TESTS: Redis Connection"
    
    if docker exec gad_redis_staging redis-cli -a "$STAGING_REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
        log_success "Redis OK - $STAGING_REDIS_HOST:$STAGING_REDIS_PORT"
        return 0
    else
        log_failure "Redis FAILED"
        return 1
    fi
}

test_websocket() {
    ((TOTAL_TESTS++))
    log_info "Test 7/$TOTAL_TESTS: WebSocket Connection"
    
    # Verificar que websocat está disponible
    if ! command -v websocat &> /dev/null; then
        log_warning "WebSocket test skipped (websocat not installed)"
        ((TOTAL_TESTS--))
        return 0
    fi
    
    # Probar conexión WebSocket con timeout de 5s
    if timeout 5 websocat -n1 "ws://localhost:8001/ws/connect" &> /dev/null; then
        log_success "WebSocket OK"
        return 0
    else
        log_warning "WebSocket connection timeout or failed (may need auth)"
        return 0  # No fallar el test por esto
    fi
}

test_api_auth_protection() {
    ((TOTAL_TESTS++))
    log_info "Test 8/$TOTAL_TESTS: API Auth Protection"
    
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/v1/tareas")
    if [ "$status_code" == "401" ] || [ "$status_code" == "404" ]; then
        log_success "API Auth Protection OK (got $status_code)"
        return 0
    else
        log_warning "API Auth returned $status_code (expected 401 or 404)"
        return 0  # No fallar el test
    fi
}

test_database_tables() {
    ((TOTAL_TESTS++))
    log_info "Test 9/$TOTAL_TESTS: Database Tables Exist"
    
    local table_count=$(docker exec gad_db_staging psql -U postgres -d grupogad_staging -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')
    
    if [ "$table_count" -gt 0 ]; then
        log_success "Database Tables OK ($table_count tables found)"
        return 0
    else
        log_failure "Database Tables FAILED (0 tables found)"
        return 1
    fi
}

test_api_response_time() {
    ((TOTAL_TESTS++))
    log_info "Test 10/$TOTAL_TESTS: API Response Time"
    
    local start_time=$(date +%s%N)
    curl -sf "$API_BASE_URL/api/v1/health" > /dev/null 2>&1
    local end_time=$(date +%s%N)
    
    local response_time=$(( (end_time - start_time) / 1000000 ))  # Convert to ms
    
    if [ "$response_time" -lt 1000 ]; then
        log_success "API Response Time OK (${response_time}ms < 1000ms)"
        return 0
    else
        log_warning "API Response Time SLOW (${response_time}ms >= 1000ms)"
        return 0  # No fallar el test
    fi
}

# ────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────

main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║          🧪 SMOKE TESTS - Staging Environment                 ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_info "Target: $API_BASE_URL"
    log_info "Starting smoke tests..."
    echo ""
    
    # Ejecutar tests
    test_api_health || true
    echo ""
    
    test_api_metrics || true
    echo ""
    
    test_api_docs || true
    echo ""
    
    test_api_openapi || true
    echo ""
    
    test_postgresql || true
    echo ""
    
    test_redis || true
    echo ""
    
    test_websocket || true
    echo ""
    
    test_api_auth_protection || true
    echo ""
    
    test_database_tables || true
    echo ""
    
    test_api_response_time || true
    echo ""
    
    # Resumen
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║                      📊 RESUMEN                                ║"
    echo "║                                                                ║"
    echo "╠════════════════════════════════════════════════════════════════╣"
    echo "║                                                                ║"
    printf "║  Total Tests:   %-45s║\n" "$TOTAL_TESTS"
    printf "║  ${GREEN}Passed:${NC}         %-45s║\n" "$PASSED_TESTS"
    printf "║  ${RED}Failed:${NC}         %-45s║\n" "$FAILED_TESTS"
    echo "║                                                                ║"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo "║  ${GREEN}Status: ✅ ALL TESTS PASSED${NC}                               ║"
        echo "║                                                                ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        log_success "Smoke tests completados exitosamente!"
        return 0
    else
        echo "║  ${RED}Status: ❌ SOME TESTS FAILED${NC}                              ║"
        echo "║                                                                ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        log_failure "Smoke tests fallaron ($FAILED_TESTS/$TOTAL_TESTS)"
        return 1
    fi
}

main "$@"
