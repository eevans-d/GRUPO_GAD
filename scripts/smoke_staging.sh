#!/bin/bash
#
# Script de Smoke Tests para validar despliegues en Staging de GRUPO_GAD.
set -euo pipefail # Salir en caso de error, variable no definida o fallo en pipe

# --- Configuración ---
# Las credenciales y el dominio se leen de variables de entorno para mayor seguridad.
# Ejemplo de cómo ejecutarlo:
# STAGING_DOMAIN="staging.tu-dominio.com" \
# STAGING_ADMIN_EMAIL="admin@grupo-gad.com" \
# STAGING_ADMIN_PASS="tu_pass_segura" \
# ./scripts/smoke_staging.sh

DOMAIN="${STAGING_DOMAIN?La variable STAGING_DOMAIN no está definida}"
ADMIN_EMAIL="${STAGING_ADMIN_EMAIL?La variable STAGING_ADMIN_EMAIL no está definida}"
ADMIN_PASS="${STAGING_ADMIN_PASS?La variable STAGING_ADMIN_PASS no está definida}"

# Verificación de que jq está instalado
command -v jq >/dev/null 2>&1 || { echo >&2 "Este script requiere 'jq' pero no está instalado. Abortando."; exit 1; }

# Contadores para el resumen final
TOTAL_TESTS=0
PASSED_TESTS=0

# Archivo temporal para guardar las respuestas
RESPONSE_FILE=$(mktemp)

# --- Funciones de Ayuda ---

# Función para limpiar y salir en caso de error fatal
cleanup_and_exit() {
    echo "--------------------------------------------------"
    echo "ERROR FATAL: $1"
    echo "Código de respuesta: $2"
    echo "Cuerpo de la respuesta:"
    cat "$RESPONSE_FILE"
    echo
    echo "--------------------------------------------------"
    rm -f "$RESPONSE_FILE"
    exit 1
}

# Función principal para ejecutar una prueba
run_test() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_codes="$4"
    local data="$5"
    
    ((TOTAL_TESTS++))
    echo -n "🧪 Ejecutando test: '$test_name'... "

    local full_url="https://$DOMAIN$endpoint"
    local curl_opts=("-s" "-w" "%{http_code}" "-o" "$RESPONSE_FILE")
    
    if [ -n "$ACCESS_TOKEN" ]; then
        curl_opts+=("-H" "Authorization: Bearer $ACCESS_TOKEN")
    fi

    if [ "$method" == "POST" ]; then
        curl_opts+=("-X" "POST" "-H" "Content-Type: application/json" "-d" "$data")
    else
        curl_opts+=("-X" "GET")
    fi

    HTTP_CODE=$(curl "${curl_opts[@]}" "$full_url")

    # Fallo fatal en errores 5xx
    if [[ "$HTTP_CODE" -ge 500 ]]; then
        cleanup_and_exit "Error de servidor (5xx)." "$HTTP_CODE"
    fi

    # Verificación de códigos de respuesta esperados
    if [[ "$expected_codes" =~ "$HTTP_CODE" ]]; then
        ((PASSED_TESTS++))
        echo "✅ PASS ($HTTP_CODE)"
        return 0
    else
        echo "❌ FAIL"
        echo "   - Esperado: $expected_codes, Obtenido: $HTTP_CODE"
        echo "   - Endpoint: $method $full_url"
        echo "   - Respuesta:"
        cat "$RESPONSE_FILE"
        echo
        return 1
    fi
}

# --- Secuencia de Pruebas ---

echo "🚀 Iniciando Smoke Tests para $DOMAIN"
echo "--------------------------------------------------"

# 1. Autenticación
echo "🔑 Obteniendo token de autenticación..."
AUTH_DATA='''{"username": "'$ADMIN_EMAIL'", "password": "'$ADMIN_PASS'"}'''
HTTP_CODE=$(curl -s -w "%{http_code}" -o "$RESPONSE_FILE" -X POST -H "Content-Type: application/json" -d "$AUTH_DATA" "https://$DOMAIN/auth/login")

if [ "$HTTP_CODE" -ne 200 ]; then
    cleanup_and_exit "Fallo de autenticación." "$HTTP_CODE"
fi

ACCESS_TOKEN=$(jq -r .access_token < "$RESPONSE_FILE")
if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
    cleanup_and_exit "No se pudo extraer el access_token." "$HTTP_CODE"
fi
echo "Token obtenido exitosamente."
echo "--------------------------------------------------"

# 2. Obtener datos del usuario 'me' y extraer UUID
run_test "Obtener usuario actual" "GET" "/users/me" "200"
USER_UUID=$(jq -r .uuid < "$RESPONSE_FILE")
if [ -z "$USER_UUID" ] || [ "$USER_UUID" == "null" ]; then
    cleanup_and_exit "No se pudo extraer el UUID del usuario desde /users/me." "200"
fi
echo "   -> UUID de usuario para pruebas: $USER_UUID"

# 3. Endpoints críticos
run_test "Buscar usuario por Telegram ID" "GET" "/users/by-telegram/123456789" "200 404"
run_test "Crear emergencia" "POST" "/tasks/emergency" "200 400 404" '''{"telegram_id":123456789,"lat":-34.6037,"lng":-58.3816}'''
run_test "Actualizar ubicación de usuario" "POST" "/geo/location/usuario/$USER_UUID" "200" '''{"lat":-34.5997,"lng":-58.3819,"source":"MANUAL"}'''
run_test "Ver vista de mapa" "GET" "/geo/map/view?center_lat=-34.6&center_lng=-58.3&radius_m=10000" "200"
run_test "Enviar mensaje de Telegram" "POST" "/admin/telegram/send" "200" '''{"group":"general","message":"Test staging OK","type":"normal"}'''

# --- Resumen Final ---
echo "--------------------------------------------------"
echo "🏁 Smoke Tests finalizados."
echo "Resumen: $PASSED_TESTS / $TOTAL_TESTS tests superados."
rm -f "$RESPONSE_FILE"

if [ "$PASSED_TESTS" -ne "$TOTAL_TESTS" ]; then
    echo "🔴 Algunos tests fallaron."
    exit 1
else
    echo "🟢 Todos los tests pasaron exitosamente."
    exit 0
fi
