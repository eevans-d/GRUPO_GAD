#!/usr/bin/env bash
# ----------------------------------------------------------------
# Nombre: postgres_backup.sh
# Descripción: Script para realizar backups periódicos de PostgreSQL
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

# S3 bucket (opcional)
S3_BUCKET=${S3_BUCKET:-""}
S3_PREFIX=${S3_PREFIX:-"grupogad/backups/"}

# Configuración de retención
RETENTION_DAYS=${RETENTION_DAYS:-"7"}  # días para mantener backups locales
S3_RETENTION_DAYS=${S3_RETENTION_DAYS:-"30"}  # días para mantener backups en S3

# Timestamp para el nombre del archivo
TIMESTAMP=$(date +"%Y%m%dT%H%M%SZ")
BACKUP_FILE="${BACKUP_DIR}/postgres_${DB_NAME}_${TIMESTAMP}.sql.gz"
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"

# Log function
log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") - $1" | tee -a "$LOG_FILE"
}

log "Iniciando backup de PostgreSQL..."
log "Base de datos: $DB_NAME"
log "Archivo destino: $BACKUP_FILE"

# Verificar si PGPASSWORD está configurado
if [ -z "$DB_PASSWORD" ]; then
    log "ADVERTENCIA: DB_PASSWORD no configurado, usando autenticación por confianza"
    # Usar variables de entorno para pg_dump
    export PGHOST="$DB_HOST"
    export PGPORT="$DB_PORT"
    export PGUSER="$DB_USER"
    export PGDATABASE="$DB_NAME"
    
    # Ejecutar pg_dump sin password
    pg_dump --clean --create --format=plain | gzip > "$BACKUP_FILE"
else
    # Usar PGPASSWORD para autenticación
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        --clean \
        --create \
        --format=plain \
        "$DB_NAME" | gzip > "$BACKUP_FILE"
fi

# Verificar resultado
if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "✅ Backup completado exitosamente. Tamaño: $BACKUP_SIZE"
    
    # Calcular hash para verificación de integridad
    BACKUP_HASH=$(sha256sum "$BACKUP_FILE" | awk '{ print $1 }')
    log "SHA256: $BACKUP_HASH"
    echo "$BACKUP_HASH" > "${BACKUP_FILE}.sha256"
    
    # Crear un archivo metadata con información del backup
    cat > "${BACKUP_FILE}.meta" << EOL
timestamp: $TIMESTAMP
database: $DB_NAME
host: $DB_HOST
user: $DB_USER
size_bytes: $(stat -c%s "$BACKUP_FILE")
sha256: $BACKUP_HASH
EOL
    
    # Subir a S3 si está configurado
    if [ -n "$S3_BUCKET" ]; then
        log "Subiendo backup a S3 bucket: $S3_BUCKET..."
        
        # Verificar si aws cli está instalado
        if command -v aws &> /dev/null; then
            # Nombre del archivo en S3
            S3_FILE="${S3_PREFIX}postgres_${DB_NAME}_${TIMESTAMP}.sql.gz"
            
            # Subir archivo principal
            aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/${S3_FILE}"
            
            # Subir archivo de hash
            aws s3 cp "${BACKUP_FILE}.sha256" "s3://${S3_BUCKET}/${S3_FILE}.sha256"
            
            # Subir archivo de metadata
            aws s3 cp "${BACKUP_FILE}.meta" "s3://${S3_BUCKET}/${S3_FILE}.meta"
            
            if [ $? -eq 0 ]; then
                log "✅ Backup subido exitosamente a S3: s3://${S3_BUCKET}/${S3_FILE}"
                
                # Eliminar backups antiguos en S3
                if [ $S3_RETENTION_DAYS -gt 0 ]; then
                    log "Buscando backups antiguos en S3 (>${S3_RETENTION_DAYS} días)..."
                    OLD_DATE=$(date -d "-${S3_RETENTION_DAYS} days" +"%Y-%m-%d")
                    
                    # Listar archivos antiguos
                    S3_OLD_FILES=$(aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}" | grep -B1 "$OLD_DATE" | awk '{print $4}')
                    
                    # Eliminar cada archivo antiguo
                    for file in $S3_OLD_FILES; do
                        log "Eliminando archivo S3 antiguo: $file"
                        aws s3 rm "s3://${S3_BUCKET}/${S3_PREFIX}${file}"
                    done
                fi
            else
                log "❌ Error al subir backup a S3"
            fi
        else
            log "❌ aws cli no está instalado. No se puede subir a S3."
        fi
    fi
    
    # Limpiar backups locales antiguos
    if [ $RETENTION_DAYS -gt 0 ]; then
        log "Limpiando backups locales antiguos (>${RETENTION_DAYS} días)..."
        find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime +$RETENTION_DAYS -delete
        find "$BACKUP_DIR" -name "postgres_*.sql.gz.sha256" -mtime +$RETENTION_DAYS -delete
        find "$BACKUP_DIR" -name "postgres_*.sql.gz.meta" -mtime +$RETENTION_DAYS -delete
        log "Limpieza de backups antiguos completada"
    fi
else
    log "❌ ERROR: Backup falló con código de salida $?"
    exit 1
fi

log "Proceso de backup finalizado"
exit 0