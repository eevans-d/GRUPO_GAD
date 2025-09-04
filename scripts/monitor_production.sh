#!/bin/bash
# ==============================================================================
# SCRIPT DE MONITOREO BÁSICO PARA GRUPO_GAD EN PRODUCCIÓN
#
# USO:
# 1. Edita las variables en la sección de CONFIGURACIÓN.
# 2. Ejecuta manualmente: ./scripts/monitor_production.sh
# 3. O configúralo con cron para ejecución periódica.
#    Ejemplo de crontab para ejecución cada hora:
#    0 * * * * /path/to/project/GRUPO_GAD/scripts/monitor_production.sh
# ==============================================================================

# --- CONFIGURACIÓN (¡EDITAR ANTES DE USAR!) ---

# Archivos y URLs
DOCKER_COMPOSE_PROD_FILE="docker/docker-compose.prod.yml"
HEALTH_CHECK_URL="http://localhost/api/v1/health/ping"
DASHBOARD_URL="http://localhost/" # URL de la página principal
LOG_FILE="logs/production_monitor.log"
METRICS_LOG_FILE="logs/metrics.log"

# Nombres de servicios y contenedores
DB_SERVICE_NAME="postgres"
API_SERVICE_NAME="api"

# Credenciales de la base de datos (se tomarán del entorno si están disponibles)
DB_USER="${POSTGRES_USER:-gad_user}"
DB_NAME="${POSTGRES_DB:-gad_db}"
# ¡IMPORTANTE! Para que psql no pida contraseña, configura un .pgpass o usa variables de entorno
# export PGPASSWORD=$POSTGRES_PASSWORD

# Umbrales de Alerta
DISK_USAGE_THRESHOLD=80  # % de uso de disco para generar una alerta
RESPONSE_TIME_THRESHOLD=5 # Segundos para una respuesta de API aceptable

# --- FIN DE LA CONFIGURACIÓN ---

# Asegurarse de que el directorio de logs exista
mkdir -p "$(dirname "$LOG_FILE")"

# Función para registrar mensajes con timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] - $1"
}

# Redirigir toda la salida al archivo de log y a la consola
exec &> >(tee -a "$LOG_FILE")

log_message "--- INICIANDO CHEQUEO DE MONITOREO ---"

# --- 1. CHECKS DE SALUD Y ESTADO ---
log_message "Sección 1: Salud de Servicios y Recursos"

# Check de endpoint de salud
log_message "Verificando endpoint de salud: $HEALTH_CHECK_URL"
response_time=$(curl -s -o /dev/null -w "%{time_total}" --max-time $RESPONSE_TIME_THRESHOLD "$HEALTH_CHECK_URL")
status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time $RESPONSE_TIME_THRESHOLD "$HEALTH_CHECK_URL")

if [ "$status_code" -eq 200 ]; then
    log_message "[OK] Health endpoint respondió con código 200."
    if (( $(echo "$response_time > $RESPONSE_TIME_THRESHOLD" | bc -l) )); then
        log_message "[WARN] Tiempo de respuesta LENTO: ${response_time}s (Umbral: ${RESPONSE_TIME_THRESHOLD}s)."
    else
        log_message "[OK] Tiempo de respuesta: ${response_time}s."
    fi
else
    log_message "[FAIL] Health endpoint falló. Código de respuesta: $status_code."
fi

# Check del estado de los servicios de Docker
log_message "Verificando estado de los servicios Docker..."
docker compose -f "$DOCKER_COMPOSE_PROD_FILE" ps

# Check de uso de disco
log_message "Verificando uso de disco..."
df -h | { head -n 1; grep -E '/$|/dev/sda1'; } | while read -r line; do
    log_message "$line"
    usage=$(echo "$line" | awk '{print $5}' | sed 's/%//')
    if [[ "$usage" -ge "$DISK_USAGE_THRESHOLD" ]]; then
        log_message "[WARN] Uso de disco en o por encima del umbral: ${usage}% (Umbral: ${DISK_USAGE_THRESHOLD}%)."
    fi
done

# Check de estadísticas de recursos de Docker
log_message "Verificando estadísticas de recursos de contenedores..."
docker stats --no-stream

# --- 2. VALIDACIÓN FUNCIONAL ---
log_message "
Sección 2: Validación Funcional Diaria"

# Check de carga del Dashboard
log_message "Verificando carga del Dashboard: $DASHBOARD_URL"
dashboard_status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$DASHBOARD_URL")
if [ "$dashboard_status" -eq 200 ]; then
    log_message "[OK] Dashboard respondió con código 200."
else
    log_message "[FAIL] Dashboard no parece estar cargando. Código de respuesta: $dashboard_status."
fi

# Check de backups recientes (asumiendo una ruta y patrón de nombre)
log_message "Verificando backups recientes de la base de datos..."
BACKUP_DIR="/var/backups"
if find "$BACKUP_DIR" -name "gad_prod_backup*.sqlc" -mtime -1 -print | grep -q .; then
    log_message "[OK] Se encontró un archivo de backup de las últimas 24 horas."
else
    log_message "[WARN] No se encontraron backups recientes en $BACKUP_DIR."
fi

# --- 3. MÉTRICAS BÁSICAS DE APLICACIÓN ---
log_message "
Sección 3: Métricas Básicas de la Aplicación"

# Conexión a la base de datos para obtener métricas
run_db_query() {
    docker exec "$DB_SERVICE_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "$1" -t -A
}

# Conteo de usuarios
user_count=$(run_db_query "SELECT COUNT(*) FROM usuario;")
log_message "Métrica - Total de usuarios: $user_count"

# Tareas creadas en las últimas 24h
tasks_last_24h=$(run_db_query "SELECT COUNT(*) FROM tarea WHERE created_at >= NOW() - INTERVAL '24 hours';")
log_message "Métrica - Tareas creadas (últimas 24h): $tasks_last_24h"

# Log de métricas a un archivo separado
metrics_line="$(date '+%Y-%m-%dT%H:%M:%S'),total_users=$user_count,tasks_24h=$tasks_last_24h,api_response_time_s=$response_time"
echo "$metrics_line" >> "$METRICS_LOG_FILE"

log_message "Métricas guardadas en $METRICS_LOG_FILE"
log_message "NOTA: El conteo de mensajes de Telegram y el login de admin no se pueden automatizar de forma simple en este script y deben ser verificados manualmente."

log_message "--- CHEQUEO DE MONITOREO FINALIZADO ---
"
