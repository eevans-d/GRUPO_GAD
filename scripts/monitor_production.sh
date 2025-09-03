#!/bin/bash

# ==============================================================================
# SCRIPT DE MONITOREO BÁSICO DE PRODUCCIÓN - GRUPO GAD
# ==============================================================================
#
# USO:
#   Este script está diseñado para ser ejecutado periódicamente (ej. cada hora
#   vía cron) para monitorear la salud básica del sistema en producción.
#
# PRE-REQUISITOS:
#   - Estar autenticado en el servidor de producción.
#   - Docker y Docker Compose instalados.
#   - `jq` instalado para procesar JSON.
#
# ==============================================================================

# --- CONFIGURACIÓN ---
set -o pipefail # Salir si un comando en un pipeline falla

# Variables (ajustar según el entorno)
LOG_FILE="$(dirname "$0")/../logs/grupogad_monitor.log"
METRICS_FILE="$(dirname "$0")/../logs/grupogad_metrics.log"
API_URL="http://localhost:8000"
DOCKER_COMPOSE_PROD="docker/docker-compose.prod.yml" # Ruta relativa al directorio de ejecución del script

# Umbrales de Alerta
DISK_USAGE_THRESHOLD=80 # Porcentaje
API_RESPONSE_TIME_THRESHOLD=5 # Segundos

# --- FUNCIONES AUXILIARES ---

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] - $1" | tee -a "$LOG_FILE"
}

log_metric() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] - METRIC: $1" | tee -a "$METRICS_FILE"
}

send_alert() {
    log "ALERTA: $1"
    # Aquí se podría integrar una notificación real (ej. Telegram, Slack, Email)
    # echo "ALERTA: $1" | telegram-send
}

# --- CHECKS DE SALUD HORARIOS ---

perform_hourly_checks() {
    log "--- Iniciando Checks de Salud Horarios ---"

    # 1. Health Check de la API
    log "Realizando Health Check de la API..."
    API_HEALTH_START=$(date +%s.%N)
    API_HEALTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$API_URL/health")
    API_HEALTH_END=$(date +%s.%N)
    API_RESPONSE_TIME=$(echo "$API_HEALTH_END - $API_HEALTH_START" | bc)

    if [ "$API_HEALTH_CODE" -eq 200 ]; then
        log "API Health Check: OK (Código: $API_HEALTH_CODE, Tiempo: ${API_RESPONSE_TIME}s)"
    else
        send_alert "API Health Check FALLÓ (Código: $API_HEALTH_CODE)"
    fi

    if (( $(echo "$API_RESPONSE_TIME > $API_RESPONSE_TIME_THRESHOLD" | bc -l) )); then
        send_alert "Tiempo de respuesta de la API ALTO (${API_RESPONSE_TIME}s)"
    fi

    # 2. Estado de los Servicios Docker Compose
    log "Verificando estado de los servicios Docker Compose..."
    (cd "$(dirname "$0")/.." && docker-compose -f "$DOCKER_COMPOSE_PROD" ps) | tee -a "$LOG_FILE"
    if (cd "$(dirname "$0")/.." && docker-compose -f "$DOCKER_COMPOSE_PROD" ps | grep -q "Exit"); then
        send_alert "Uno o más servicios Docker Compose no están en estado 'Up'."
    fi

    # 3. Espacio en Disco
    log "Verificando espacio en disco..."
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/\%//g')
    log "Uso de disco: ${DISK_USAGE}%"
    if [ "$DISK_USAGE" -ge "$DISK_USAGE_THRESHOLD" ]; then
        send_alert "Uso de disco ALTO (${DISK_USAGE}%)"
    fi

    # 4. Uso de Recursos de Contenedores (CPU, Memoria)
    log "Verificando uso de recursos de contenedores..."
    docker stats --no-stream | tee -a "$LOG_FILE"
    # Aquí se podría añadir lógica para parsear la salida de docker stats y establecer umbrales
    # Por ejemplo, si la CPU o la memoria de un contenedor específico superan un límite.

    log "--- Checks de Salud Horarios Completados ---"
}

# --- VALIDACIÓN FUNCIONAL DIARIA ---

