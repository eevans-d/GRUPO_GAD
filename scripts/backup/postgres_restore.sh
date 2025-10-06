#!/usr/bin/env bash
# ----------------------------------------------------------------
# Nombre: postgres_restore.sh
# Descripción: Script para restaurar PostgreSQL desde un backup
# Autor: GRUPO_GAD
# Fecha: 2025-10-06
# Versión: 1.0
# ----------------------------------------------------------------

# Configuración (por defecto toma valores del environment)
DB_HOST=${DB_HOST:-"postgres"}
DB_PORT=${DB_PORT:-"5432"}
DB_USER=${DB_USER:-"postgres"}
DB_NAME=${DB_NAME:-"grupogad"}
DB_PASSWORD=${DB_PASSWORD:-""}

# Directorio de backups: usa valor de entorno o default
BACKUP_DIR=${BACKUP_DIR:-"/home/eevan/ProyectosIA/GRUPO_GAD/backups"}

# Log file
LOG_FILE="${BACKUP_DIR}/restore_$(date +"%Y%m%dT%H%M%SZ").log"

# Log function
log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") - $1" | tee -a "$LOG_FILE"
}

# Mostrar ayuda si no se proporciona un archivo
if [ $# -lt 1 ]; then
    echo "Uso: $0 <archivo_backup> [--verify-only]"
    echo ""
    echo "Opciones:"
    echo "  --verify-only     Solo verificar el backup sin restaurarlo"
    echo ""
    echo "Ejemplo:"
    echo "  $0 ${BACKUP_DIR}/postgres_grupogad_20251006T120000Z.sql.gz"
    echo "  $0 ${BACKUP_DIR}/postgres_grupogad_20251006T120000Z.sql.gz --verify-only"
    echo ""
    echo "Backups disponibles:"
    find "$BACKUP_DIR" -name "postgres_*.sql.gz" | sort -r
    exit 1
fi

BACKUP_FILE=$1
VERIFY_ONLY=0

# Comprobar si se ha pasado la opción --verify-only
if [ $# -eq 2 ] && [ "$2" == "--verify-only" ]; then
    VERIFY_ONLY=1
fi

# Comprobar si el archivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    log "❌ ERROR: El archivo de backup no existe: $BACKUP_FILE"
    exit 1
fi

log "Iniciando verificación del backup: $BACKUP_FILE"

# Verificar integridad del backup
HASH_FILE="${BACKUP_FILE}.sha256"
if [ -f "$HASH_FILE" ]; then
    STORED_HASH=$(cat "$HASH_FILE")
    CALCULATED_HASH=$(sha256sum "$BACKUP_FILE" | awk '{ print $1 }')
    
    if [ "$STORED_HASH" == "$CALCULATED_HASH" ]; then
        log "✅ Verificación de integridad correcta"
    else
        log "❌ ERROR: Fallo en verificación de integridad del backup"
        log "Hash almacenado: $STORED_HASH"
        log "Hash calculado: $CALCULATED_HASH"
        exit 1
    fi
else
    log "⚠️ No se encontró archivo de hash para verificar integridad"
fi

# Mostrar metadatos si existen
META_FILE="${BACKUP_FILE}.meta"
if [ -f "$META_FILE" ]; then
    log "Metadatos del backup:"
    cat "$META_FILE" | tee -a "$LOG_FILE"
fi

# Si es solo verificación, terminar aquí
if [ $VERIFY_ONLY -eq 1 ]; then
    log "✅ Verificación completada exitosamente. No se realizará restauración."
    exit 0
fi

# Confirmación de restauración
log "⚠️ ADVERTENCIA: La restauración eliminará TODOS los datos actuales de la base de datos $DB_NAME"
log "Para continuar, escriba 'RESTAURAR' y presione Enter:"
read -r CONFIRM

if [ "$CONFIRM" != "RESTAURAR" ]; then
    log "Restauración cancelada por el usuario"
    exit 1
fi

log "Iniciando restauración de base de datos..."

# Verificar si PGPASSWORD está configurado
if [ -z "$DB_PASSWORD" ]; then
    log "ADVERTENCIA: DB_PASSWORD no configurado, usando autenticación por confianza"
    export PGHOST="$DB_HOST"
    export PGPORT="$DB_PORT"
    export PGUSER="$DB_USER"
    export PGDATABASE="$DB_NAME"
    
    # Realizar restauración
    gunzip -c "$BACKUP_FILE" | psql
else
    # Usar PGPASSWORD para autenticación
    gunzip -c "$BACKUP_FILE" | PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        "$DB_NAME"
fi

# Verificar resultado
if [ $? -eq 0 ]; then
    log "✅ Restauración completada exitosamente"
    
    # Ejecutar migraciones de Alembic para asegurar consistencia
    log "Ejecutando migraciones de Alembic para asegurar consistencia..."
    cd "$(dirname "$0")/../.." && poetry run alembic upgrade head
    
    if [ $? -eq 0 ]; then
        log "✅ Migraciones Alembic aplicadas correctamente"
    else
        log "⚠️ Advertencia: Fallo al aplicar migraciones Alembic. Es posible que necesite ejecutarlas manualmente."
    fi
else
    log "❌ ERROR: Restauración fallida con código de salida $?"
    exit 1
fi

log "Proceso de restauración finalizado"
exit 0