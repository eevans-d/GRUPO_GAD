#!/bin/bash
# ==============================================================================
# SCRIPT DE ROLLBACK DE EMERGENCIA PARA GRUPO_GAD
#
# USO:
# 1. Edita las variables en la sección de CONFIGURACIÓN.
# 2. Asegúrate de que el archivo de backup de la BD exista en la ruta especificada.
# 3. Ejecuta desde la raíz del proyecto: ./scripts/emergency_rollback.sh
#
# ¡ADVERTENCIA! Este script es destructivo. Borrará la base de datos
# actual y la reemplazará con el backup. Úsalo solo en una emergencia.
# ==============================================================================

set -e # Termina el script inmediatamente si un comando falla.

# --- CONFIGURACIÓN (¡EDITAR ANTES DE USAR!) ---
# TODO: Especifica el tag de Git de la versión estable anterior.
PREVIOUS_GIT_TAG="v1.1.0" 

# TODO: Especifica la ruta al archivo de backup de la BD pre-despliegue.
DB_BACKUP_FILE="/var/backups/gad_prod_backup_pre_deploy.sqlc"

# TODO: Especifica el nombre del servicio de la API en docker-compose.
API_SERVICE_NAME="api"

# TODO: Especifica el nombre del servicio de la BD en docker-compose.
DB_SERVICE_NAME="postgres"

# Archivos de configuración de Docker
DOCKER_COMPOSE_PROD_FILE="docker/docker-compose.prod.yml"

# Variables de la base de datos (se tomarán del entorno si están disponibles)
DB_USER="${POSTGRES_USER:-gad_user}"
DB_NAME="${POSTGRES_DB:-gad_db}"

# --- INICIO DEL SCRIPT ---

echo "============================================="
echo "==   INICIANDO ROLLBACK DE EMERGENCIA      =="
echo "============================================="
echo "ADVERTENCIA: Este proceso es destructivo y tomará varios minutos."
read -p "¿Estás seguro de que quieres continuar? (s/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]
then
    echo "Rollback cancelado."
    exit 1
fi

# --- PASO 1: DETENER SERVICIOS ---
echo -e "
[PASO 1/5] Deteniendo todos los servicios de producción..."
docker compose -f "$DOCKER_COMPOSE_PROD_FILE" down
echo "Servicios detenidos."

# --- PASO 2: REVERTIR CÓDIGO FUENTE ---
echo -e "
[PASO 2/5] Revirtiendo el código a la versión estable anterior (Tag: $PREVIOUS_GIT_TAG)..."
git checkout "$PREVIOUS_GIT_TAG"
echo "Checkout a $PREVIOUS_GIT_TAG completado."

# --- PASO 3: RESTAURAR BASE DE DATOS ---
echo -e "
[PASO 3/5] Restaurando la base de datos desde el backup..."
echo "Archivo de backup: $DB_BACKUP_FILE"

if [ ! -f "$DB_BACKUP_FILE" ]; then
    echo "¡ERROR CRÍTICO! No se encontró el archivo de backup de la base de datos en '$DB_BACKUP_FILE'."
    echo "No se puede continuar con la restauración. El sistema está detenido."
    exit 1
fi

echo "Iniciando contenedor de la base de datos para la restauración..."
docker compose -f "$DOCKER_COMPOSE_PROD_FILE" up -d "$DB_SERVICE_NAME"
sleep 10 # Esperar a que el servicio de BD esté listo

echo "Borrando base de datos actual (si existe)..."
docker exec -i "$DB_SERVICE_NAME" dropdb -U "$DB_USER" --if-exists "$DB_NAME"

echo "Creando nueva base de datos vacía..."
docker exec -i "$DB_SERVICE_NAME" createdb -U "$DB_USER" "$DB_NAME"

echo "Restaurando desde el backup..."
cat "$DB_BACKUP_FILE" | docker exec -i "$DB_SERVICE_NAME" pg_restore -U "$DB_USER" -d "$DB_NAME"
echo "Base de datos restaurada."

# Opcional: Alembic downgrade (usar si no se restaura un backup completo)
# echo "Ejecutando 'alembic downgrade base'..."
# docker compose -f "$DOCKER_COMPOSE_PROD_FILE" run --rm "$API_SERVICE_NAME" alembic downgrade base

# --- PASO 4: REINICIAR TODOS LOS SERVICIOS ---
echo -e "
[PASO 4/5] Reiniciando todos los servicios con la versión anterior..."
docker compose -f "$DOCKER_COMPOSE_PROD_FILE" up -d --build
echo "Servicios reiniciados."

# --- PASO 5: VERIFICACIÓN BÁSICA ---
echo -e "
[PASO 5/5] Esperando que la API esté saludable (timeout: 120s)..."
HEALTH_CHECK_URL="http://localhost/api/v1/health/ping"
end_time=$((SECONDS+120))

while [ $SECONDS -lt $end_time ]; do
    if curl --silent --fail "$HEALTH_CHECK_URL" | grep -q "pong"; then
        echo "¡ÉXITO! La API está respondiendo correctamente."
        echo -e "
============================================="
        echo "==      ROLLBACK COMPLETADO CON ÉXITO      =="
        echo "============================================="
        echo "Por favor, realiza la validación manual según el checklist."
        exit 0
    fi
    echo "Esperando a la API..."
    sleep 5
done

echo "¡ERROR CRÍTICO! La API no respondió después de 120 segundos."
echo "El rollback ha fallado. Revisa los logs de los contenedores con:"
echo "docker compose -f $DOCKER_COMPOSE_PROD_FILE logs --tail=100 $API_SERVICE_NAME"
exit 1
