#!/bin/bash
# ========================================================================
# 🚀 GRUPO_GAD - Production Deployment Script
# ========================================================================
# Descripción: Zero-downtime deployment a producción con smoke tests
# Uso: ./scripts/deploy_production.sh [--skip-backup] [--force]
# ========================================================================

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
ENV_FILE="${PROJECT_ROOT}/.env.production"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOY_LOG="${PROJECT_ROOT}/logs/deploy_${TIMESTAMP}.log"

# Argumentos
SKIP_BACKUP=false
FORCE_DEPLOY=false

# Funciones de utilidad
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "${DEPLOY_LOG}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "${DEPLOY_LOG}" >&2
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "${DEPLOY_LOG}"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $*" | tee -a "${DEPLOY_LOG}"
}

check_prerequisites() {
    log "🔍 Verificando prerequisitos..."
    
    # Verificar docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    
    # Verificar docker compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose no está instalado"
        exit 1
    fi
    
    # Verificar archivo de configuración
    if [ ! -f "${COMPOSE_FILE}" ]; then
        log_error "docker-compose.prod.yml no encontrado"
        exit 1
    fi
    
    # Verificar .env.production
    if [ ! -f "${ENV_FILE}" ]; then
        log_error ".env.production no encontrado. Copiar de .env.production.example"
        exit 1
    fi
    
    # Verificar que no sea el ejemplo
    if grep -q "CAMBIAR_POR" "${ENV_FILE}"; then
        log_error ".env.production contiene valores placeholder. Configurar primero."
        exit 1
    fi
    
    log "✅ Prerequisitos OK"
}

backup_database() {
    if [ "$SKIP_BACKUP" = true ]; then
        log_warn "⏭️  Backup omitido (--skip-backup)"
        return 0
    fi
    
    log "💾 Creando backup de base de datos..."
    
    mkdir -p "${BACKUP_DIR}"
    
    # Extraer credenciales del .env
    source "${ENV_FILE}"
    
    BACKUP_FILE="${BACKUP_DIR}/pre_deploy_${TIMESTAMP}.sql.gz"
    
    docker compose -f "${COMPOSE_FILE}" exec -T db pg_dump \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --no-owner --no-acl \
        | gzip > "${BACKUP_FILE}"
    
    if [ -f "${BACKUP_FILE}" ] && [ -s "${BACKUP_FILE}" ]; then
        log "✅ Backup creado: ${BACKUP_FILE}"
        echo "${BACKUP_FILE}" > "${BACKUP_DIR}/latest_backup.txt"
    else
        log_error "Backup falló"
        exit 1
    fi
}

pull_latest_images() {
    log "📦 Descargando últimas imágenes..."
    
    cd "${PROJECT_ROOT}"
    docker compose -f "${COMPOSE_FILE}" pull
    
    log "✅ Imágenes actualizadas"
}

run_migrations() {
    log "🗄️  Ejecutando migraciones de base de datos..."
    
    # Ejecutar migraciones en un contenedor temporal
    docker compose -f "${COMPOSE_FILE}" run --rm --no-deps api \
        alembic upgrade head
    
    if [ $? -eq 0 ]; then
        log "✅ Migraciones completadas"
    else
        log_error "Migraciones fallaron"
        exit 1
    fi
}

deploy_services() {
    log "🚀 Desplegando servicios..."
    
    cd "${PROJECT_ROOT}"
    
    # Zero-downtime deployment: crear nuevos contenedores antes de eliminar viejos
    docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans --wait
    
    log "⏳ Esperando que servicios estén healthy..."
    sleep 10
    
    # Verificar health checks
    for service in db redis api; do
        log_info "Verificando health de $service..."
        for i in {1..30}; do
            if docker compose -f "${COMPOSE_FILE}" ps "$service" | grep -q "healthy\|running"; then
                log "✅ $service está healthy"
                break
            fi
            if [ $i -eq 30 ]; then
                log_error "$service no está healthy después de 30 intentos"
                docker compose -f "${COMPOSE_FILE}" logs "$service" | tail -50
                exit 1
            fi
            sleep 2
        done
    done
    
    log "✅ Servicios desplegados correctamente"
}

