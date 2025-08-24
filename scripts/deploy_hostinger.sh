#!/bin/bash

# Script para desplegar la aplicación GAD en un VPS de Hostinger.
#
# REQUISITOS:
# 1. El VPS debe tener Docker y Docker Compose instalados.
# 2. Debes tener acceso SSH al VPS con una clave pública.
# 3. Debes haber creado un archivo .env en el servidor con las credenciales de producción.

# --- Configuración ---
REMOTE_USER="root"                 # Usuario SSH en tu VPS
REMOTE_HOST="YOUR_VPS_IP"          # IP de tu VPS
PROJECT_DIR="/root/gad-project"    # Directorio del proyecto en el VPS

echo "--- Iniciando despliegue en Hostinger ---"

# 1. Copiar archivos del proyecto al VPS
# Se copian los directorios principales y los archivos de configuración.
# Se excluyen archivos de desarrollo como .git, .gitignore, etc.
echo ">>> Copiando archivos del proyecto a $REMOTE_USER@$REMOTE_HOST:$PROJECT_DIR..."
scp -r \
  --exclude='.git' \
  --exclude='.gitignore' \
  --exclude='*.md' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  api bot scripts workflows docker-compose.yml requirements.txt \
  $REMOTE_USER@$REMOTE_HOST:$PROJECT_DIR

# 2. Copiar el archivo .env de producción
# IMPORTANTE: Debes tener un archivo .env.production listo para copiar.
# O puedes crear el .env manualmente en el servidor.
# echo ">>> Copiando archivo .env de producción..."
# scp .env.production $REMOTE_USER@$REMOTE_HOST:$PROJECT_DIR/.env

# 3. Conectarse al VPS y levantar los servicios con Docker Compose
echo ">>> Conectándose a VPS para iniciar servicios..."
ssh $REMOTE_USER@$REMOTE_HOST << EOF
  cd $PROJECT_DIR
  
  echo ">>> Construyendo y levantando los contenedores (esto puede tardar)..."
  docker compose up -d --build
  
  echo ">>> Esperando a que la base de datos se inicie..."
  sleep 20
  
  echo ">>> Ejecutando el script de bootstrap..."
  bash scripts/bootstrap.sh
  
  echo "--- Despliegue completado ---"
  docker ps
EOF

echo "--- Proceso de despliegue finalizado ---"
