#!/bin/bash
# ========================================================================
# 🔄 GRUPO_GAD - Production Rollback Script
# ========================================================================
# Descripción: Rollback rápido a estado anterior con restauración de DB
# Uso: ./scripts/rollback_production.sh [--backup-file <path>]
# ========================================================================

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
ENV_FILE="${PROJECT_ROOT}/.env.production"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ROLLBACK_LOG="${PROJECT_ROOT}/logs/rollback_${TIMESTAMP}.log"

# Argumentos
BACKUP_FILE=""

# Funciones de utilidad
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "${ROLLBACK_LOG}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "${ROLLBACK_LOG}" >&2
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "${ROLLBACK_LOG}"
}

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $*" | tee -a "${ROLLBACK_LOG}"
}

find_latest_backup() {
    log "🔍 Buscando último backup..."
    
    if [ -f "${BACKUP_DIR}/latest_backup.txt" ]; then
        BACKUP_FILE=$(cat "${BACKUP_DIR}/latest_backup.txt")
        if [ -f "${BACKUP_FILE}" ]; then
            log "✅ Backup encontrado: ${BACKUP_FILE}"
            return 0
        fi
    fi
    
    # Buscar el más reciente
    LATEST=$(find "${BACKUP_DIR}" -name "pre_deploy_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [ -n "${LATEST}" ]; then
        BACKUP_FILE="${LATEST}"
        log "✅ Backup encontrado: ${BACKUP_FILE}"
        return 0
    fi
    
    log_error "No se encontró ningún backup"
    return 1
}

stop_services() {
    log "🛑 Deteniendo servicios..."
    
    cd "${PROJECT_ROOT}"
    docker compose -f "${COMPOSE_FILE}" stop api bot caddy
    
    log "✅ Servicios detenidos"
}

restore_database() {
    log "💾 Restaurando base de datos desde backup..."
    
    if [ -z "${BACKUP_FILE}" ] || [ ! -f "${BACKUP_FILE}" ]; then
        log_error "Backup file no válido: ${BACKUP_FILE}"
        return 1
    fi
    
    # Extraer credenciales
    source "${ENV_FILE}"
    
    log_info "Restaurando desde: ${BACKUP_FILE}"
    
    # Crear backup de seguridad del estado actual
    EMERGENCY_BACKUP="${BACKUP_DIR}/emergency_${TIMESTAMP}.sql.gz"
    log_info "Creando backup de emergencia: ${EMERGENCY_BACKUP}"
    docker compose -f "${COMPOSE_FILE}" exec -T db pg_dump \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --no-owner --no-acl \
        | gzip > "${EMERGENCY_BACKUP}" || log_warn "Backup de emergencia falló"
    
    # Restaurar backup
    log_info "Restaurando base de datos..."
    gunzip < "${BACKUP_FILE}" | docker compose -f "${COMPOSE_FILE}" exec -T db psql \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}"
    
    if [ $? -eq 0 ]; then
        log "✅ Base de datos restaurada"
    else
        log_error "Restauración de DB falló"
        return 1
    fi
}

rollback_code() {
    log "🔄 Haciendo rollback de código..."
    
    cd "${PROJECT_ROOT}"
    
    # Obtener commit anterior
    PREVIOUS_COMMIT=$(git log --oneline -2 | tail -1 | cut -d' ' -f1)
    
    if [ -n "${PREVIOUS_COMMIT}" ]; then
        log_info "Rollback a commit: ${PREVIOUS_COMMIT}"
        git checkout "${PREVIOUS_COMMIT}" 2>&1 | tee -a "${ROLLBACK_LOG}"
    else
        log_warn "No se pudo determinar commit anterior, omitiendo rollback de código"
    fi
    
    log "✅ Código revertido"
}

restart_services() {
    log "🔄 Reiniciando servicios..."
    
    cd "${PROJECT_ROOT}"
    docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans
    
    # Esperar health checks
    log_info "Esperando que servicios estén healthy..."
    sleep 10
    
    for service in db redis api; do
        for i in {1..20}; do
            if docker compose -f "${COMPOSE_FILE}" ps "$service" | grep -q "healthy\|running"; then
                log "✅ $service está healthy"
                break
            fi
            if [ $i -eq 20 ]; then
                log_error "$service no está healthy"
                docker compose -f "${COMPOSE_FILE}" logs "$service" | tail -30
                return 1
            fi
            sleep 2
        done
    done
    
    log "✅ Servicios reiniciados"
}

verify_rollback() {
    log "🧪 Verificando rollback..."
    
    sleep 5
    
    # Test health endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        log "✅ Health check OK"
    else
        log_error "Health check falló: HTTP $HTTP_CODE"
        return 1
    fi
    
    log "✅ Rollback verificado"
}

print_rollback_info() {
    log ""
    log "╔════════════════════════════════════════════════════════════════╗"
    log "║              🔄 ROLLBACK COMPLETADO EXITOSAMENTE               ║"
    log "╚════════════════════════════════════════════════════════════════╝"
    log ""
    log "📊 Información de rollback:"
    log "   • Timestamp: ${TIMESTAMP}"
    log "   • Log file: ${ROLLBACK_LOG}"
    log "   • Backup usado: ${BACKUP_FILE}"
    log ""
    log "📝 Comandos útiles:"
    log "   • Ver logs:   docker compose -f ${COMPOSE_FILE} logs -f api"
    log "   • Ver status: docker compose -f ${COMPOSE_FILE} ps"
    log ""
}

# ========================================================================
# MAIN
# ========================================================================

main() {
    # Parse argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup-file)
                BACKUP_FILE="$2"
                shift 2
                ;;
            *)
                log_error "Argumento desconocido: $1"
                echo "Uso: $0 [--backup-file <path>]"
                exit 1
                ;;
        esac
    done
    
    # Banner
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║            🔄 GRUPO_GAD - Production Rollback 🔄               ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    mkdir -p "$(dirname "${ROLLBACK_LOG}")"
    
    # Confirmación
    log_warn "⚠️  Este script hará ROLLBACK de PRODUCCIÓN"
    read -p "¿Continuar? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "❌ Rollback cancelado por el usuario"
        exit 0
    fi
    
    # Buscar backup si no se especificó
    if [ -z "${BACKUP_FILE}" ]; then
        if ! find_latest_backup; then
            log_error "No se puede hacer rollback sin backup"
            exit 1
        fi
    fi
    
    # Ejecutar rollback
    stop_services
    restore_database
    rollback_code
    restart_services
    verify_rollback
    print_rollback_info
    
    log "🎉 Rollback completado exitosamente"
    exit 0
}

trap 'log_error "Rollback falló en línea $LINENO. Ver log: ${ROLLBACK_LOG}"' ERR

main "$@"
