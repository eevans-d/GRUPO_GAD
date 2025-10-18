#!/bin/bash

################################################################################
# GRUPO_GAD - Fly.io Deployment Script
# 
# Automatiza el deployment completo a Fly.io:
# - Validación de pre-requisitos
# - Configuración de secrets
# - Deploy de base de datos (PostgreSQL)
# - Deploy de Redis (Upstash)
# - Deploy de la aplicación
# - Verificación post-deployment
#
# Uso:
#   ./scripts/deploy_flyio.sh [--skip-db] [--skip-redis] [--full]
#
# Opciones:
#   --skip-db     Salta la creación de PostgreSQL (si ya existe)
#   --skip-redis  Salta la creación de Redis (si ya existe)
#   --full        Deploy completo desde cero
#   --help        Muestra esta ayuda
################################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
APP_NAME="grupo-gad"
DB_NAME="grupo-gad-db"
REDIS_NAME="grupo-gad-redis"
REGION="mia"  # Miami - closest to Latin America
SKIP_DB=false
SKIP_REDIS=false

################################################################################
# HELPER FUNCTIONS
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 no está instalado"
        return 1
    fi
    return 0
}

show_help() {
    cat << EOF
GRUPO_GAD - Fly.io Deployment Script

Uso:
    ./scripts/deploy_flyio.sh [OPTIONS]

Opciones:
    --skip-db     Salta la creación de PostgreSQL (si ya existe)
    --skip-redis  Salta la creación de Redis (si ya existe)
    --full        Deploy completo desde cero (default)
    --help        Muestra esta ayuda

Ejemplos:
    # Deploy completo (primera vez)
    ./scripts/deploy_flyio.sh --full

    # Re-deploy solo la app (DB y Redis ya existen)
    ./scripts/deploy_flyio.sh --skip-db --skip-redis

    # Deploy app + Redis nuevo (DB existente)
    ./scripts/deploy_flyio.sh --skip-db

Variables de entorno requeridas:
    SECRET_KEY              (obligatorio)
    POSTGRES_USER           (obligatorio si --skip-db no está presente)
    POSTGRES_PASSWORD       (obligatorio si --skip-db no está presente)

EOF
}

################################################################################
# VALIDATION
################################################################################

validate_prerequisites() {
    log_info "Validando pre-requisitos..."

    # Check flyctl
    if ! check_command flyctl; then
        log_error "flyctl no está instalado. Instala con:"
        echo "  curl -L https://fly.io/install.sh | sh"
        exit 1
    fi

    # Check authentication
    if ! flyctl auth whoami &> /dev/null; then
        log_error "No estás autenticado en Fly.io"
        echo "Ejecuta: flyctl auth login"
        exit 1
    fi

    # Check fly.toml
    if [ ! -f "fly.toml" ]; then
        log_error "fly.toml no encontrado"
        exit 1
    fi

    # Check Dockerfile
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile no encontrado"
        exit 1
    fi

    log_success "Pre-requisitos validados"
}

validate_secrets() {
    log_info "Validando secrets..."

    if [ -z "${SECRET_KEY:-}" ]; then
        log_error "SECRET_KEY no está definida"
        echo "Ejecuta: export SECRET_KEY=your-secret-key"
        exit 1
    fi

    if [ "$SKIP_DB" = false ]; then
        if [ -z "${POSTGRES_USER:-}" ]; then
            log_warning "POSTGRES_USER no definida, usando default: postgres"
            export POSTGRES_USER="postgres"
        fi

        if [ -z "${POSTGRES_PASSWORD:-}" ]; then
            log_error "POSTGRES_PASSWORD no está definida"
            echo "Ejecuta: export POSTGRES_PASSWORD=your-password"
            exit 1
        fi

        if [ -z "${POSTGRES_DB:-}" ]; then
            log_warning "POSTGRES_DB no definida, usando default: grupo_gad"
            export POSTGRES_DB="grupo_gad"
        fi
    fi

    log_success "Secrets validados"
}

################################################################################
# DEPLOYMENT STEPS
################################################################################

create_app() {
    log_info "Verificando app en Fly.io..."

    if flyctl apps list | grep -q "$APP_NAME"; then
        log_success "App '$APP_NAME' ya existe"
    else
        log_info "Creando app '$APP_NAME'..."
        flyctl apps create "$APP_NAME" --org personal
        log_success "App creada"
    fi
}

setup_database() {
    if [ "$SKIP_DB" = true ]; then
        log_warning "Saltando creación de PostgreSQL (--skip-db)"
        return
    fi

    log_info "Configurando PostgreSQL..."

    # Check si DB ya existe
    if flyctl apps list | grep -q "$DB_NAME"; then
        log_warning "PostgreSQL '$DB_NAME' ya existe, saltando creación"
        
        # Verificar si está attached
        if flyctl postgres list --app "$APP_NAME" 2>/dev/null | grep -q "$DB_NAME"; then
            log_success "PostgreSQL ya está attached a la app"
        else
            log_info "Attachando PostgreSQL existente a la app..."
            flyctl postgres attach "$DB_NAME" --app "$APP_NAME"
            log_success "PostgreSQL attached"
        fi
        return
    fi

    log_info "Creando cluster PostgreSQL..."
    flyctl postgres create \
        --name "$DB_NAME" \
        --region "$REGION" \
        --initial-cluster-size 1 \
        --vm-size shared-cpu-1x \
        --volume-size 10 \
        --yes

    log_info "Attachando PostgreSQL a la app..."
    flyctl postgres attach "$DB_NAME" --app "$APP_NAME"

    log_success "PostgreSQL configurado correctamente"
}

