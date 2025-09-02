#!/bin/bash
set -e

# ==============================================================================
# SCRIPT DE DESPLIEGUE A PRODUCCIÓN PARA GRUPO GAD
#
# USO:
# 1. Reemplaza los valores de las variables en la sección "PLACEHOLDERS".
# 2. Asegúrate de tener un archivo .env.production localmente con las
#    credenciales correctas que se copiarán al servidor.
# 3. Ejecuta el script desde la raíz del proyecto: ./src/scripts/deploy_production.sh
# ==============================================================================

# --- Bloque 1: Copia de Archivos y Configuración del Entorno ---

# --- 1. Definir Placeholders (¡¡¡REEMPLAZAR ANTES DE EJECUTAR!!!) ---
export PROD_DOMAIN="grupo-gad.com"
export PROD_VPS_IP="123.45.67.89"
export PROD_REMOTE_PATH="/opt/grupo-gad"
export REMOTE_USER="root"

echo "--- 🚨 ADVERTENCIA ---"
echo "Estás a punto de desplegar en el entorno de PRODUCCIÓN."
echo "Dominio: ${PROD_DOMAIN}"
echo "Servidor: ${PROD_VPS_IP}"
echo "Presiona Ctrl+C en los próximos 5 segundos para cancelar."
sleep 5

# --- 2. Sincronizar archivos del proyecto con rsync ---
echo ">>> Sincronizando archivos con el servidor de producción..."
rsync -avz -e ssh \
  --exclude='.git' \
  --exclude='*.md' \
  --exclude='__pycache__/' \
  --exclude='.pytest_cache/' \
  --exclude='.venv/' \
  --exclude='*.db' \
  --exclude='.env' \
  --exclude='tests/' \
  . ${REMOTE_USER}@${PROD_VPS_IP}:${PROD_REMOTE_PATH}/

# --- 3. Configurar variables de entorno sensibles en el servidor ---
echo ">>> Configurando variables de entorno en ${PROD_REMOTE_PATH}/.env.production..."
# Este comando copia de forma segura el contenido de tu .env.production local al servidor.
cat .env.production | ssh -t ${REMOTE_USER}@${PROD_VPS_IP} "cat > ${PROD_REMOTE_PATH}/.env.production"
echo ">>> Configuración inicial completada."


# --- Bloque 2: Despliegue con Docker y Migraciones ---

echo ">>> Conectándose al VPS para iniciar el despliegue de servicios..."
ssh -t ${REMOTE_USER}@${PROD_VPS_IP} << EOF
  set -e
  cd ${PROD_REMOTE_PATH}

  echo ">>> (1/3) Levantando servicios con Docker Compose..."
  docker compose -f docker/docker-compose.prod.yml up -d --build --force-recreate

  echo ">>> (2/3) Esperando a que la base de datos se inicie..."
  sleep 20

  echo ">>> (3/3) Aplicando migraciones de base de datos (Alembic)..."
  docker compose -f docker/docker-compose.prod.yml exec api poetry run alembic upgrade head

  echo "--- ✅ Servicios desplegados y base de datos actualizada ---"
EOF


# --- Bloque 3: Validación Post-Despliegue ---

echo ">>> Iniciando validación post-despliegue..."

# --- 1. Health Check del API ---
echo ">>> Verificando Health Check en https://${PROD_DOMAIN}/api/v1/health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --insecure https://${PROD_DOMAIN}/api/v1/health)
if [ "$HEALTH_STATUS" -eq 200 ]; then
  echo "✅ Health Check OK (Código 200)."
else
  echo "🚨 ERROR: Health Check falló (Código ${HEALTH_STATUS})."
  exit 1
fi

# --- 2. Ejecutar Smoke Tests contra Producción ---
echo ">>> Ejecutando smoke tests contra el dominio de producción..."
if [ -f "./scripts/smoke_staging.sh" ]; then
    ./scripts/smoke_staging.sh https://${PROD_DOMAIN}
else
    echo "⚠️  Advertencia: No se encontró el script de smoke tests."
fi

# --- 3. Verificación de SSL ---
echo ">>> Verificando certificado SSL..."
echo | openssl s_client -servername ${PROD_DOMAIN} -connect ${PROD_DOMAIN}:443 2>/dev/null | openssl x509 -noout -dates

# --- 4. Verificaciones Manuales ---
echo "--- Verificaciones Manuales Pendientes ---"
echo "  [ ] Confirma que el bot responde a comandos en el grupo de Telegram."
echo "  [ ] Accede a https://${PROD_DOMAIN}/dashboard y verifica que la autenticación funciona."
echo "-----------------------------------------"


# --- Bloque 4: Finalización y Comunicación ---

echo ">>> Iniciando tareas de finalización..."

# --- 1. Backup Inicial Post-Deploy (ejecutado en el servidor) ---
echo ">>> Creando primer backup de la base de datos de producción..."
ssh -t ${REMOTE_USER}@${PROD_VPS_IP} << EOF
  set -e
  # Se asume que el directorio /opt/backups existe en el servidor
  mkdir -p /opt/backups
  DB_CONTAINER=\\\$(docker ps -qf "name=gad_db_prod")
  TIMESTAMP=\\\$(date +%Y%m%d_%H%M%S)
  BACKUP_FILE="/opt/backups/prod_db_backup_\$TIMESTAMP.sql.gz"
  
  echo "Creando backup en \$BACKUP_FILE..."
  docker exec \$DB_CONTAINER pg_dumpall -U \$(grep POSTGRES_USER .env.production | cut -d '=' -f2) | gzip > \$BACKUP_FILE
  
  echo "✅ Backup inicial creado en \$BACKUP_FILE"
EOF

# --- 2. Activar Scripts de Mantenimiento (Cron) ---
echo ">>> Recordatorio: Activa los cron jobs en el servidor si aún no lo has hecho."
echo "Ejemplo de cron para backups diarios:"
echo "0 2 * * * /root/scripts/backup_diario.sh >> /var/log/cron.log 2>&1"

# --- 3. Comunicación a Stakeholders ---
echo ""
echo "--- ✅ GO-LIVE COMPLETADO ---"
echo "El despliegue de la v1.0.0 en producción ha finalizado con éxito."
echo "La plataforma está operativa en: https://${PROD_DOMAIN}"
echo "Notificar a los stakeholders correspondientes."
