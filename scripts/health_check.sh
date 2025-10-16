#!/bin/bash
# ========================================================================
# 🏥 GRUPO_GAD - System Health Check Script
# ========================================================================
# Descripción: Validación completa de salud del sistema
# Uso: ./scripts/health_check.sh [--production] [--verbose]
# ========================================================================

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
VERBOSE=false
ENVIRONMENT="development"
COMPOSE_FILE="docker-compose.yml"
FAILED_CHECKS=0
TOTAL_CHECKS=0

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            ENVIRONMENT="production"
            COMPOSE_FILE="docker-compose.prod.yml"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Uso: $0 [--production] [--verbose]"
            exit 1
            ;;
    esac
done

# Funciones de logging
log_check() {
    echo -e "${BLUE}[CHECK]${NC} $*"
    ((TOTAL_CHECKS++))
}

log_ok() {
    echo -e "${GREEN}[✅ OK]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[⚠️  WARN]${NC} $*"
}

log_fail() {
    echo -e "${RED}[❌ FAIL]${NC} $*"
    ((FAILED_CHECKS++))
}

log_info() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[INFO]${NC} $*"
    fi
}

# ========================================================================
# CHECKS
# ========================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           🏥 GRUPO_GAD - HEALTH CHECK                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Environment: ${ENVIRONMENT}"
echo "Compose file: ${COMPOSE_FILE}"
echo ""

# ========================================================================
# 1. Docker Services
# ========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  DOCKER SERVICES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check 1.1: DB Container
log_check "PostgreSQL container running"
if docker compose -f "$COMPOSE_FILE" ps db 2>/dev/null | grep -q "running\|healthy"; then
    log_ok "PostgreSQL container is running"
else
    log_fail "PostgreSQL container is not running"
fi

# Check 1.2: Redis Container
log_check "Redis container running"
if docker compose -f "$COMPOSE_FILE" ps redis 2>/dev/null | grep -q "running\|healthy"; then
    log_ok "Redis container is running"
else
    log_fail "Redis container is not running"
fi

# Check 1.3: API Container
log_check "API container running"
if docker compose -f "$COMPOSE_FILE" ps api 2>/dev/null | grep -q "running\|healthy"; then
    log_ok "API container is running"
else
    log_fail "API container is not running"
fi

# Check 1.4: Caddy Container (solo en production)
if [ "$ENVIRONMENT" = "production" ]; then
    log_check "Caddy container running"
    if docker compose -f "$COMPOSE_FILE" ps caddy 2>/dev/null | grep -q "running"; then
        log_ok "Caddy container is running"
    else
        log_fail "Caddy container is not running"
    fi
fi

echo ""

# ========================================================================
# 2. API Health
# ========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  API HEALTH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check 2.1: Health Endpoint
log_check "API health endpoint"
API_URL="http://localhost:8000"
if [ "$ENVIRONMENT" = "production" ]; then
    API_URL="http://localhost:8000"  # Via Caddy internamente
fi

HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/api/v1/health" 2>/dev/null || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    HEALTH_JSON=$(curl -s "${API_URL}/api/v1/health" 2>/dev/null)
    log_ok "API health endpoint responding (HTTP 200)"
    log_info "Response: ${HEALTH_JSON}"
else
    log_fail "API health endpoint not responding (HTTP ${HEALTH_RESPONSE})"
fi

# Check 2.2: Metrics Endpoint
log_check "Metrics endpoint"
METRICS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/metrics" 2>/dev/null || echo "000")
if [ "$METRICS_RESPONSE" = "200" ]; then
    log_ok "Metrics endpoint responding (HTTP 200)"
    if [ "$VERBOSE" = true ]; then
        METRICS_COUNT=$(curl -s "${API_URL}/metrics" 2>/dev/null | grep -c "^#" || echo "0")
        log_info "Metrics exported: ${METRICS_COUNT} metric families"
    fi
else
    log_fail "Metrics endpoint not responding (HTTP ${METRICS_RESPONSE})"
fi

# Check 2.3: API Response Time
log_check "API response time"
START_TIME=$(date +%s%N)
curl -s "${API_URL}/api/v1/health" > /dev/null 2>&1
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))  # Convert to ms

