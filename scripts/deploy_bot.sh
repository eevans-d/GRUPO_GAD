#!/bin/bash
# ============================================
# Script de Deployment para Bot de Telegram
# GRUPO_GAD - Sistema Gubernamental
# ============================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${ENVIRONMENT:-staging}"
IMAGE_NAME="gad-bot"
REGISTRY="${DOCKER_REGISTRY:-docker.io}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

# Functions
print_header() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}\n"
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Validate environment
validate_environment() {
    print_step "Validando entorno de deployment..."
    
    if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
        print_error "ENVIRONMENT debe ser development, staging o production"
        exit 1
    fi
    
    print_success "Entorno: $ENVIRONMENT"
}

# Check prerequisites
check_prerequisites() {
    print_step "Verificando pre-requisitos..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        exit 1
    fi
    print_success "Docker instalado: $(docker --version)"
    
    # Check .env file
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        print_error "Archivo .env no encontrado en $PROJECT_ROOT"
        echo "  Copia .env.example a .env y configura las variables"
        exit 1
    fi
    print_success "Archivo .env encontrado"
    
    # Check critical env vars
    source "$PROJECT_ROOT/.env"
    
    if [[ -z "${TELEGRAM_TOKEN:-}" ]]; then
        print_error "TELEGRAM_TOKEN no está configurado en .env"
        exit 1
    fi
    
    if [[ -z "${ADMIN_CHAT_ID:-}" ]]; then
        print_error "ADMIN_CHAT_ID no está configurado en .env"
        exit 1
    fi
    
    print_success "Variables críticas configuradas"
}

# Run tests
run_tests() {
    print_step "Ejecutando tests del bot..."
    
    cd "$PROJECT_ROOT"
    
    if ! python -m pytest tests/bot/ -q --tb=short; then
        print_error "Tests fallaron. Abortando deployment."
        exit 1
    fi
    
    print_success "Todos los tests pasaron"
}

# Build Docker image
build_image() {
    print_step "Construyendo imagen Docker..."
    
    cd "$PROJECT_ROOT"
    
    docker build \
        -f docker/Dockerfile.bot \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        -t "${IMAGE_NAME}:latest" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        .
    
    print_success "Imagen construida: ${IMAGE_NAME}:${IMAGE_TAG}"
}

# Tag and push image
push_image() {
    if [[ "$ENVIRONMENT" == "development" ]]; then
        print_step "Omitiendo push en development"
        return 0
    fi
    
    print_step "Tagging imagen para registry..."
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${FULL_IMAGE}"
    
    print_step "Pushing imagen a registry..."
    
    if ! docker push "${FULL_IMAGE}"; then
        print_error "Failed to push image to registry"
        echo "  Asegúrate de estar autenticado: docker login $REGISTRY"
        exit 1
    fi
    
    print_success "Imagen pushed: ${FULL_IMAGE}"
}

# Deploy to environment
deploy() {
    print_step "Desplegando bot a $ENVIRONMENT..."
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        deploy_local
    elif [[ "$ENVIRONMENT" == "staging" || "$ENVIRONMENT" == "production" ]]; then
        deploy_docker_compose
    else
        print_error "Método de deployment no implementado para $ENVIRONMENT"
        exit 1
    fi
}

# Deploy locally with Docker Compose
deploy_local() {
    cd "$PROJECT_ROOT"
    
    print_step "Deteniendo contenedor anterior..."
    docker compose stop bot || true
    docker compose rm -f bot || true
    
    print_step "Iniciando bot con docker compose..."
    docker compose up -d bot
    
    print_success "Bot desplegado localmente"
}

# Deploy with Docker Compose (staging/production)
deploy_docker_compose() {
    cd "$PROJECT_ROOT"
    
    if [[ "$ENVIRONMENT" == "production" ]]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    else
        COMPOSE_FILE="docker-compose.yml"
    fi
    
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_error "Archivo $COMPOSE_FILE no encontrado"
        exit 1
    fi
    
    print_step "Deteniendo contenedor anterior..."
    docker compose -f "$COMPOSE_FILE" stop bot || true
    docker compose -f "$COMPOSE_FILE" rm -f bot || true
    
    print_step "Pulling imagen actualizada..."
    docker compose -f "$COMPOSE_FILE" pull bot || true
    
    print_step "Iniciando bot..."
    docker compose -f "$COMPOSE_FILE" up -d bot
    
    print_success "Bot desplegado con $COMPOSE_FILE"
}

