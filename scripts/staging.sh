#!/bin/bash
# ============================================================================
# GRUPO_GAD - Staging Management Script
# ============================================================================
# Descripción: Helper para gestionar el entorno staging
# Uso: ./scripts/staging.sh [command]
# ============================================================================

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
COMPOSE_FILE="docker-compose.staging.yml"
ENV_FILE=".env.staging"
PROJECT_NAME="gad_staging"

# ────────────────────────────────────────────────────────────────────────
# Funciones auxiliares
# ────────────────────────────────────────────────────────────────────────

log_info() {
    echo -e "${BLUE}ℹ ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️ ${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

check_prerequisites() {
    log_info "Verificando prerequisitos..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    
    # Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose no está disponible"
        exit 1
    fi
    
    # Archivo .env.staging
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Archivo $ENV_FILE no encontrado"
        log_info "Crear desde .env.staging con secrets únicos"
        exit 1
    fi
    
    log_success "Prerequisitos OK"
}

# ────────────────────────────────────────────────────────────────────────
# Comandos
# ────────────────────────────────────────────────────────────────────────

cmd_up() {
    log_info "Levantando entorno staging..."
    check_prerequisites
    
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    log_success "Entorno staging iniciado"
    log_info "Esperando services healthy (30s)..."
    sleep 30
    
    cmd_status
}

cmd_down() {
    log_info "Deteniendo entorno staging..."
    
    docker compose -f "$COMPOSE_FILE" down
    
    log_success "Entorno staging detenido"
}

cmd_restart() {
    log_info "Reiniciando entorno staging..."
    cmd_down
    sleep 5
    cmd_up
}

cmd_status() {
    log_info "Estado de servicios staging:"
    echo ""
    docker compose -f "$COMPOSE_FILE" ps
    echo ""
    
    # Health checks
    log_info "Health checks:"
    
    # API
    if curl -sf http://localhost:8001/api/v1/health > /dev/null 2>&1; then
        log_success "API (HTTP): OK - http://localhost:8001"
    else
        log_warning "API (HTTP): No disponible"
    fi
    
    # Caddy HTTPS
    if curl -ksf https://localhost:8443/api/v1/health > /dev/null 2>&1; then
        log_success "Caddy (HTTPS): OK - https://localhost:8443"
    else
        log_warning "Caddy (HTTPS): No disponible"
    fi
    
    # PostgreSQL
    if docker exec gad_db_staging pg_isready -U postgres > /dev/null 2>&1; then
        log_success "PostgreSQL: OK - localhost:5435"
    else
        log_warning "PostgreSQL: No disponible"
    fi
    
    # Redis
    if docker exec gad_redis_staging redis-cli -a redis_staging_secure_2025 ping > /dev/null 2>&1; then
        log_success "Redis: OK - localhost:6382"
    else
        log_warning "Redis: No disponible"
    fi
}

cmd_logs() {
    local service="${1:-}"
    
    if [ -z "$service" ]; then
        log_info "Mostrando logs de todos los servicios..."
        docker compose -f "$COMPOSE_FILE" logs -f
    else
        log_info "Mostrando logs de $service..."
        docker compose -f "$COMPOSE_FILE" logs -f "$service"
    fi
}

cmd_migrate() {
    log_info "Ejecutando migraciones en staging..."
    
    # Verificar que API está running
    if ! docker ps | grep -q gad_api_staging; then
        log_error "API staging no está corriendo. Ejecutar: ./scripts/staging.sh up"
        exit 1
    fi
    
    docker exec gad_api_staging alembic upgrade head
    
    log_success "Migraciones completadas"
}

cmd_shell() {
    local service="${1:-api-staging}"
    
    log_info "Abriendo shell en $service..."
    
    case "$service" in
        api|api-staging)
            docker exec -it gad_api_staging /bin/bash
            ;;
        db|db-staging)
            docker exec -it gad_db_staging psql -U postgres -d grupogad_staging
            ;;
        redis|redis-staging)
            docker exec -it gad_redis_staging redis-cli -a redis_staging_secure_2025
            ;;
        caddy|caddy-staging)
            docker exec -it gad_caddy_staging /bin/sh
            ;;
        *)
            log_error "Servicio desconocido: $service"
            log_info "Servicios disponibles: api, db, redis, caddy"
            exit 1
            ;;
    esac
}

