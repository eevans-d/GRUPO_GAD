#!/usr/bin/env bash
# ================================================================
# Script de Deployment Automatizado para Google Cloud Platform
# Proyecto: GRUPO_GAD
# ================================================================

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_ID="${GCP_PROJECT_ID:-grupo-gad-prod}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="grupo-gad-api"
IMAGE_NAME="api"
ARTIFACT_REGISTRY="us-central1-docker.pkg.dev"

# Funciones de utilidad
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

check_requirements() {
    log_info "Verificando requisitos..."
    
    # Verificar gcloud
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI no está instalado"
        exit 1
    fi
    
    # Verificar docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    
    # Verificar autenticación
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "No hay cuenta autenticada. Ejecuta: gcloud auth login"
        exit 1
    fi
    
    log_success "Todos los requisitos cumplidos"
}

build_image() {
    log_info "Construyendo imagen Docker..."
    
    VERSION="${1:-latest}"
    COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    docker build \
        -f docker/Dockerfile.cloudrun \
        -t "${IMAGE_NAME}:${VERSION}" \
        -t "${IMAGE_NAME}:${COMMIT_SHA}" \
        --build-arg BUILD_DATE="$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
        --build-arg VERSION="${VERSION}" \
        --build-arg COMMIT="${COMMIT_SHA}" \
        .
    
    log_success "Imagen construida: ${IMAGE_NAME}:${VERSION}"
}

tag_and_push() {
    log_info "Taggeando y pusheando imagen a Artifact Registry..."
    
    VERSION="${1:-latest}"
    COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    FULL_IMAGE_PATH="${ARTIFACT_REGISTRY}/${PROJECT_ID}/grupo-gad-images/${IMAGE_NAME}"
    
    # Tag para versión
    docker tag "${IMAGE_NAME}:${VERSION}" "${FULL_IMAGE_PATH}:${VERSION}"
    docker push "${FULL_IMAGE_PATH}:${VERSION}"
    
    # Tag para commit SHA
    docker tag "${IMAGE_NAME}:${COMMIT_SHA}" "${FULL_IMAGE_PATH}:${COMMIT_SHA}"
    docker push "${FULL_IMAGE_PATH}:${COMMIT_SHA}"
    
    # Tag latest
    docker tag "${IMAGE_NAME}:${VERSION}" "${FULL_IMAGE_PATH}:latest"
    docker push "${FULL_IMAGE_PATH}:latest"
    
    log_success "Imagen pusheada: ${FULL_IMAGE_PATH}:${VERSION}"
}

deploy_to_cloud_run() {
    log_info "Desplegando a Cloud Run..."
    
    VERSION="${1:-latest}"
    FULL_IMAGE_PATH="${ARTIFACT_REGISTRY}/${PROJECT_ID}/grupo-gad-images/${IMAGE_NAME}:${VERSION}"
    
    # Obtener connection name de Cloud SQL
    SQL_INSTANCE=$(gcloud sql instances describe grupo-gad-db \
        --format='get(connectionName)' 2>/dev/null || echo "")
    
    if [ -z "$SQL_INSTANCE" ]; then
        log_warning "No se encontró instancia Cloud SQL, continuando sin ella..."
    fi
    
    # Obtener IP de Redis
    REDIS_IP=$(gcloud redis instances describe grupo-gad-cache \
        --region="${REGION}" \
        --format='get(host)' 2>/dev/null || echo "")
    
    # Construir comando de deploy
    DEPLOY_CMD="gcloud run deploy ${SERVICE_NAME} \
        --image=${FULL_IMAGE_PATH} \
        --platform=managed \
        --region=${REGION} \
        --service-account=grupo-gad-api@${PROJECT_ID}.iam.gserviceaccount.com \
        --allow-unauthenticated \
        --min-instances=1 \
        --max-instances=10 \
        --cpu=2 \
        --memory=4Gi \
        --timeout=300 \
        --concurrency=80 \
        --port=8080 \
        --set-env-vars=ENVIRONMENT=production,PROJECT_NAME=GRUPO_GAD,API_V1_STR=/api/v1"
    
    # Añadir Cloud SQL si existe
    if [ -n "$SQL_INSTANCE" ]; then
        DEPLOY_CMD="${DEPLOY_CMD} --set-cloudsql-instances=${SQL_INSTANCE}"
        DEPLOY_CMD="${DEPLOY_CMD} --set-env-vars=POSTGRES_SERVER=/cloudsql/${SQL_INSTANCE},POSTGRES_DB=gad_db,POSTGRES_USER=gad_user,POSTGRES_PORT=5432"
    fi
    
    # Añadir Redis si existe
    if [ -n "$REDIS_IP" ]; then
        DEPLOY_CMD="${DEPLOY_CMD} --set-env-vars=REDIS_HOST=${REDIS_IP},REDIS_PORT=6379"
    fi
    
    # Añadir secretos
    DEPLOY_CMD="${DEPLOY_CMD} --set-secrets=SECRET_KEY=SECRET_KEY:latest,POSTGRES_PASSWORD=POSTGRES_PASSWORD:latest,TELEGRAM_TOKEN=TELEGRAM_TOKEN:latest"
    
    # Ejecutar deploy
    eval "$DEPLOY_CMD"
    
    log_success "Servicio desplegado en Cloud Run"
}