perform_daily_validation() {
    log "--- Iniciando Validación Funcional Diaria ---"

    # 1. Login Admin Exitoso
    log "Intentando login de administrador..."
    # Asume que tienes credenciales de prueba seguras o un método para obtener un token
    # Esto es un placeholder, la implementación real dependerá de tu API de auth
    ADMIN_USERNAME="admin"
    ADMIN_PASSWORD="your_admin_password" # ¡CAMBIAR ESTO EN PRODUCCIÓN!
    AUTH_RESPONSE=$(curl -s -X POST -F "username=$ADMIN_USERNAME" -F "password=$ADMIN_PASSWORD" "$API_URL/api/v1/auth/token")
    AUTH_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')

    if [ -n "$AUTH_TOKEN" ] && [ "$AUTH_TOKEN" != "null" ]; then
        log "Login de administrador: OK"
        # Opcional: Probar un endpoint protegido con este token
        # curl -s -H "Authorization: Bearer $AUTH_TOKEN" "$API_URL/api/v1/users/me"
    else
        send_alert "Login de administrador FALLÓ."
        log "Respuesta de autenticación: $AUTH_RESPONSE"
    fi

    # 2. Bot responde a /start
    log "Verificando respuesta del Bot de Telegram a /start..."
    # Esto requiere una forma de interactuar con el bot, que no es trivial desde un script bash.
    # Una opción sería un script Python separado que use la API de Telegram.
    # Por ahora, es un check manual o un placeholder.
    log "Verificación del Bot: Requiere validación manual o un script externo."
    # Placeholder para un check real:
    # if python3 check_telegram_bot.py; then
    #     log "Bot de Telegram responde a /start: OK"
    # else
    #     send_alert "Bot de Telegram NO responde a /start."
    # fi

    # 3. Dashboard carga correctamente
    log "Verificando carga del Dashboard (página principal)..."
    DASHBOARD_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$API_URL/")
    if [ "$DASHBOARD_HTTP_CODE" -eq 200 ]; then
        log "Dashboard carga correctamente: OK (Código: $DASHBOARD_HTTP_CODE)"
    else
        send_alert "Dashboard NO carga correctamente (Código: $DASHBOARD_HTTP_CODE)"
    fi

    # 4. Backups se generan automáticamente
    log "Verificando generación automática de backups..."
    # Asume que los backups se guardan en un directorio específico y tienen un patrón de nombre
    BACKUP_DIR="/opt/backups/db" # Ajustar si es diferente
    if find "$BACKUP_DIR" -mtime -1 -name "*.sql.gz" | grep -q .; then
        log "Backups de base de datos generados en las últimas 24h: OK"
    else
        send_alert "NO se encontraron backups de base de datos en las últimas 24h."
    fi

    log "--- Validación Funcional Diaria Completada ---"
}

# --- MÉTRICAS BÁSICAS ---

collect_basic_metrics() {
    log "--- Recopilando Métricas Básicas ---"

    # 1. Conteo de Usuarios Activos (ej. en las últimas 24h)
    # Esto requiere un endpoint en la API o acceso directo a la BD
    log "Obteniendo conteo de usuarios activos..."
    # Placeholder: Asume un endpoint /metrics/active_users
    ACTIVE_USERS=$(curl -s "$API_URL/metrics/active_users" | jq -r '.count')
    if [ -n "$ACTIVE_USERS" ] && [ "$ACTIVE_USERS" != "null" ]; then
        log_metric "Usuarios Activos (24h): $ACTIVE_USERS"
    else
        log "No se pudo obtener el conteo de usuarios activos."
    fi

    # 2. Tareas Creadas en Últimas 24h
    log "Obteniendo tareas creadas en últimas 24h..."
    # Placeholder: Asume un endpoint /metrics/tasks_created_24h
    TASKS_CREATED=$(curl -s "$API_URL/metrics/tasks_created_24h" | jq -r '.count')
    if [ -n "$TASKS_CREATED" ] && [ "$TASKS_CREATED" != "null" ]; then
        log_metric "Tareas Creadas (24h): $TASKS_CREATED"
    else
        log "No se pudo obtener el conteo de tareas creadas."
    fi

    # 3. Mensajes Telegram Enviados (requiere integración con el bot)
    log "Obteniendo mensajes de Telegram enviados..."
    # Esto es complejo sin un sistema de logs centralizado o un endpoint específico.
    log "Métrica de Mensajes Telegram: Requiere integración específica."
    # Placeholder:
    # TELEGRAM_MESSAGES=$(curl -s "$API_URL/metrics/telegram_messages_24h" | jq -r '.count')
    # if [ -n "$TELEGRAM_MESSAGES" ] && [ "$TELEGRAM_MESSAGES" != "null" ]; then
    #     log_metric "Mensajes Telegram Enviados (24h): $TELEGRAM_MESSAGES"
    # else
    #     log "No se pudo obtener el conteo de mensajes de Telegram."
    # fi

    # 4. Tiempo de Respuesta Promedio (ej. de un endpoint clave)
    log "Obteniendo tiempo de respuesta promedio de un endpoint clave..."
    # Esto se puede obtener de logs de acceso del servidor web (nginx/uvicorn)
    # o de un endpoint de métricas si la API lo expone.
    # Para este script, ya se calculó el tiempo de respuesta del health check.
    log_metric "Tiempo de Respuesta Promedio (Health Check): ${API_RESPONSE_TIME}s"
}

# --- EJECUCIÓN PRINCIPAL ---

# Crear archivos de log si no existen
touch "$LOG_FILE"
touch "$METRICS_FILE"

# Determinar si es el momento de ejecutar la validación diaria (ej. una vez al día a las 03:00 AM)
# Esto es un ejemplo, se puede ajustar la lógica de cron para esto.
CURRENT_HOUR=$(date +%H)
if [ "$CURRENT_HOUR" -eq 03 ]; then # Ejecutar a las 03:00 AM
    perform_daily_validation
fi

# Siempre ejecutar los checks horarios y la recolección de métricas
perform_hourly_checks
collect_basic_metrics

log "Monitoreo completado."