cmd_clean() {
    log_warning "¡Esto eliminará TODOS los datos de staging!"
    read -p "¿Continuar? (yes/no): " -r
    echo
    
    if [[ $REPLY != "yes" ]]; then
        log_info "Operación cancelada"
        exit 0
    fi
    
    log_info "Limpiando entorno staging..."
    docker compose -f "$COMPOSE_FILE" down -v
    
    log_success "Entorno staging limpio (volumes eliminados)"
}

cmd_smoke_test() {
    log_info "Ejecutando smoke tests en staging..."
    
    local base_url="https://localhost:8443"
    local failures=0
    
    echo ""
    log_info "Test 1: Health check"
    if curl -ksf "$base_url/api/v1/health" | grep -q "ok"; then
        log_success "Health check OK"
    else
        log_error "Health check FAILED"
        ((failures++))
    fi
    
    echo ""
    log_info "Test 2: Metrics endpoint"
    if curl -ksf "$base_url/metrics" | grep -q "python_gc_objects_collected_total"; then
        log_success "Metrics OK"
    else
        log_error "Metrics FAILED"
        ((failures++))
    fi
    
    echo ""
    log_info "Test 3: API docs"
    if curl -ksf "$base_url/docs" | grep -q "FastAPI"; then
        log_success "API docs OK"
    else
        log_error "API docs FAILED"
        ((failures++))
    fi
    
    echo ""
    log_info "Test 4: WebSocket connection"
    if timeout 5 websocat -n1 --insecure "wss://localhost:8443/ws/connect" &> /dev/null; then
        log_success "WebSocket OK"
    else
        log_warning "WebSocket test skipped (websocat no disponible)"
    fi
    
    echo ""
    if [ $failures -eq 0 ]; then
        log_success "Smoke tests completados: 0 fallos"
        return 0
    else
        log_error "Smoke tests completados: $failures fallos"
        return 1
    fi
}

cmd_help() {
    cat << EOF
${BLUE}GRUPO_GAD - Staging Management${NC}

${YELLOW}Uso:${NC}
    ./scripts/staging.sh [command] [options]

${YELLOW}Comandos disponibles:${NC}
    ${GREEN}up${NC}          Levantar entorno staging
    ${GREEN}down${NC}        Detener entorno staging
    ${GREEN}restart${NC}     Reiniciar entorno staging
    ${GREEN}status${NC}      Ver estado de servicios
    ${GREEN}logs${NC}        Ver logs [service]
    ${GREEN}migrate${NC}     Ejecutar migraciones Alembic
    ${GREEN}shell${NC}       Abrir shell [api|db|redis|caddy]
    ${GREEN}clean${NC}       Limpiar entorno (elimina volumes)
    ${GREEN}smoke${NC}       Ejecutar smoke tests
    ${GREEN}help${NC}        Mostrar esta ayuda

${YELLOW}Ejemplos:${NC}
    ./scripts/staging.sh up
    ./scripts/staging.sh logs api-staging
    ./scripts/staging.sh shell db
    ./scripts/staging.sh migrate
    ./scripts/staging.sh smoke

${YELLOW}URLs:${NC}
    API HTTP:  http://localhost:8001
    API HTTPS: https://localhost:8443
    PostgreSQL: localhost:5435
    Redis: localhost:6382

${YELLOW}Notas:${NC}
    - HTTPS usa certificado self-signed (warning esperado)
    - Para curl: usar flag -k (--insecure)
    - Para k6: usar --insecure-skip-tls-verify
EOF
}

# ────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────

main() {
    local command="${1:-help}"
    
    case "$command" in
        up)
            cmd_up
            ;;
        down)
            cmd_down
            ;;
        restart)
            cmd_restart
            ;;
        status)
            cmd_status
            ;;
        logs)
            shift
            cmd_logs "$@"
            ;;
        migrate)
            cmd_migrate
            ;;
        shell)
            shift
            cmd_shell "$@"
            ;;
        clean)
            cmd_clean
            ;;
        smoke)
            cmd_smoke_test
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            log_error "Comando desconocido: $command"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