if [ "$RESPONSE_TIME" -lt 200 ]; then
    log_ok "API response time: ${RESPONSE_TIME}ms (excellent)"
elif [ "$RESPONSE_TIME" -lt 500 ]; then
    log_ok "API response time: ${RESPONSE_TIME}ms (good)"
elif [ "$RESPONSE_TIME" -lt 2000 ]; then
    log_warn "API response time: ${RESPONSE_TIME}ms (slow)"
else
    log_fail "API response time: ${RESPONSE_TIME}ms (critical)"
fi

echo ""

# ========================================================================
# 3. Database Health
# ========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  DATABASE HEALTH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check 3.1: PostgreSQL Connectivity
log_check "PostgreSQL connectivity"
if docker compose -f "$COMPOSE_FILE" exec -T db pg_isready -q 2>/dev/null; then
    log_ok "PostgreSQL accepting connections"
else
    log_fail "PostgreSQL not accepting connections"
fi

# Check 3.2: Database Exists
log_check "Database exists"
DB_EXISTS=$(docker compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -lqt 2>/dev/null | grep -c "grupogad" || echo "0")
if [ "$DB_EXISTS" -gt 0 ]; then
    log_ok "Database 'grupogad*' exists"
else
    log_fail "Database 'grupogad*' not found"
fi

# Check 3.3: Active Connections
log_check "Database connections"
ACTIVE_CONNECTIONS=$(docker compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -tAc \
    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null || echo "0")

if [ "$ACTIVE_CONNECTIONS" -lt 50 ]; then
    log_ok "Active connections: ${ACTIVE_CONNECTIONS} (healthy)"
    log_info "Threshold: <50 OK, <80 WARNING, ≥80 CRITICAL"
elif [ "$ACTIVE_CONNECTIONS" -lt 80 ]; then
    log_warn "Active connections: ${ACTIVE_CONNECTIONS} (high)"
else
    log_fail "Active connections: ${ACTIVE_CONNECTIONS} (critical)"
fi

# Check 3.4: Database Size
log_check "Database size"
if docker compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -tAc \
    "SELECT pg_size_pretty(pg_database_size('grupogad_dev'));" 2>/dev/null; then
    DB_SIZE=$(docker compose -f "$COMPOSE_FILE" exec -T db psql -U postgres -tAc \
        "SELECT pg_size_pretty(pg_database_size('grupogad_dev'));" 2>/dev/null | tr -d '[:space:]')
    log_ok "Database size: ${DB_SIZE}"
fi

echo ""

# ========================================================================
# 4. Redis Health
# ========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  REDIS HEALTH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check 4.1: Redis Connectivity
log_check "Redis connectivity"
if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    log_ok "Redis responding to PING"
else
    log_fail "Redis not responding"
fi

