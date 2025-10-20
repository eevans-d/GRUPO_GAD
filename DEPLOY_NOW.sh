#!/bin/bash
# Script de despliegue automático para GRUPO_GAD en Fly.io
# Fecha: 20 Octubre 2025

set -e  # Exit on error

echo "=============================================="
echo "  GRUPO_GAD - Despliegue Automático Fly.io"
echo "=============================================="
echo ""

# Agregar flyctl al PATH
export PATH="/home/eevan/.fly/bin:$PATH"

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar instalación de flyctl
echo -e "${YELLOW}[1/7]${NC} Verificando flyctl..."
if ! command -v flyctl &> /dev/null; then
    echo -e "${RED}✗ flyctl no encontrado${NC}"
    exit 1
fi
echo -e "${GREEN}✓ flyctl instalado: $(flyctl version | head -1)${NC}"
echo ""

# Verificar autenticación
echo -e "${YELLOW}[2/7]${NC} Verificando autenticación..."
if ! flyctl auth whoami &> /dev/null; then
    echo -e "${YELLOW}⚠ No estás autenticado. Ejecutando login...${NC}"
    echo ""
    echo "Se abrirá tu navegador para autenticarte en Fly.io"
    echo "Presiona ENTER cuando estés listo..."
    read
    flyctl auth login
    echo ""
fi
FLYIO_USER=$(flyctl auth whoami 2>/dev/null || echo "unknown")
echo -e "${GREEN}✓ Autenticado como: ${FLYIO_USER}${NC}"
echo ""

# Cambiar al directorio del proyecto
echo -e "${YELLOW}[3/7]${NC} Navegando al directorio del proyecto..."
cd /home/eevan/ProyectosIA/GRUPO_GAD
echo -e "${GREEN}✓ En: $(pwd)${NC}"
echo ""

# Verificar que fly.toml existe
echo -e "${YELLOW}[4/7]${NC} Verificando configuración fly.toml..."
if [ ! -f "fly.toml" ]; then
    echo -e "${RED}✗ fly.toml no encontrado${NC}"
    exit 1
fi
echo -e "${GREEN}✓ fly.toml encontrado${NC}"
APP_NAME=$(grep 'app = ' fly.toml | cut -d'"' -f2)
echo -e "${GREEN}✓ App name: ${APP_NAME}${NC}"
echo ""

# Verificar que Dockerfile existe
echo -e "${YELLOW}[5/7]${NC} Verificando Dockerfile..."
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}✗ Dockerfile no encontrado${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Dockerfile encontrado${NC}"
# Verificar que tiene las fixes de PostgreSQL
if grep -q "libpq-dev" Dockerfile && grep -q "libpq5" Dockerfile; then
    echo -e "${GREEN}✓ PostgreSQL libraries presentes (libpq-dev, libpq5)${NC}"
else
    echo -e "${RED}✗ WARNING: PostgreSQL libraries faltantes en Dockerfile${NC}"
fi
echo ""

# Estado de la app en Fly.io
echo -e "${YELLOW}[6/7]${NC} Verificando estado de la app en Fly.io..."
flyctl status --app ${APP_NAME} 2>&1 | head -10 || echo "App no desplegada aún"
echo ""

# Preparar para deploy
echo -e "${YELLOW}[7/7]${NC} Preparando despliegue..."
echo ""
echo "=============================================="
echo "  LISTO PARA DESPLEGAR"
echo "=============================================="
echo ""
echo "Se ejecutará:"
echo "  $ flyctl deploy --app ${APP_NAME} --no-cache"
echo ""
echo -e "${YELLOW}Opciones:${NC}"
echo "  [1] Desplegar AHORA (automático)"
echo "  [2] Solo mostrar comandos (manual)"
echo "  [3] Cancelar"
echo ""
read -p "Elige opción [1/2/3]: " OPTION

case $OPTION in
    1)
        echo ""
        echo "=============================================="
        echo "  INICIANDO DESPLIEGUE"
        echo "=============================================="
        echo ""
        flyctl deploy --app ${APP_NAME} --no-cache
        
        echo ""
        echo "=============================================="
        echo "  DESPLIEGUE COMPLETADO"
        echo "=============================================="
        echo ""
        echo "Verificar:"
        echo "  $ curl https://${APP_NAME}.fly.dev/health"
        echo "  $ flyctl logs --app ${APP_NAME}"
        ;;
    2)
        echo ""
        echo "Comandos para ejecutar manualmente:"
        echo ""
        echo "  export PATH=\"/home/eevan/.fly/bin:\$PATH\""
        echo "  cd /home/eevan/ProyectosIA/GRUPO_GAD"
        echo "  flyctl deploy --app ${APP_NAME} --no-cache"
        echo ""
        ;;
    3)
        echo "Cancelado."
        exit 0
        ;;
    *)
        echo "Opción inválida."
        exit 1
        ;;
esac