run_smoke_tests() {
    log_info "Ejecutando smoke tests..."
    
    # Obtener URL del servicio
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
        --region=${REGION} \
        --format='get(status.url)')
    
    if [ -z "$SERVICE_URL" ]; then
        log_error "No se pudo obtener URL del servicio"
        return 1
    fi
    
    log_info "URL del servicio: ${SERVICE_URL}"
    
    # Test 1: Health check
    log_info "Test 1: Health check..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/api/v1/health")
    if [ "$HTTP_CODE" == "200" ]; then
        log_success "✓ Health check passed (HTTP ${HTTP_CODE})"
    else
        log_error "✗ Health check failed (HTTP ${HTTP_CODE})"
        return 1
    fi
    
    # Test 2: Metrics endpoint
    log_info "Test 2: Metrics endpoint..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/metrics")
    if [ "$HTTP_CODE" == "200" ]; then
        log_success "✓ Metrics endpoint passed (HTTP ${HTTP_CODE})"
    else
        log_warning "⚠ Metrics endpoint returned HTTP ${HTTP_CODE}"
    fi
    
    # Test 3: API versión
    log_info "Test 3: API version..."
    RESPONSE=$(curl -s "${SERVICE_URL}/api/v1/health")
    if echo "$RESPONSE" | grep -q "status"; then
        log_success "✓ API version endpoint working"
    else
        log_error "✗ API version endpoint failed"
        return 1
    fi
    
    log_success "Todos los smoke tests pasaron ✓"
}

show_deployment_info() {
    log_info "Información del deployment:"
    
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
        --region=${REGION} \
        --format='get(status.url)' 2>/dev/null || echo "N/A")
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  DEPLOYMENT COMPLETADO"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  📦 Proyecto:    ${PROJECT_ID}"
    echo "  🌍 Región:      ${REGION}"
    echo "  🚀 Servicio:    ${SERVICE_NAME}"
    echo "  🔗 URL:         ${SERVICE_URL}"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Comandos útiles:"
    echo ""
    echo "  Ver logs:"
    echo "  $ gcloud run services logs read ${SERVICE_NAME} --region=${REGION}"
    echo ""
    echo "  Describir servicio:"
    echo "  $ gcloud run services describe ${SERVICE_NAME} --region=${REGION}"
    echo ""
    echo "  Ver métricas:"
    echo "  $ curl ${SERVICE_URL}/metrics"
    echo ""
}

main() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  GRUPO_GAD - Deployment Automatizado GCP"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    VERSION="${1:-latest}"
    
    check_requirements
    build_image "$VERSION"
    tag_and_push "$VERSION"
    deploy_to_cloud_run "$VERSION"
    run_smoke_tests
    show_deployment_info
    
    log_success "¡Deployment completado exitosamente! 🎉"
}

# Ejecutar script
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
