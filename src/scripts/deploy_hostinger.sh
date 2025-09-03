#!/bin/bash

# Script para desplegar la aplicación GAD en un VPS de Hostinger.
#
# REQUISITOS:
# 1. El VPS debe tener Docker y Docker Compose instalados.
# 2. Debes tener acceso SSH al VPS con una clave pública.
# 3. Debes haber creado un archivo .env.production en el servidor con las credenciales para este entorno.

# --- Configuración ---
REMOTE_USER="root"                      # Usuario SSH en tu VPS
REMOTE_HOST="YOUR_VPS_IP"               # IP de tu VPS
DOMAIN="staging.midominio.com"  # Dominio público para los health checks
PROJECT_DIR="/root/gad-project"         # Directorio del proyecto en el VPS

# --- ¡ATENCIÓN! ---
# Antes de ejecutar, asegúrate de reemplazar YOUR_VPS_IP y staging.tu-dominio.com
# con los valores correctos para tu entorno.

echo "--- Iniciando despliegue en Hostinger ---"
if [ "$REMOTE_HOST" = "YOUR_VPS_IP" ]; then
    echo "🚨 ERROR: Por favor, edita este script y reemplaza YOUR_VPS_IP con la IP de tu servidor."
    exit 1
fi


# 1. Copiar archivos del proyecto al VPS
# Se copian los directorios principales y los archivos de configuración.
# Se excluyen archivos de desarrollo como .git, .gitignore, etc.
# NOTA: Se usa rsync para mayor eficiencia y se incluyen pyproject.toml y poetry.lock,
# cruciales para la construcción de la imagen con Poetry.
echo ">>> Copiando archivos del proyecto a $REMOTE_USER@$REMOTE_HOST:$PROJECT_DIR..."
rsync -avz -e ssh \
  --exclude='.git' \
  --exclude='.gitignore' \
  --exclude='*.md' \
  --exclude='__pycache__/' \
  --exclude='.pytest_cache/' \
  --exclude='.venv/' \
  --exclude='*.pyc' \
  --exclude='htmlcov/' \
  --exclude='*.db' \
  . $REMOTE_USER@$REMOTE_HOST:$PROJECT_DIR/

# 2. Conectarse al VPS y ejecutar el ciclo de despliegue
echo ">>> Conectándose a VPS para iniciar servicios..."
ssh -t $REMOTE_USER@$REMOTE_HOST << EOF
  set -e # Salir inmediatamente si un comando falla
  cd $PROJECT_DIR
  
  echo ">>> (1/5) Construyendo y levantando los contenedores con el perfil de producción..."
  docker compose -f docker/docker-compose.prod.yml up -d --build --force-recreate
  
  echo ">>> (2/5) Esperando a que los servicios se inicien..."
  sleep 20
  
  echo ">>> (3/5) Aplicando migraciones de la base de datos..."
  docker compose -f docker/docker-compose.prod.yml exec api poetry run alembic upgrade head
  
  echo ">>> (4/5) Ejecutando health check..."
  # El flag --insecure es para evitar problemas con certificados autofirmados en staging.
  curl --fail --insecure https://$DOMAIN/api/v1/health || (echo "Health check falló" && exit 1)
  echo "✅ Health check OK"

  echo ">>> (5/5) Verificando estado de los servicios..."
  docker compose -f docker/docker-compose.prod.yml ps
  
  echo "--- Últimos logs de los servicios ---"
  docker compose -f docker/docker-compose.prod.yml logs --tail=10 api
  docker compose -f docker/docker-compose.prod.yml logs --tail=10 bot

  echo "--- ✅ Despliegue completado exitosamente ---"
EOF


echo "--- Proceso de despliegue finalizado ---"
