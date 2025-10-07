#!/usr/bin/env bash
# ----------------------------------------------------------------
# Nombre: post_deployment_verification.sh
# Descripción: Script de verificación post-despliegue para GRUPO_GAD
# Autor: GRUPO_GAD
# Fecha: 2025-10-07
# Versión: 1.0
# ----------------------------------------------------------------

# Configuración de colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuración de variables
DOMAIN=${DOMAIN:-"grupogad.com"}
API_URL=${API_URL:-"https://api.${DOMAIN}"}
TIMEOUT=${TIMEOUT:-30}
COMPOSE_FILE=${COMPOSE_FILE:-"docker-compose.yml"}
COMPOSE_PROD_FILE=${COMPOSE_PROD_FILE:-"docker-compose.prod.yml"}

# Contadores para el resumen
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Arrays para almacenar resultados
declare -a FAILED_TESTS
declare -a WARNING_TESTS

# Función para imprimir mensajes con formato
print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}======================================================================"
    echo -e "    $1"
    echo -e "======================================================================${NC}"
}

print_step() {
    echo -e "${BLUE}➤${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED_CHECKS++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED_CHECKS++))
    FAILED_TESTS+=("$1")
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNING_CHECKS++))
    WARNING_TESTS+=("$1")
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Función para incrementar el contador total
increment_total() {
    ((TOTAL_CHECKS++))
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para realizar peticiones HTTP con timeout
http_check() {
    local url="$1"
    local expected_status="${2:-200}"
    local description="$3"
    
    increment_total
    print_step "Verificando: $description ($url)"
    
    if command_exists curl; then
        local response
        response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT --max-time $TIMEOUT "$url" 2>/dev/null)
        
        if [ "$response" = "$expected_status" ]; then
            print_success "$description - Estado HTTP: $response"
            return 0
        else
            print_error "$description - Estado HTTP esperado: $expected_status, obtenido: $response"
            return 1
        fi
    else
        print_warning "curl no está disponible, saltando verificación HTTP: $description"
        return 2
    fi
}

# Función para verificar servicios Docker
check_docker_service() {
    local service_name="$1"
    local description="$2"
    
    increment_total
    print_step "Verificando servicio Docker: $service_name"
    
    if ! command_exists docker; then
        print_error "Docker no está instalado o no está en el PATH"
        return 1
    fi
    
    local status
    status=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD_FILE" ps --format "table {{.Service}}\t{{.State}}" 2>/dev/null | grep "^$service_name" | awk '{print $2}')
    
    if [ "$status" = "running" ]; then
        print_success "$description está ejecutándose"
        return 0
    elif [ -z "$status" ]; then
        print_error "$description no encontrado en docker-compose"
        return 1
    else
        print_error "$description no está ejecutándose (estado: $status)"
        return 1
    fi
}

# Función para verificar puertos
check_port() {
    local host="$1"
    local port="$2"
    local description="$3"
    
    increment_total
    print_step "Verificando conectividad: $description ($host:$port)"
    
    if command_exists nc; then
        if nc -z -w$TIMEOUT "$host" "$port" 2>/dev/null; then
            print_success "$description está accesible en $host:$port"
            return 0
        else
            print_error "$description no está accesible en $host:$port"
            return 1
        fi
    elif command_exists telnet; then
        if timeout $TIMEOUT telnet "$host" "$port" </dev/null &>/dev/null; then
            print_success "$description está accesible en $host:$port"
            return 0
        else
            print_error "$description no está accesible en $host:$port"
            return 1
        fi
    else
        print_warning "ni nc ni telnet están disponibles, saltando verificación de puerto: $description"
        return 2
    fi
}

