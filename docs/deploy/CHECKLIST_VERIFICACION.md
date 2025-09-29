# CHECKLIST DE VERIFICACIÓN PRE-DESPLIEGUE CONDICIONAL

**Generado por**: Prompt Pasivo B - Checklist Verificación  
**Fecha**: {{ timestamp }}  
**Principio**: **EL DESPLIEGUE SOLO ES POSIBLE SI TODAS LAS CONDICIONES CRÍTICAS ESTÁN VERIFICADAS**

## NIVEL 1: INFRAESTRUCTURA MÍNIMA ⚠️

### ✅ Base de Datos PostGIS
```bash
# Verificar PostGIS instalado y funcional
docker compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT PostGIS_version();"
# Debe retornar: POSTGIS="3.4.x ..." 
# Si falla: NO DESPLEGAR
```
**Estado actual**: 🟢 PASS - PostGIS configurado en docker-compose.yml línea 5

### ✅ Redis Accesibilidad (Opcional)
```bash
# Verificar Redis responde
docker compose exec redis redis-cli PING
# Debe retornar: PONG
# Si falla pero no se usa: WARN, OK continuar
```
**Estado actual**: 🟢 PASS - Redis configurado pero opcional

### ✅ Secrets No en Repositorio
```bash
# Buscar secrets expuestos
git grep -i "CHANGEME\|sk-\|bot:[0-9]\|password.*=" | grep -v ".example\|.md:"
# Debe retornar: vacío
# Si encuentra algo: NO DESPLEGAR
```
**Estado actual**: 🟢 PASS - No se encontraron secrets hardcodeados

## NIVEL 2: CONFIGURACIÓN CONSISTENTE ⚠️

### ❌ Una Sola Fuente de Verdad para Settings
```bash
# Verificar no hay múltiples configs
find . -name "config.py" -o -name "settings.py" | grep -v __pycache__ | grep -v test
# Debe retornar: solo ./config/settings.py
# Si hay más: RESOLVER conflictos antes de desplegar
```
**Estado actual**: 🔴 FAIL - Encontrado: `./config/settings.py` y `./src/app/core/config.py`  
**Acción requerida**: Eliminar `src/app/core/config.py` y migrar imports

### ✅ Variables de Entorno Completas
```bash
# Comparar .env.example con variables usadas en código
grep -h "getenv\|env\[" src/**/*.py config/*.py | grep -o '"[^"]*"' | sort -u > /tmp/used_vars
grep "^[A-Z]" .env.example | cut -d= -f1 | sort > /tmp/example_vars
diff /tmp/used_vars /tmp/example_vars
# Debe ser minimal difference
```
**Estado actual**: 🟡 REVIEW - Revisar manualmente variables críticas

## NIVEL 3: FUNCIONALIDAD CRÍTICA VALIDADA ⚠️

### ❌ Endpoint de Emergencia
```bash
# Buscar endpoint específico de emergencia con PostGIS
grep -r "/emergency\|emergency" src/api/routers/
# Debe existir router que use PostGIS para asignación inmediata
```
**Estado actual**: 🔴 FAIL - No hay endpoint específico /emergency  
**Acción requerida**: Implementar endpoint crítico antes de desplegar

### ❌ Webhook Telegram Configurado
```bash
# Verificar implementación de webhook para producción
grep -r "set_webhook\|webhook" src/bot/
# Debe existir para ambiente de producción
```
**Estado actual**: 🔴 FAIL - Solo polling, no webhook  
**Acción requerida**: Implementar webhook antes de despliegue en producción

### ✅ Healthcheck Robusto
```bash
# Verificar healthcheck valida componentes críticos
curl -f http://localhost:8000/api/v1/health
curl -f http://localhost:8000/metrics
# Ambos deben retornar 200 con datos de DB y WebSocket
```
**Estado actual**: 🟢 PASS - Health endpoint implementado

## NIVEL 4: OBSERVABILIDAD MÍNIMA ⚠️

### ⚠️ Métricas Técnicas
```bash
# Verificar métricas de producción disponibles
curl -s http://localhost:8000/metrics | grep -E "request_latency|error_count|db_query_time"
# Debe exponer métricas críticas de rendimiento
```
**Estado actual**: 🟡 PARTIAL - Métricas básicas, faltan específicas de DB y latencia

### ✅ Logs Estructurados
```bash
# Verificar configuración de logs para producción
grep -r "json.*log\|structured.*log" src/core/logging.py
# Debe configurar JSON logging en producción
```
**Estado actual**: 🟢 PASS - Logging estructurado configurado en `src/core/logging.py:65`

## NIVEL 5: SCRIPTS DE INICIO Y MIGRACIÓN ❌

### ❌ Script de Inicio Automático
```bash
# Verificar script de inicialización
ls scripts/start.sh
# Debe existir y contener: alembic upgrade head
```
**Estado actual**: 🔴 CRITICAL - No existe `scripts/start.sh`  
**Acción requerida**: Crear script antes de cualquier despliegue

### ✅ Migraciones Funcionales
```bash
# Verificar migraciones están al día
alembic current
alembic check
# Debe mostrar estado actual sin errores
```
**Estado actual**: 🟢 PASS - Migraciones Alembic configuradas

## RESUMEN EJECUTIVO

| Nivel | Items Verificados | Passed | Failed | Warnings |
|-------|------------------|--------|--------|----------|
| Infraestructura | 3 | 3 | 0 | 0 |
| Configuración | 2 | 1 | 1 | 1 |
| Funcionalidad | 3 | 1 | 2 | 0 |
| Observabilidad | 2 | 1 | 0 | 1 |
| Scripts | 2 | 1 | 1 | 0 |
| **TOTAL** | **12** | **7** | **4** | **2** |

## ⛔ DECISIÓN DE DESPLIEGUE

**ESTADO**: 🔴 **NO APTO PARA DESPLIEGUE**

**BLOCKERS CRÍTICOS**:
1. ❌ Configuración dual no resuelta
2. ❌ Endpoint /emergency no implementado  
3. ❌ Webhook Telegram no configurado
4. ❌ Script de inicio missing

**ACCIONES OBLIGATORIAS ANTES DE DESPLEGAR**:
1. Resolver configuración dual eliminando `src/app/core/config.py`
2. Implementar endpoint `/api/v1/emergency` con PostGIS
3. Configurar webhook Telegram para producción
4. Crear `scripts/start.sh` con migraciones automáticas

**ESTE CHECKLIST DEBE EJECUTARSE ANTES DE CADA DESPLIEGUE**  
**Solo cuando todos los items sean 🟢 PASS se permite desplegar**

---
**Validación ejecutada**: {{ timestamp }}  
**Próxima validación requerida**: antes del siguiente despliegue