# Verify deployment
verify_deployment() {
    print_step "Verificando deployment..."
    
    sleep 5  # Wait for bot to start
    
    # Check if container is running
    if docker ps | grep -q gad_bot; then
        print_success "Contenedor bot está corriendo"
    else
        print_error "Contenedor bot NO está corriendo"
        echo "  Ver logs: docker logs gad_bot_dev"
        exit 1
    fi
    
    # Check logs for errors
    print_step "Verificando logs iniciales..."
    docker logs --tail 20 gad_bot_dev 2>&1 | tail -10
    
    if docker logs --tail 50 gad_bot_dev 2>&1 | grep -qi "error\|exception\|traceback"; then
        print_error "Errores detectados en logs"
        echo "  Revisa logs completos: docker logs gad_bot_dev"
        exit 1
    fi
    
    print_success "Deployment verificado correctamente"
}

# Rollback function
rollback() {
    print_header "ROLLBACK - Revirtiendo a versión anterior"
    
    print_step "Deteniendo versión actual..."
    docker compose stop bot || true
    docker compose rm -f bot || true
    
    print_step "Desplegando versión anterior (tag: previous)..."
    IMAGE_TAG="previous" deploy
    
    print_success "Rollback completado"
}

# Show usage
usage() {
    cat << EOF
Uso: $0 [OPCIONES]

Script de deployment para el Bot de Telegram de GRUPO_GAD.

OPCIONES:
    -e, --environment ENV    Entorno (development|staging|production). Default: staging
    -t, --tag TAG            Tag de la imagen Docker. Default: latest
    -s, --skip-tests         Omitir ejecución de tests
    -p, --skip-push          Omitir push a registry
    -r, --rollback           Revertir a versión anterior
    -h, --help               Mostrar esta ayuda

VARIABLES DE ENTORNO:
    ENVIRONMENT              Entorno de deployment
    DOCKER_REGISTRY          Registry de Docker (default: docker.io)
    IMAGE_TAG                Tag de la imagen

EJEMPLOS:
    # Deploy local (development)
    $0 -e development

    # Deploy a staging
    $0 -e staging

    # Deploy a production con tag específico
    $0 -e production -t v1.0.0

    # Rollback en production
    $0 -e production --rollback

PREREQUISITOS:
    - Docker instalado
    - Archivo .env configurado
    - Tests pasando (si no se usa --skip-tests)
    - Autenticación en Docker registry (para staging/prod)

EOF
}

# Main execution
main() {
    SKIP_TESTS=false
    SKIP_PUSH=false
    DO_ROLLBACK=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -t|--tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            -s|--skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            -p|--skip-push)
                SKIP_PUSH=true
                shift
                ;;
            -r|--rollback)
                DO_ROLLBACK=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                print_error "Opción desconocida: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Execute rollback if requested
    if [[ "$DO_ROLLBACK" == true ]]; then
        rollback
        exit 0
    fi
    
    # Normal deployment flow
    print_header "DEPLOYMENT - Bot de Telegram GRUPO_GAD"
    echo "Entorno: $ENVIRONMENT"
    echo "Imagen: ${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    
    validate_environment
    check_prerequisites
    
    if [[ "$SKIP_TESTS" == false ]]; then
        run_tests
    else
        print_step "Omitiendo tests (--skip-tests)"
    fi
    
    build_image
    
    if [[ "$SKIP_PUSH" == false ]]; then
        push_image
    else
        print_step "Omitiendo push (--skip-push)"
    fi
    
    deploy
    verify_deployment
    
    print_header "DEPLOYMENT COMPLETADO EXITOSAMENTE"
    echo -e "${GREEN}✓ Bot desplegado en ${ENVIRONMENT}${NC}"
    echo -e "${GREEN}✓ Imagen: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
    echo ""
    echo "Comandos útiles:"
    echo "  - Ver logs: docker logs -f gad_bot_dev"
    echo "  - Detener bot: docker compose stop bot"
    echo "  - Rollback: $0 -e $ENVIRONMENT --rollback"
}

# Execute main
main "$@"