# Función para verificar DNS
check_dns() {
    local domain="$1"
    local description="$2"
    
    increment_total
    print_step "Verificando resolución DNS: $domain"
    
    if command_exists dig; then
        local result
        result=$(dig +short "$domain" 2>/dev/null)
        if [ -n "$result" ]; then
            print_success "DNS para $domain resuelve a: $result"
            return 0
        else
            print_error "DNS para $domain no resuelve"
            return 1
        fi
    elif command_exists nslookup; then
        if nslookup "$domain" >/dev/null 2>&1; then
            print_success "DNS para $domain resuelve correctamente"
            return 0
        else
            print_error "DNS para $domain no resuelve"
            return 1
        fi
    else
        print_warning "ni dig ni nslookup están disponibles, saltando verificación DNS: $domain"
        return 2
    fi
}

# Función para verificar certificados SSL
check_ssl() {
    local domain="$1"
    local description="$2"
    
    increment_total
    print_step "Verificando certificado SSL: $domain"
    
    if command_exists openssl; then
        local cert_info
        cert_info=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" -verify_return_error 2>/dev/null)
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            local expiry
            expiry=$(echo "$cert_info" | openssl x509 -noout -dates 2>/dev/null | grep "notAfter" | cut -d= -f2)
            print_success "Certificado SSL válido para $domain (expira: $expiry)"
            return 0
        else
            print_error "Certificado SSL inválido o no encontrado para $domain"
            return 1
        fi
    else
        print_warning "openssl no está disponible, saltando verificación SSL: $domain"
        return 2
    fi
}

# Función para verificar logs de Docker
check_docker_logs() {
    local service_name="$1"
    local description="$2"
    local error_patterns="$3"
    
    increment_total
    print_step "Verificando logs de $service_name en busca de errores"
    
    if ! command_exists docker; then
        print_warning "Docker no está disponible, saltando verificación de logs"
        return 2
    fi
    
    local logs
    logs=$(docker compose -f "$COMPOSE_FILE" -f "$COMPOSE_PROD_FILE" logs --tail=100 "$service_name" 2>/dev/null)
    
    if [ -z "$logs" ]; then
        print_warning "No se pudieron obtener logs para $service_name"
        return 2
    fi
    
    # Buscar patrones de error comunes
    local error_found=false
    for pattern in $error_patterns; do
        if echo "$logs" | grep -i "$pattern" >/dev/null 2>&1; then
            print_error "Encontrado patrón de error '$pattern' en logs de $service_name"
            error_found=true
        fi
    done
    
    if [ "$error_found" = false ]; then
        print_success "No se encontraron errores evidentes en logs de $service_name"
        return 0
    else
        return 1
    fi
}

# Función para verificar métricas de Prometheus
check_prometheus_metrics() {
    local metrics_url="$1"
    
    increment_total
    print_step "Verificando disponibilidad de métricas Prometheus"
    
    if command_exists curl; then
        local response
        response=$(curl -s --connect-timeout $TIMEOUT --max-time $TIMEOUT "$metrics_url" 2>/dev/null)
        
        if echo "$response" | grep -q "TYPE.*gauge\|TYPE.*counter\|TYPE.*histogram"; then
            local metric_count
            metric_count=$(echo "$response" | grep -c "^# TYPE")
            print_success "Métricas Prometheus disponibles ($metric_count tipos de métricas encontrados)"
            return 0
        else
            print_error "Métricas Prometheus no disponibles o formato incorrecto"
            return 1
        fi
    else
        print_warning "curl no está disponible, saltando verificación de métricas"
        return 2
    fi
}

