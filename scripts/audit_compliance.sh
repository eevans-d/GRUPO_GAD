#!/bin/bash
# GRUPO_GAD Compliance Audit Script v1.1

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    echo ""
    echo "======================================================================"
    echo " $1"
    echo "======================================================================"
}

# --- INICIO DE LA AUDITORÍA ---

print_header "1. Validación de Stack Inmutable y Estructura"
echo "Verificando versiones de dependencias en pyproject.toml..."
grep -E "fastapi|sqlalchemy|python-telegram-bot|pydantic|redis" pyproject.toml

echo "\nVerificando estructura de directorios críticos..."
CRITICAL_DIRS=$(find src/ -maxdepth 1 -type d \( -name "api" -o -name "bot" -o -name "core" -o -name "schemas" -o -name "shared" \) | wc -l)
if [ "$CRITICAL_DIRS" -eq 5 ]; then echo "[${GREEN}PASS${NC}] Estructura de directorios src/ OK"; else echo "[${RED}FAIL${NC}] Estructura de directorios src/ INCOMPLETA"; fi

echo "\nVerificando archivos críticos de configuración y dashboard..."
ls -la docker-compose.prod.yml .env.production Caddyfile dashboard/templates/admin_dashboard.html dashboard/static/dashboard.js


print_header "2. Validación de los 5 Elementos Críticos (API Endpoints)"

if ! command -v jq &> /dev/null; then
    echo "[${RED}FAIL${NC}] jq no está instalado. Por favor, instálalo para continuar."
    exit 1
fi

if [ -z "$DOMAIN" ] || [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASS" ] || [ -z "$TELEGRAM_TEST_ID" ]; then
    echo "[${YELLOW}SKIP${NC}] Variables de entorno no definidas. Saltando validaciones de API."
else
    echo "Obteniendo token de administrador..."
    TOKEN=$(curl -s -k -X POST -H "Content-Type: application/json" \
    "https://$DOMAIN/api/v1/auth/login" \
    -d '''{"email":"'''$ADMIN_EMAIL'''","password":"'''$ADMIN_PASS'''"}''' | jq -r '.access_token')

    if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
        echo "[${RED}FAIL${NC}] No se pudo obtener el token. Verifica credenciales y que el API esté online en https://$DOMAIN"
    else
        echo "[${GREEN}PASS${NC}] Token de administrador obtenido."
        
        echo "\n--- Testing Elemento 1: Mapeo Telegram ↔ UUID ---"
        curl -s -o /dev/null -w "HTTP %{http_code}\n" -k -H "Authorization: Bearer $TOKEN" "https://$DOMAIN/api/v1/users/by-telegram/$TELEGRAM_TEST_ID"

        echo "\n--- Testing Elemento 2: Emergencias con PostGIS ---"
        curl -s -o /dev/null -w "HTTP %{http_code}\n" -k -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST "https://$DOMAIN/api/v1/tasks/emergency" -d '''{"telegram_id":'''$TELEGRAM_TEST_ID''',"lat":-34.6037,"lng":-58.3816,"descripcion":"Test emergencia auditoria"}'''

        echo "\n--- Testing Elemento 3: Control Admin con Bypass ---"
        curl -s -o /dev/null -w "HTTP %{http_code}\n" -k -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST "https://$DOMAIN/api/v1/admin/agent/command" -d '''{"command":"SYSTEM_STATUS","admin_override":true}'''

        echo "\n--- Testing Elemento 5: Control Telegram ---"
        curl -s -o /dev/null -w "HTTP %{http_code}\n" -k -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST "https://$DOMAIN/api/v1/admin/telegram/send" -d '''{"group":"general","message":"[TEST] Auditoria cumplimiento OK","type":"normal"}'''
    fi
fi

echo "\n--- Testing Elemento 4: Scripts de Migración ---"
ls -la scripts/migration/analyze_legacy.py scripts/migration/migrate_users.py scripts/migration/rollback.sh


print_header "3. Validación PostGIS y Geolocalización"
if ! docker compose ps -q db &>/dev/null; then
    echo "[${YELLOW}SKIP${NC}] Contenedor 'db' no está en ejecución. Saltando validaciones de PostGIS."
else
    echo "Verificando versión de PostGIS..."
    docker compose exec -T db psql -U grupo_gad -d grupo_gad -c "SELECT PostGIS_version();"
    
    echo "\nVerificando SRID (debe ser 4326)..."
    SRID=$(docker compose exec -T db psql -U grupo_gad -d grupo_gad -tAc "SELECT Find_SRID('public','geo_locations','geom');")
    if [ "$SRID" = "4326" ]; then echo "[${GREEN}PASS${NC}] SRID es 4326"; else echo "[${RED}FAIL${NC}] SRID es $SRID"; fi

    echo "\nVerificando funciones críticas..."
    docker compose exec -T db psql -U grupo_gad -d grupo_gad -c "\df find_nearby_entities" | grep -q "find_nearby_entities" && echo "[${GREEN}PASS${NC}] Función find_nearby_entities existe" || echo "[${RED}FAIL${NC}] Función find_nearby_entities NO encontrada"
    docker compose exec -T db psql -U grupo_gad -d grupo_gad -c "\df calculate_route_distance" | grep -q "calculate_route_distance" && echo "[${GREEN}PASS${NC}] Función calculate_route_distance existe" || echo "[${RED}FAIL${NC}] Función calculate_route_distance NO encontrada"

    echo "\nVerificando vista materializada..."
    docker compose exec -T db psql -U grupo_gad -d grupo_gad -c "SELECT count(*) FROM mv_latest_locations;"
fi


print_header "4. Validación Dashboard Integrado"
if [ -z "$DOMAIN" ] || [ -z "$TOKEN" ]; then
    echo "[${YELLOW}SKIP${NC}] DOMAIN no definido o token no obtenido. Saltando validaciones de Dashboard."
else
    echo "--- Testing Dashboard Access ---"
    curl -s -o /dev/null -w "HTTP %{http_code}\n" -k -H "Authorization: Bearer $TOKEN" "https://$DOMAIN/dashboard"

    echo "\n--- Testing Static Files ---"
    curl -s -o /dev/null -w "HTTP %{http_code}\n" -k "https://$DOMAIN/static/dashboard.js"

    echo "\n--- Contando endpoints OpenAPI (debe ser >= 11) ---"
    ENDPOINT_COUNT=$(curl -fksS "https://$DOMAIN/api/v1/openapi.json" | jq '.paths | keys | length')
    echo "Total endpoints: $ENDPOINT_COUNT"
    if [ "$ENDPOINT_COUNT" -ge 11 ]; then echo "[${GREEN}PASS${NC}] Conteo de Endpoints OK"; else echo "[${RED}FAIL${NC}] Conteo de Endpoints INSUFICIENTE"; fi
fi

print_header "AUDITORÍA COMPLETADA"