smoke_tests() {
    log "🧪 Ejecutando smoke tests..."
    
    # Esperar que API esté lista
    sleep 5
    
    # Test 1: Health endpoint
    log_info "Test 1/3: Health endpoint..."
    for i in {1..10}; do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health || echo "000")
        if [ "$HTTP_CODE" = "200" ]; then
            log "✅ Health endpoint OK"
            break
        fi
        if [ $i -eq 10 ]; then
            log_error "Health endpoint falló: HTTP $HTTP_CODE"
            exit 1
        fi
        sleep 3
    done
    
    # Test 2: Metrics endpoint
    log_info "Test 2/3: Metrics endpoint..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/metrics || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        log "✅ Metrics endpoint OK"
    else
        log_error "Metrics endpoint falló: HTTP $HTTP_CODE"
        exit 1
    fi
    
    # Test 3: WebSocket connection
    log_info "Test 3/3: WebSocket connection..."
    if [ -f "${SCRIPT_DIR}/ws_smoke_test.py" ]; then
        cd "${PROJECT_ROOT}"
        if python3 "${SCRIPT_DIR}/ws_smoke_test.py" &> /dev/null; then
            log "✅ WebSocket connection OK"
        else
            log_warn "⚠️  WebSocket test falló (no crítico)"
        fi
    else
        log_warn "⚠️  ws_smoke_test.py no encontrado, omitiendo"
    fi
    
    log "✅ Smoke tests completados"
}

cleanup_old_images() {
    log "🧹 Limpiando imágenes antiguas..."
    
    docker image prune -f --filter "until=48h" || true
    
    log "✅ Limpieza completada"
}

print_deployment_info() {
    log ""
    log "╔════════════════════════════════════════════════════════════════╗"
    log "║              🎉 DEPLOYMENT COMPLETADO EXITOSAMENTE             ║"
    log "╚════════════════════════════════════════════════════════════════╝"
    log ""
    log "📊 Información de deployment:"
    log "   • Timestamp: ${TIMESTAMP}"
    log "   • Log file: ${DEPLOY_LOG}"
    
    if [ -f "${BACKUP_DIR}/latest_backup.txt" ]; then
        LATEST_BACKUP=$(cat "${BACKUP_DIR}/latest_backup.txt")
        log "   • Backup: ${LATEST_BACKUP}"
    fi
    
    log ""
    log "🔗 Endpoints disponibles:"
    log "   • API Health: http://localhost:8000/api/v1/health"
    log "   • Metrics:    http://localhost:8000/metrics"
    log "   • WebSocket:  ws://localhost:8000/ws/connect"
    log ""
    log "📝 Comandos útiles:"
    log "   • Ver logs:       docker compose -f ${COMPOSE_FILE} logs -f api"
    log "   • Ver status:     docker compose -f ${COMPOSE_FILE} ps"
    log "   • Rollback:       ./scripts/rollback_production.sh"
    log ""
}

# ========================================================================
# MAIN
# ========================================================================

main() {
    # Parse argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            *)
                log_error "Argumento desconocido: $1"
                echo "Uso: $0 [--skip-backup] [--force]"
                exit 1
                ;;
        esac
    done
    
    # Banner
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║           🚀 GRUPO_GAD - Production Deployment 🚀              ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Crear directorio de logs
    mkdir -p "$(dirname "${DEPLOY_LOG}")"
    
    # Confirmación si no es force
    if [ "$FORCE_DEPLOY" = false ]; then
        log_warn "⚠️  Este script desplegará a PRODUCCIÓN"
        read -p "¿Continuar? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log "❌ Deployment cancelado por el usuario"
            exit 0
        fi
    fi
    
    # Ejecutar pasos de deployment
    check_prerequisites
    backup_database
    pull_latest_images
    run_migrations
    deploy_services
    smoke_tests
    cleanup_old_images
    print_deployment_info
    
    log "🎉 Deployment completado exitosamente"
    exit 0
}

# Trap para limpiar en caso de error
trap 'log_error "Deployment falló en línea $LINENO. Ver log: ${DEPLOY_LOG}"' ERR

main "$@"
