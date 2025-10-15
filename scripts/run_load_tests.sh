#!/bin/bash
# -*- coding: utf-8 -*-
#
# Script para ejecutar tests de carga (HTTP + WebSocket) en GRUPO_GAD
#
# Uso:
#   ./scripts/run_load_tests.sh [http|ws|all]
#
# Requisitos:
#   - k6 instalado
#   - API corriendo en localhost:8000
#   - Docker compose up (db, redis, api)

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
API_URL="${API_URL:-http://localhost:8000}"
WS_URL="${WS_URL:-ws://localhost:8000/ws/connect}"
RESULTS_DIR="scripts/load_test_results"

# ============================================================================
# FUNCIONES
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_requirements() {
    log_info "Verificando requisitos..."
    
    # Verificar k6
    if ! command -v k6 &> /dev/null; then
        log_error "k6 no está instalado"
        echo "Instalar: https://k6.io/docs/getting-started/installation/"
        exit 1
    fi
    log_success "k6 encontrado: $(k6 version | head -1)"
    
    # Verificar API
    if ! curl -sf "${API_URL}/health" > /dev/null 2>&1; then
        log_error "API no disponible en ${API_URL}"
        log_warning "Ejecutar: make up"
        exit 1
    fi
    log_success "API disponible en ${API_URL}"
}

create_results_dir() {
    mkdir -p "${RESULTS_DIR}"
    log_info "Directorio de resultados: ${RESULTS_DIR}"
}

run_http_test() {
    log_info "==================================================="
    log_info "  TEST DE CARGA HTTP - GRUPO_GAD API"
    log_info "==================================================="
    log_info "Endpoint: ${API_URL}"
    log_info "VUs: 20-100"
    log_info "Duración: ~4.5 minutos"
    echo ""
    
    API_URL="${API_URL}" k6 run \
        --out json="${RESULTS_DIR}/http_results.json" \
        scripts/load_test_http.js
    
    local EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "Test HTTP completado exitosamente"
    else
        log_error "Test HTTP falló con código: $EXIT_CODE"
    fi
    
    return $EXIT_CODE
}

run_ws_test() {
    log_info "==================================================="
    log_info "  TEST DE CARGA WEBSOCKET - GRUPO_GAD"
    log_info "==================================================="
    log_info "Endpoint: ${WS_URL}"
    log_info "Conexiones: 5-30 concurrentes"
    log_info "Duración: ~4.5 minutos"
    echo ""
    
    WS_URL="${WS_URL}" API_URL="${API_URL}" k6 run \
        --out json="${RESULTS_DIR}/ws_results.json" \
        scripts/load_test_ws.js
    
    local EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "Test WebSocket completado exitosamente"
    else
        log_error "Test WebSocket falló con código: $EXIT_CODE"
    fi
    
    return $EXIT_CODE
}

generate_summary() {
    log_info "==================================================="
    log_info "  RESUMEN DE RESULTADOS"
    log_info "==================================================="
    echo ""
    
    if [ -f "${RESULTS_DIR}/http_results.json" ]; then
        log_info "📊 HTTP Test Results:"
        echo "   - Archivo: ${RESULTS_DIR}/http_results.json"
    fi
    
    if [ -f "${RESULTS_DIR}/ws_results.json" ]; then
        log_info "📊 WebSocket Test Results:"
        echo "   - Archivo: ${RESULTS_DIR}/ws_results.json"
    fi
    
    if [ -f "scripts/load_test_http_results.json" ]; then
        log_info "📄 HTTP Summary: scripts/load_test_http_results.json"
    fi
    
    if [ -f "scripts/load_test_ws_results.json" ]; then
        log_info "📄 WebSocket Summary: scripts/load_test_ws_results.json"
    fi
    
    echo ""
    log_success "Tests de carga completados"
    log_info "Para análisis detallado, revisar archivos JSON en ${RESULTS_DIR}/"
}

show_usage() {
    echo "Uso: $0 [http|ws|all]"
    echo ""
    echo "Opciones:"
    echo "  http    - Ejecutar solo test HTTP"
    echo "  ws      - Ejecutar solo test WebSocket"
    echo "  all     - Ejecutar ambos tests (default)"
    echo ""
    echo "Variables de entorno:"
    echo "  API_URL - URL de la API (default: http://localhost:8000)"
    echo "  WS_URL  - URL WebSocket (default: ws://localhost:8000/ws/connect)"
    echo ""
    echo "Ejemplo:"
    echo "  API_URL=http://api.example.com $0 http"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    local TEST_TYPE="${1:-all}"
    
    if [ "$TEST_TYPE" = "-h" ] || [ "$TEST_TYPE" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    log_info "🚀 Iniciando tests de carga - GRUPO_GAD"
    echo ""
    
    check_requirements
    create_results_dir
    
    local HTTP_EXIT=0
    local WS_EXIT=0
    
    case "$TEST_TYPE" in
        http)
            run_http_test
            HTTP_EXIT=$?
            ;;
        ws)
            run_ws_test
            WS_EXIT=$?
            ;;
        all)
            run_http_test
            HTTP_EXIT=$?
            echo ""
            log_info "Esperando 10 segundos antes del test WebSocket..."
            sleep 10
            echo ""
            run_ws_test
            WS_EXIT=$?
            ;;
        *)
            log_error "Opción inválida: $TEST_TYPE"
            show_usage
            exit 1
            ;;
    esac
    
    echo ""
    generate_summary
    
    # Exit code: 0 si todos pasaron, 1 si alguno falló
    if [ $HTTP_EXIT -ne 0 ] || [ $WS_EXIT -ne 0 ]; then
        exit 1
    fi
    
    exit 0
}

main "$@"