setup_redis() {
    if [ "$SKIP_REDIS" = true ]; then
        log_warning "Saltando creación de Redis (--skip-redis)"
        return
    fi

    log_info "Configurando Redis (Upstash)..."

    # Check si Redis ya existe
    if flyctl redis list 2>/dev/null | grep -q "$REDIS_NAME"; then
        log_warning "Redis '$REDIS_NAME' ya existe, saltando creación"
        return
    fi

    log_info "Creando Redis en Upstash..."
    flyctl redis create \
        --name "$REDIS_NAME" \
        --region global \
        --plan free \
        --yes || {
            log_warning "Error creando Redis, puede que ya exista"
        }

    log_info "Attachando Redis a la app..."
    flyctl redis attach "$REDIS_NAME" --app "$APP_NAME" || {
        log_warning "Error attachando Redis, puede que ya esté attached"
    }

    log_success "Redis configurado correctamente"
}

configure_secrets() {
    log_info "Configurando secrets..."

    # Secret base
    log_info "Configurando SECRET_KEY..."
    flyctl secrets set SECRET_KEY="$SECRET_KEY" --app "$APP_NAME" --stage

    # Environment
    log_info "Configurando variables de entorno..."
    flyctl secrets set \
        ENVIRONMENT=production \
        DEBUG=false \
        --app "$APP_NAME" \
        --stage

    # PostgreSQL (si no se saltó)
    if [ "$SKIP_DB" = false ]; then
        log_info "Configurando credenciales PostgreSQL..."
        flyctl secrets set \
            POSTGRES_USER="$POSTGRES_USER" \
            POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
            POSTGRES_DB="$POSTGRES_DB" \
            --app "$APP_NAME" \
            --stage
    fi

    log_success "Secrets configurados (staged)"
}

deploy_app() {
    log_info "Deployando aplicación a Fly.io..."

    flyctl deploy --app "$APP_NAME" --strategy rolling

    log_success "Aplicación deployada"
}

################################################################################
# VERIFICATION
################################################################################

verify_deployment() {
    log_info "Verificando deployment..."

    # Wait for app to be ready
    log_info "Esperando que la app esté lista..."
    sleep 10

    # Get app URL
    APP_URL=$(flyctl info --app "$APP_NAME" --json | grep -o '"hostname":"[^"]*"' | cut -d'"' -f4)
    if [ -z "$APP_URL" ]; then
        APP_URL="${APP_NAME}.fly.dev"
    fi

    log_info "URL de la app: https://$APP_URL"

    # Check health endpoint
    log_info "Verificando health endpoint..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://$APP_URL/health" || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        log_success "Health check OK (HTTP $HTTP_CODE)"
    else
        log_error "Health check FAILED (HTTP $HTTP_CODE)"
        log_warning "Revisa los logs con: flyctl logs --app $APP_NAME"
        return 1
    fi

    # Show status
    log_info "Status de la app:"
    flyctl status --app "$APP_NAME"

    log_success "Deployment verificado correctamente"
}

show_post_deploy_info() {
    APP_URL=$(flyctl info --app "$APP_NAME" --json | grep -o '"hostname":"[^"]*"' | cut -d'"' -f4 || echo "${APP_NAME}.fly.dev")

    cat << EOF

${GREEN}═══════════════════════════════════════════════════════════════${NC}
${GREEN}           DEPLOYMENT COMPLETADO EXITOSAMENTE                  ${NC}
${GREEN}═══════════════════════════════════════════════════════════════${NC}

📍 App URL:        https://$APP_URL
📊 Dashboard:      https://fly.io/apps/$APP_NAME
📝 Logs:           flyctl logs --app $APP_NAME
🔍 Status:         flyctl status --app $APP_NAME
🖥️  SSH:            flyctl ssh console --app $APP_NAME

${BLUE}Endpoints disponibles:${NC}
├─ Health:         https://$APP_URL/health
├─ API Docs:       https://$APP_URL/docs
├─ ReDoc:          https://$APP_URL/redoc
├─ WebSocket:      wss://$APP_URL/ws/connect
└─ Dashboard:      https://$APP_URL/dashboard/

${YELLOW}Próximos pasos:${NC}
1. Verificar API: curl https://$APP_URL/health
2. Ver logs:      flyctl logs --app $APP_NAME
3. Monitorear:    flyctl dashboard --app $APP_NAME

${YELLOW}Comandos útiles:${NC}
├─ Restart:       flyctl apps restart $APP_NAME
├─ Scale:         flyctl scale memory 1024 --app $APP_NAME
├─ Secrets:       flyctl secrets list --app $APP_NAME
└─ DB Console:    flyctl postgres connect --app $DB_NAME

${GREEN}═══════════════════════════════════════════════════════════════${NC}

EOF
}

################################################################################
# MAIN
################################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-db)
                SKIP_DB=true
                shift
                ;;
            --skip-redis)
                SKIP_REDIS=true
                shift
                ;;
            --full)
                SKIP_DB=false
                SKIP_REDIS=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Opción desconocida: $1"
                show_help
                exit 1
                ;;
        esac
    done

    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║            GRUPO_GAD - FLY.IO DEPLOYMENT                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    # Validations
    validate_prerequisites
    validate_secrets

    # Deployment steps
    create_app
    setup_database
    setup_redis
    configure_secrets
    deploy_app

    # Verification
    verify_deployment

    # Post-deploy info
    show_post_deploy_info

    log_success "¡Deployment completado con éxito!"
}

# Run main
main "$@"