# Check 4.2: Redis Memory Usage
log_check "Redis memory usage"
REDIS_MEMORY=$(docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli INFO memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r' || echo "N/A")
if [ "$REDIS_MEMORY" != "N/A" ]; then
    log_ok "Redis memory usage: ${REDIS_MEMORY}"
fi

# Check 4.3: Redis Keys Count
log_check "Redis keys count"
REDIS_KEYS=$(docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli DBSIZE 2>/dev/null | tr -d '\r' || echo "0")
log_ok "Redis keys: ${REDIS_KEYS}"

echo ""

# ========================================================================
# 5. WebSocket Health (si aplica)
# ========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  WEBSOCKET HEALTH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check 5.1: WebSocket Stats Endpoint
log_check "WebSocket stats endpoint"
WS_STATS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/ws/stats" 2>/dev/null || echo "000")
if [ "$WS_STATS_RESPONSE" = "200" ]; then
    log_ok "WebSocket stats endpoint responding"
    if [ "$VERBOSE" = true ]; then
        WS_STATS=$(curl -s "${API_URL}/ws/stats" 2>/dev/null)
        log_info "Stats: ${WS_STATS}"
    fi
else
    log_warn "WebSocket stats endpoint not responding (may be disabled)"
fi

echo ""

# ========================================================================
# 6. Monitoring Health (si está activo)
# ========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  MONITORING HEALTH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check 6.1: Prometheus
log_check "Prometheus"
if docker compose -f docker-compose.monitoring.yml ps prometheus 2>/dev/null | grep -q "running\|healthy"; then
    PROM_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:9090/-/healthy" 2>/dev/null || echo "000")
    if [ "$PROM_RESPONSE" = "200" ]; then
        log_ok "Prometheus is healthy"
    else
        log_warn "Prometheus container running but not healthy"
    fi
else
    log_warn "Prometheus not running (monitoring disabled)"
fi

# Check 6.2: Grafana
log_check "Grafana"
if docker compose -f docker-compose.monitoring.yml ps grafana 2>/dev/null | grep -q "running\|healthy"; then
    GRAFANA_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/api/health" 2>/dev/null || echo "000")
    if [ "$GRAFANA_RESPONSE" = "200" ]; then
        log_ok "Grafana is healthy"
    else
        log_warn "Grafana container running but not healthy"
    fi
else
    log_warn "Grafana not running (monitoring disabled)"
fi

# Check 6.3: AlertManager
log_check "AlertManager"
if docker compose -f docker-compose.monitoring.yml ps alertmanager 2>/dev/null | grep -q "running\|healthy"; then
    ALERT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:9093/-/healthy" 2>/dev/null || echo "000")
    if [ "$ALERT_RESPONSE" = "200" ]; then
        log_ok "AlertManager is healthy"
        
        # Check for active alerts
        if [ "$VERBOSE" = true ]; then
            ACTIVE_ALERTS=$(curl -s "http://localhost:9093/api/v2/alerts" 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
            if [ "$ACTIVE_ALERTS" -eq 0 ]; then
                log_info "No active alerts"
            else
                log_warn "${ACTIVE_ALERTS} active alerts"
            fi
        fi
    else
        log_warn "AlertManager container running but not healthy"
    fi
else
    log_warn "AlertManager not running (monitoring disabled)"
fi

echo ""

# ========================================================================
# 7. Resource Usage
# ========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  RESOURCE USAGE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check 7.1: Disk Space
log_check "Disk space"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    log_ok "Disk usage: ${DISK_USAGE}% (healthy)"
elif [ "$DISK_USAGE" -lt 90 ]; then
    log_warn "Disk usage: ${DISK_USAGE}% (high)"
else
    log_fail "Disk usage: ${DISK_USAGE}% (critical)"
fi

# Check 7.2: Memory Usage
log_check "Memory usage"
MEMORY_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
if [ "$MEMORY_USAGE" -lt 80 ]; then
    log_ok "Memory usage: ${MEMORY_USAGE}% (healthy)"
elif [ "$MEMORY_USAGE" -lt 90 ]; then
    log_warn "Memory usage: ${MEMORY_USAGE}% (high)"
else
    log_fail "Memory usage: ${MEMORY_USAGE}% (critical)"
fi

# Check 7.3: CPU Usage (5-second average)
log_check "CPU usage"
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d% -f1)
CPU_USAGE_INT=$(printf "%.0f" "$CPU_USAGE")
if [ "$CPU_USAGE_INT" -lt 70 ]; then
    log_ok "CPU usage: ${CPU_USAGE}% (healthy)"
elif [ "$CPU_USAGE_INT" -lt 90 ]; then
    log_warn "CPU usage: ${CPU_USAGE}% (high)"
else
    log_fail "CPU usage: ${CPU_USAGE}% (critical)"
fi

echo ""

# ========================================================================
# SUMMARY
# ========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PASSED_CHECKS=$((TOTAL_CHECKS - FAILED_CHECKS))
SUCCESS_RATE=$(( PASSED_CHECKS * 100 / TOTAL_CHECKS ))

echo "Total checks: ${TOTAL_CHECKS}"
echo "Passed: ${PASSED_CHECKS}"
echo "Failed: ${FAILED_CHECKS}"
echo "Success rate: ${SUCCESS_RATE}%"
echo ""

if [ "$FAILED_CHECKS" -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED - SYSTEM HEALTHY${NC}"
    echo ""
    exit 0
elif [ "$FAILED_CHECKS" -lt 3 ]; then
    echo -e "${YELLOW}⚠️  SOME CHECKS FAILED - SYSTEM DEGRADED${NC}"
    echo ""
    exit 1
else
    echo -e "${RED}❌ MULTIPLE CHECKS FAILED - SYSTEM UNHEALTHY${NC}"
    echo ""
    exit 2
fi