# Función principal de verificación
main() {
    print_header "VERIFICACIÓN POST-DESPLIEGUE - GRUPO_GAD"
    print_info "Fecha: $(date)"
    print_info "Dominio: $DOMAIN"
    print_info "URL API: $API_URL"
    print_info "Timeout: ${TIMEOUT}s"
    echo ""

    # 1. Verificar servicios Docker
    print_header "1. VERIFICACIÓN DE SERVICIOS DOCKER"
    check_docker_service "api" "Servicio API"
    check_docker_service "db" "Base de datos PostgreSQL"
    check_docker_service "redis" "Servicio Redis"
    check_docker_service "caddy" "Servidor web Caddy"
    check_docker_service "bot" "Bot de Telegram"

    # 2. Verificar conectividad de red
    print_header "2. VERIFICACIÓN DE CONECTIVIDAD"
    check_port "localhost" "80" "Puerto HTTP (80)"
    check_port "localhost" "443" "Puerto HTTPS (443)"
    check_port "localhost" "5432" "Puerto PostgreSQL (5432)"
    check_port "localhost" "6379" "Puerto Redis (6379)"

    # 3. Verificar DNS
    print_header "3. VERIFICACIÓN DNS"
    check_dns "$DOMAIN" "Dominio principal"
    check_dns "api.$DOMAIN" "Subdominio API"
    check_dns "admin.$DOMAIN" "Subdominio Admin"

    # 4. Verificar SSL/TLS
    print_header "4. VERIFICACIÓN SSL/TLS"
    check_ssl "$DOMAIN" "Certificado del dominio principal"
    check_ssl "api.$DOMAIN" "Certificado del subdominio API"

    # 5. Verificar endpoints HTTP
    print_header "5. VERIFICACIÓN DE ENDPOINTS HTTP"
    http_check "$API_URL/health" "200" "Health check de la API"
    http_check "$API_URL/metrics" "200" "Endpoint de métricas"
    http_check "$API_URL/docs" "200" "Documentación de la API (Swagger)"
    http_check "https://$DOMAIN" "200" "Página principal"

    # 6. Verificar métricas
    print_header "6. VERIFICACIÓN DE MÉTRICAS"
    check_prometheus_metrics "$API_URL/metrics"

    # 7. Verificar logs de servicios
    print_header "7. VERIFICACIÓN DE LOGS"
    check_docker_logs "api" "API" "error fatal exception traceback"
    check_docker_logs "db" "Base de datos" "error fatal could_not_connect"
    check_docker_logs "caddy" "Caddy" "error failed timeout"

    # 8. Resumen final
    print_header "8. RESUMEN DE VERIFICACIÓN"
    
    echo ""
    print_info "Total de verificaciones: $TOTAL_CHECKS"
    print_success "Verificaciones exitosas: $PASSED_CHECKS"
    print_warning "Advertencias: $WARNING_CHECKS"
    print_error "Verificaciones fallidas: $FAILED_CHECKS"
    
    echo ""
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        print_success "🎉 TODAS LAS VERIFICACIONES PASARON CORRECTAMENTE"
        if [ $WARNING_CHECKS -gt 0 ]; then
            print_warning "Hay $WARNING_CHECKS advertencias que deberías revisar"
        fi
        echo ""
        print_info "El sistema está listo para producción ✅"
        exit 0
    else
        print_error "❌ $FAILED_CHECKS VERIFICACIONES FALLARON"
        echo ""
        print_info "Verificaciones fallidas:"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}•${NC} $test"
        done
        
        if [ $WARNING_CHECKS -gt 0 ]; then
            echo ""
            print_info "Advertencias:"
            for test in "${WARNING_TESTS[@]}"; do
                echo -e "  ${YELLOW}•${NC} $test"
            done
        fi
        
        echo ""
        print_info "Por favor, revisa y corrige los problemas antes de continuar"
        exit 1
    fi
}

# Verificar argumentos de línea de comandos
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            API_URL="https://api.$DOMAIN"
            shift 2
            ;;
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --help)
            echo "Uso: $0 [opciones]"
            echo ""
            echo "Opciones:"
            echo "  --domain DOMAIN     Dominio principal (por defecto: grupogad.com)"
            echo "  --api-url URL       URL de la API (por defecto: https://api.DOMAIN)"
            echo "  --timeout SECONDS   Timeout para conexiones (por defecto: 30)"
            echo "  --help              Mostrar esta ayuda"
            echo ""
            exit 0
            ;;
        *)
            echo "Opción desconocida: $1"
            echo "Usa --help para ver las opciones disponibles"
            exit 1
            ;;
    esac
done

# Ejecutar verificación principal
main