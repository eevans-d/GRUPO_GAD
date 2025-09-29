# GUÍA DE TROUBLESHOOTING Y MANTENIMIENTO - GRUPO_GAD

## 1. PROBLEMAS COMUNES DE DESPLIEGUE

### Top 5 Errores Más Probables Durante Deployment

#### Error 1: Database Connection Failed
**Síntomas:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "db" (172.18.0.2), port 5432 failed
```

**Solución Paso a Paso:**
```bash
# 1. Verificar que PostgreSQL está corriendo
docker compose ps db
# Debe mostrar: "Up" y "healthy"

# 2. Verificar variables de entorno
echo $DATABASE_URL
echo $POSTGRES_USER
echo $POSTGRES_PASSWORD

# 3. Probar conexión manual
docker compose exec api python -c "
from config.settings import settings
print('Database URL:', settings.DATABASE_URL)
"

# 4. Verificar conectividad desde contenedor
docker compose exec api pg_isready -h db -p 5432 -U $POSTGRES_USER

# 5. Si falla, reiniciar servicios de BD
docker compose down db
docker compose up -d db
# Esperar 30 segundos para que inicie completamente
```

**Logs a Revisar:**
```bash
# Logs de PostgreSQL
docker compose logs db | tail -50

# Logs de la API
docker compose logs api | grep -i "database\|connection"
```

#### Error 2: JWT Secret Key Invalid
**Síntomas:**
```
pydantic_core._pydantic_core.ValidationError: SECRET_KEY [env var: 'SECRET_KEY']
Input should be a valid string [type=string_type, input=ValueType.null]
```

**Solución Paso a Paso:**
```bash
# 1. Verificar que SECRET_KEY existe
echo $SECRET_KEY
# No debe estar vacío

# 2. Generar nueva SECRET_KEY si es necesario
openssl rand -hex 32

# 3. Actualizar en .env.production
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env.production

# 4. Reiniciar aplicación
docker compose restart api
```

**Comando de Diagnóstico:**
```bash
docker compose exec api python -c "
from config.settings import settings
print('Secret key length:', len(settings.SECRET_KEY) if settings.SECRET_KEY else 'NONE')
print('Secret key starts with:', settings.SECRET_KEY[:8] if settings.SECRET_KEY else 'NONE')
"
```

#### Error 3: Port Already in Use
**Síntomas:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```

**Solución Paso a Paso:**
```bash
# 1. Identificar proceso usando el puerto
lsof -i :8000
# O en sistemas sin lsof:
netstat -tulpn | grep :8000

# 2. Detener proceso conflictivo
kill -9 <PID>

# 3. O cambiar puerto en docker-compose
# Editar puerto en docker-compose.prod.yml:
#   ports:
#     - "8001:8000"  # Puerto externo:interno

# 4. Reiniciar servicios
docker compose down
docker compose up -d
```

#### Error 4: Alembic Migration Failed
**Síntomas:**
```
alembic.util.exc.CommandError: Target database is not up to date.
sqlalchemy.exc.ProgrammingError: relation "users" does not exist
```

**Solución Paso a Paso:**
```bash
# 1. Verificar estado actual de migraciones
docker compose exec api alembic current

# 2. Ver historial de migraciones
docker compose exec api alembic history --verbose

# 3. Si la BD está vacía, ejecutar todas las migraciones
docker compose exec api alembic upgrade head

# 4. Si hay conflictos, hacer downgrade y upgrade
docker compose exec api alembic downgrade -1
docker compose exec api alembic upgrade head

# 5. En casos extremos, reset completo (SOLO DEVELOPMENT)
# docker compose down -v  # Elimina volúmenes
# docker compose up -d db
# docker compose exec api alembic upgrade head
```

**Logs Exactos a Revisar:**
```bash
# Logs de migraciones
docker compose logs api | grep -i "alembic\|migration"

# Estado de tablas en BD
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"
```

#### Error 5: FastAPI Import Error
**Síntomas:**
```
ModuleNotFoundError: No module named 'src.api.main'
ImportError: cannot import name 'app' from 'src.api.main'
```

**Solución Paso a Paso:**
```bash
# 1. Verificar estructura de archivos
docker compose exec api ls -la src/api/

# 2. Verificar PYTHONPATH
docker compose exec api python -c "import sys; print(sys.path)"

# 3. Probar imports manualmente
docker compose exec api python -c "
try:
    from src.api.main import app
    print('✅ Import successful')
except Exception as e:
    print('❌ Import failed:', str(e))
"

# 4. Verificar dependencias instaladas
docker compose exec api pip list | grep fastapi

# 5. Rebuilder imagen si es necesario
docker compose build --no-cache api
docker compose up -d api
```

### Comandos Específicos de Diagnóstico

#### Health Check Completo
```bash
#!/bin/bash
# scripts/health_check.sh

echo "=== HEALTH CHECK GRUPO_GAD ==="

# 1. Verificar servicios Docker
echo "🐳 Docker Services:"
docker compose ps

# 2. Verificar conectividad de red
echo "🌐 Network Connectivity:"
docker compose exec api ping -c 2 db
docker compose exec api ping -c 2 redis

# 3. Verificar endpoints críticos
echo "🔍 API Endpoints:"
curl -f http://localhost:8000/api/v1/health || echo "❌ Health endpoint failed"
curl -f http://localhost:8000/metrics || echo "❌ Metrics endpoint failed"

# 4. Verificar base de datos
echo "📊 Database Status:"
docker compose exec db pg_isready -U $POSTGRES_USER

# 5. Verificar logs recientes por errores
echo "📋 Recent Errors:"
docker compose logs --since=5m api | grep -i "error\|exception\|failed" | tail -5
```

#### Estado de WebSockets
```bash
# Verificar conexiones WebSocket activas
curl -s http://localhost:8000/ws/stats | jq '.'

# Probar conexión WebSocket
# Instalar wscat si no está disponible: npm install -g wscat
echo "Testing WebSocket connection..."
timeout 10s wscat -c ws://localhost:8000/ws/connect || echo "WebSocket connection failed"
```

### Señales de Alerta Temprana

#### Script de Monitoreo de Métricas
```bash
#!/bin/bash
# scripts/early_warning.sh

# Umbrales de alerta
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
RESPONSE_TIME_THRESHOLD=2000  # ms

echo "🚨 EARLY WARNING SYSTEM - GRUPO_GAD"

# 1. CPU Usage
CPU_USAGE=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}" | grep api | awk '{print $2}' | sed 's/%//')
if (( $(echo "$CPU_USAGE > $CPU_THRESHOLD" | bc -l) )); then
    echo "⚠️  HIGH CPU: ${CPU_USAGE}% (Threshold: ${CPU_THRESHOLD}%)"
fi

# 2. Memory Usage
MEMORY_USAGE=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemPerc}}" | grep api | awk '{print $2}' | sed 's/%//')
if (( $(echo "$MEMORY_USAGE > $MEMORY_THRESHOLD" | bc -l) )); then
    echo "⚠️  HIGH MEMORY: ${MEMORY_USAGE}% (Threshold: ${MEMORY_THRESHOLD}%)"
fi

# 3. Disk Usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if (( DISK_USAGE > DISK_THRESHOLD )); then
    echo "⚠️  HIGH DISK: ${DISK_USAGE}% (Threshold: ${DISK_THRESHOLD}%)"
fi

# 4. Response Time
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/api/v1/health | awk '{print $1*1000}')
if (( $(echo "$RESPONSE_TIME > $RESPONSE_TIME_THRESHOLD" | bc -l) )); then
    echo "⚠️  SLOW RESPONSE: ${RESPONSE_TIME}ms (Threshold: ${RESPONSE_TIME_THRESHOLD}ms)"
fi

# 5. Database Connections
DB_CONNECTIONS=$(docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT count(*) FROM pg_stat_activity;" -t | xargs)
if (( DB_CONNECTIONS > 15 )); then
    echo "⚠️  HIGH DB CONNECTIONS: ${DB_CONNECTIONS} (Max recommended: 15)"
fi

echo "✅ Early warning check completed"
```

## 2. COMANDOS DE MANTENIMIENTO ESENCIALES

### Health Checks Específicos

#### Health Check de Sistema Completo
```bash
#!/bin/bash
# scripts/system_health_check.sh

echo "🏥 SISTEMA DE SALUD - GRUPO_GAD"
echo "==============================="

# Función para logging con timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 1. Verificar servicios críticos
log_with_timestamp "Verificando servicios Docker..."
services_status=$(docker compose ps --format json | jq -r '.[] | "\(.Name): \(.State)"')
echo "$services_status"

# 2. Verificar conectividad de red interna
log_with_timestamp "Verificando conectividad de red..."
if docker compose exec api ping -c 1 db >/dev/null 2>&1; then
    echo "✅ API -> Database: OK"
else
    echo "❌ API -> Database: FAILED"
fi

if docker compose exec api ping -c 1 redis >/dev/null 2>&1; then
    echo "✅ API -> Redis: OK"
else
    echo "❌ API -> Redis: FAILED"
fi

# 3. Verificar endpoints de salud
log_with_timestamp "Verificando endpoints de API..."
health_response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health)
if [ "$health_response" = "200" ]; then
    echo "✅ Health endpoint: OK"
else
    echo "❌ Health endpoint: FAILED (Code: $health_response)"
fi

# 4. Verificar base de datos
log_with_timestamp "Verificando base de datos..."
if docker compose exec db pg_isready -U $POSTGRES_USER >/dev/null 2>&1; then
    echo "✅ PostgreSQL: Ready"
    
    # Verificar migraciones
    migration_status=$(docker compose exec api alembic current 2>/dev/null | tail -1)
    echo "📊 Migration status: $migration_status"
else
    echo "❌ PostgreSQL: Not ready"
fi

# 5. Verificar recursos del sistema
log_with_timestamp "Verificando recursos del sistema..."
df -h | head -2
free -h | head -2

echo "==============================="
log_with_timestamp "Health check completado"
```

### Comandos para Restart de Servicios

#### Restart Inteligente de Servicios
```bash
#!/bin/bash
# scripts/intelligent_restart.sh

SERVICE=${1:-"all"}
BACKUP_BEFORE_RESTART=${2:-"yes"}

echo "🔄 RESTART INTELIGENTE - GRUPO_GAD"
echo "Servicio: $SERVICE"
echo "Backup antes de restart: $BACKUP_BEFORE_RESTART"

# Función para backup antes de restart
perform_backup() {
    if [ "$BACKUP_BEFORE_RESTART" = "yes" ]; then
        echo "💾 Realizando backup preventivo..."
        timestamp=$(date +"%Y%m%d_%H%M%S")
        
        # Backup de base de datos
        docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > "backup_pre_restart_${timestamp}.sql"
        
        # Backup de configuración
        cp .env.production "backup_env_${timestamp}.txt"
        
        echo "✅ Backup completado: backup_pre_restart_${timestamp}.sql"
    fi
}

# Restart específico por servicio
restart_api() {
    echo "🔄 Restarting API service..."
    perform_backup
    
    # Graceful shutdown
    docker compose exec api pkill -SIGTERM python || true
    sleep 5
    
    # Restart container
    docker compose restart api
    
    # Wait for health check
    echo "⏳ Esperando que API esté disponible..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
            echo "✅ API restarted successfully"
            return 0
        fi
        sleep 2
    done
    echo "❌ API restart failed or taking too long"
    return 1
}

restart_db() {
    echo "🔄 Restarting Database service..."
    perform_backup
    
    # Graceful shutdown de conexiones
    docker compose exec api python -c "
from src.core.database import async_engine
import asyncio
async def close_connections():
    if async_engine:
        await async_engine.dispose()
asyncio.run(close_connections())
" 2>/dev/null || true

    # Restart PostgreSQL
    docker compose restart db
    
    # Wait for database to be ready
    echo "⏳ Esperando que PostgreSQL esté disponible..."
    for i in {1..30}; do
        if docker compose exec db pg_isready -U $POSTGRES_USER >/dev/null 2>&1; then
            echo "✅ Database restarted successfully"
            return 0
        fi
        sleep 2
    done
    echo "❌ Database restart failed or taking too long"
    return 1
}

restart_all() {
    echo "🔄 Restarting all services..."
    perform_backup
    
    # Ordenado: API -> Redis -> DB -> API
    docker compose restart redis
    sleep 5
    
    restart_db
    sleep 10
    
    restart_api
}

# Ejecutar restart según parámetro
case $SERVICE in
    "api")
        restart_api
        ;;
    "db"|"database")
        restart_db
        ;;
    "redis")
        docker compose restart redis
        ;;
    "all")
        restart_all
        ;;
    *)
        echo "❌ Servicio no válido. Use: api, db, redis, all"
        exit 1
        ;;
esac
```

### Update de Dependencias Seguro

#### Script de Actualización de Dependencias
```bash
#!/bin/bash
# scripts/safe_dependency_update.sh

BACKUP_DIR="backups/dependency_updates/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 ACTUALIZACIÓN SEGURA DE DEPENDENCIAS - GRUPO_GAD"

# 1. Backup completo antes de actualizar
echo "💾 Creando backup completo..."
cp requirements.txt "$BACKUP_DIR/"
cp requirements.lock "$BACKUP_DIR/"
cp pyproject.toml "$BACKUP_DIR/"

# Backup de base de datos
docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > "$BACKUP_DIR/database_backup.sql"

# 2. Verificar estado actual
echo "🔍 Estado actual del sistema..."
docker compose exec api pip list > "$BACKUP_DIR/current_packages.txt"

# 3. Ejecutar tests antes de actualizar
echo "🧪 Ejecutando tests antes de actualización..."
if ! docker compose exec api pytest --tb=short -q; then
    echo "❌ Tests fallan antes de actualización. Abortando."
    exit 1
fi

# 4. Actualizar dependencias en ambiente temporal
echo "📦 Creando ambiente temporal para pruebas..."
docker compose -f docker-compose.test.yml build --no-cache

# 5. Ejecutar tests en ambiente actualizado
echo "🧪 Ejecutando tests en ambiente actualizado..."
if ! docker compose -f docker-compose.test.yml run --rm api pytest --tb=short; then
    echo "❌ Tests fallan con nuevas dependencias. Rollback automático."
    
    # Restaurar archivos originales
    cp "$BACKUP_DIR/requirements.txt" .
    cp "$BACKUP_DIR/requirements.lock" .
    cp "$BACKUP_DIR/pyproject.toml" .
    
    exit 1
fi

# 6. Si tests pasan, aplicar cambios a producción
echo "✅ Tests pasan. Aplicando cambios a producción..."
docker compose build --no-cache api
docker compose up -d api

# 7. Verificación post-actualización
echo "🔍 Verificación post-actualización..."
sleep 30

if curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    echo "✅ Actualización completada exitosamente"
    
    # Guardar estado final
    docker compose exec api pip list > "$BACKUP_DIR/updated_packages.txt"
    
    # Comparar cambios
    echo "📊 Cambios aplicados:"
    diff "$BACKUP_DIR/current_packages.txt" "$BACKUP_DIR/updated_packages.txt" || true
else
    echo "❌ Verificación falló. Iniciando rollback..."
    
    # Rollback completo
    cp "$BACKUP_DIR/requirements.txt" .
    cp "$BACKUP_DIR/requirements.lock" .
    cp "$BACKUP_DIR/pyproject.toml" .
    
    docker compose build --no-cache api
    docker compose up -d api
    
    echo "🔄 Rollback completado"
fi
```

### Limpieza de Logs y Archivos Temporales

#### Script de Limpieza del Sistema
```bash
#!/bin/bash
# scripts/system_cleanup.sh

LOG_RETENTION_DAYS=${1:-7}
TEMP_RETENTION_HOURS=${2:-24}

echo "🧹 LIMPIEZA DEL SISTEMA - GRUPO_GAD"
echo "Retención de logs: $LOG_RETENTION_DAYS días"
echo "Retención de temporales: $TEMP_RETENTION_HOURS horas"

# Función para logging
log_action() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 1. Limpiar logs antiguos
log_action "Limpiando logs antiguos..."
find logs/ -name "*.log" -mtime +$LOG_RETENTION_DAYS -delete 2>/dev/null || true
find logs/ -name "*.log.*" -mtime +$LOG_RETENTION_DAYS -delete 2>/dev/null || true

# 2. Rotar logs actuales si son muy grandes (>100MB)
log_action "Verificando tamaño de logs actuales..."
for logfile in logs/*.log; do
    if [ -f "$logfile" ] && [ $(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile" 2>/dev/null || echo 0) -gt 104857600 ]; then
        log_action "Rotando log grande: $logfile"
        mv "$logfile" "${logfile}.$(date +%Y%m%d_%H%M%S)"
        touch "$logfile"
    fi
done

# 3. Limpiar archivos temporales
log_action "Limpiando archivos temporales..."
find /tmp -name "*grupo_gad*" -mtime +1 -delete 2>/dev/null || true
find . -name "*.tmp" -mtime +1 -delete 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 4. Limpiar backups antiguos
log_action "Limpiando backups antiguos..."
find backups/ -name "*.sql" -mtime +30 -delete 2>/dev/null || true
find backups/ -name "*.gz" -mtime +30 -delete 2>/dev/null || true

# 5. Limpiar Docker images no utilizadas
log_action "Limpiando Docker artifacts..."
docker image prune -f --filter "until=$((LOG_RETENTION_DAYS*24))h" 2>/dev/null || true
docker container prune -f --filter "until=$((LOG_RETENTION_DAYS*24))h" 2>/dev/null || true

# 6. Optimizar base de datos (VACUUM)
log_action "Optimizando base de datos..."
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;" 2>/dev/null || true

# 7. Reportar espacio liberado
log_action "Reporte de limpieza:"
df -h | head -2
du -sh logs/ backups/ 2>/dev/null || true

log_action "✅ Limpieza completada"
```

### Verificación de Integridad de Base de Datos

#### Script de Verificación de BD
```bash
#!/bin/bash
# scripts/db_integrity_check.sh

echo "🔍 VERIFICACIÓN DE INTEGRIDAD - BASE DE DATOS"

# 1. Verificar conectividad
if ! docker compose exec db pg_isready -U $POSTGRES_USER >/dev/null 2>&1; then
    echo "❌ Base de datos no disponible"
    exit 1
fi

# 2. Verificar tamaño y estadísticas
echo "📊 Estadísticas de base de datos:"
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public' 
ORDER BY tablename, attname;
"

# 3. Verificar índices faltantes o no utilizados
echo "🔍 Análisis de índices:"
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT 
    t.tablename,
    indexname,
    c.reltuples AS num_rows,
    pg_size_pretty(pg_relation_size(quote_ident(t.tablename)::text)) AS table_size,
    pg_size_pretty(pg_relation_size(quote_ident(indexrelname)::text)) AS index_size,
    CASE WHEN indisunique THEN 'Y' ELSE 'N' END AS UNIQUE,
    idx_scan as number_of_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_tables t
LEFT OUTER JOIN pg_class c ON c.relname=t.tablename
LEFT OUTER JOIN (
    SELECT 
        c.relname AS ctablename, 
        ipg.relname AS indexname, 
        x.indnatts AS number_of_columns, 
        idx_scan, 
        idx_tup_read, 
        idx_tup_fetch,
        indexrelname,
        indisunique 
    FROM pg_index x
    JOIN pg_class c ON c.oid = x.indrelid
    JOIN pg_class ipg ON ipg.oid = x.indexrelid
    JOIN pg_stat_all_indexes psai ON x.indexrelid = psai.indexrelid
) AS foo ON t.tablename = foo.ctablename
WHERE t.schemaname='public'
ORDER BY 1,2;
"

# 4. Verificar constraints y foreign keys
echo "🔗 Verificación de constraints:"
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
LEFT JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.table_schema = 'public'
ORDER BY tc.table_name, tc.constraint_type;
"

# 5. Verificar conexiones activas
echo "🔌 Conexiones activas:"
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    LEFT(query, 50) as query_preview
FROM pg_stat_activity 
WHERE state = 'active'
ORDER BY query_start;
"

echo "✅ Verificación de integridad completada"
```

## 3. MONITORING Y ALERTAS BÁSICAS

### Métricas Críticas a Monitorear

#### Script de Monitoreo Integral
```bash
#!/bin/bash
# scripts/comprehensive_monitoring.sh

METRICS_FILE="logs/metrics_$(date +%Y%m%d).log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=85
ALERT_THRESHOLD_DISK=90
ALERT_THRESHOLD_RESPONSE_TIME=2000

# Función para logging con timestamp
log_metric() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$METRICS_FILE"
}

log_metric "=== MONITORING GRUPO_GAD ==="

# 1. Métricas de Sistema
log_metric "📊 System Metrics:"

# CPU Usage
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
log_metric "CPU Usage: ${CPU_USAGE}%"
if (( $(echo "$CPU_USAGE > $ALERT_THRESHOLD_CPU" | bc -l) )); then
    log_metric "🚨 ALERT: HIGH CPU USAGE: ${CPU_USAGE}%"
fi

# Memory Usage
MEMORY_INFO=$(free | grep Mem)
MEMORY_TOTAL=$(echo $MEMORY_INFO | awk '{print $2}')
MEMORY_USED=$(echo $MEMORY_INFO | awk '{print $3}')
MEMORY_USAGE=$((MEMORY_USED * 100 / MEMORY_TOTAL))
log_metric "Memory Usage: ${MEMORY_USAGE}%"
if (( MEMORY_USAGE > ALERT_THRESHOLD_MEMORY )); then
    log_metric "🚨 ALERT: HIGH MEMORY USAGE: ${MEMORY_USAGE}%"
fi

# Disk Usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
log_metric "Disk Usage: ${DISK_USAGE}%"
if (( DISK_USAGE > ALERT_THRESHOLD_DISK )); then
    log_metric "🚨 ALERT: HIGH DISK USAGE: ${DISK_USAGE}%"
fi

# 2. Métricas de Aplicación
log_metric "🚀 Application Metrics:"

# Response Time
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/api/v1/health 2>/dev/null || echo "999")
RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME * 1000" | bc)
log_metric "API Response Time: ${RESPONSE_TIME_MS}ms"
if (( $(echo "$RESPONSE_TIME_MS > $ALERT_THRESHOLD_RESPONSE_TIME" | bc -l) )); then
    log_metric "🚨 ALERT: SLOW API RESPONSE: ${RESPONSE_TIME_MS}ms"
fi

# HTTP Status Codes (last hour)
ERROR_COUNT=$(docker compose logs --since=1h api 2>/dev/null | grep -c "ERROR\|exception\|failed" || echo "0")
log_metric "Error Count (last hour): $ERROR_COUNT"
if (( ERROR_COUNT > 10 )); then
    log_metric "🚨 ALERT: HIGH ERROR COUNT: $ERROR_COUNT"
fi

# 3. Métricas de Base de Datos
log_metric "🗄️  Database Metrics:"

# Database Connections
DB_CONNECTIONS=$(docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | xargs || echo "0")
log_metric "Active DB Connections: $DB_CONNECTIONS"
if (( DB_CONNECTIONS > 15 )); then
    log_metric "🚨 ALERT: HIGH DB CONNECTIONS: $DB_CONNECTIONS"
fi

# Database Size
DB_SIZE=$(docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -t -c "SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB'));" 2>/dev/null | xargs || echo "Unknown")
log_metric "Database Size: $DB_SIZE"

# Slow Queries (if log_min_duration_statement is configured)
SLOW_QUERIES=$(docker compose logs db --since=1h 2>/dev/null | grep -c "duration.*ms" || echo "0")
log_metric "Slow Queries (last hour): $SLOW_QUERIES"

# 4. Métricas de WebSocket
log_metric "🔌 WebSocket Metrics:"

WS_STATS=$(curl -s http://localhost:8000/ws/stats 2>/dev/null || echo '{"error": "unavailable"}')
if echo "$WS_STATS" | jq . >/dev/null 2>&1; then
    WS_CONNECTIONS=$(echo "$WS_STATS" | jq -r '.active_connections // 0')
    WS_MESSAGES=$(echo "$WS_STATS" | jq -r '.total_messages_sent // 0')
    log_metric "Active WS Connections: $WS_CONNECTIONS"
    log_metric "Total WS Messages: $WS_MESSAGES"
else
    log_metric "WebSocket Stats: Unavailable"
fi

# 5. Docker Container Status
log_metric "🐳 Container Status:"
CONTAINER_STATUS=$(docker compose ps --format "table {{.Name}}\t{{.Status}}" | tail -n +2)
log_metric "$CONTAINER_STATUS"

log_metric "=== END MONITORING ==="
```

### Setup de Logging Estructurado

#### Configuración de Loguru para Producción
```python
# src/core/production_logging.py
import sys
import os
from loguru import logger
from typing import Dict, Any
import json

class ProductionLogger:
    def __init__(self):
        # Remover handler por defecto
        logger.remove()
        
        # Configurar para producción con rotación
        logger.add(
            "logs/api_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="INFO",
            rotation="00:00",  # Rotar diariamente
            retention="30 days",  # Mantener 30 días
            compression="gz",  # Comprimir logs antiguos
            enqueue=True,  # Thread-safe
            serialize=True,  # JSON format
        )
        
        # Handler para errores críticos (archivo separado)
        logger.add(
            "logs/errors_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="00:00",
            retention="90 days",  # Mantener errores por más tiempo
            compression="gz",
            enqueue=True,
            serialize=True,
        )
        
        # Console output solo para desarrollo
        if os.getenv("ENVIRONMENT", "production") != "production":
            logger.add(
                sys.stderr,
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> | {message}",
                level="DEBUG",
                colorize=True,
            )
    
    def structure_log(self, event_type: str, **kwargs) -> Dict[str, Any]:
        """Crear log estructurado para mejor análisis"""
        return {
            "event_type": event_type,
            "timestamp": logger._core.datetime.utcnow().isoformat(),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "service": "grupo_gad_api",
            **kwargs
        }
    
    def log_api_request(self, method: str, path: str, status_code: int, duration_ms: float, **kwargs):
        """Log especializado para requests API"""
        log_data = self.structure_log(
            "api_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
        
        if status_code >= 500:
            logger.error("API Error", **log_data)
        elif status_code >= 400:
            logger.warning("API Client Error", **log_data)
        else:
            logger.info("API Request", **log_data)
    
    def log_database_operation(self, operation: str, table: str, duration_ms: float, **kwargs):
        """Log especializado para operaciones de BD"""
        log_data = self.structure_log(
            "database_operation",
            operation=operation,
            table=table,
            duration_ms=duration_ms,
            **kwargs
        )
        
        if duration_ms > 1000:  # Más de 1 segundo
            logger.warning("Slow Database Operation", **log_data)
        else:
            logger.info("Database Operation", **log_data)
    
    def log_websocket_event(self, event_type: str, connection_id: str, **kwargs):
        """Log especializado para eventos WebSocket"""
        log_data = self.structure_log(
            "websocket_event",
            ws_event_type=event_type,
            connection_id=connection_id,
            **kwargs
        )
        logger.info("WebSocket Event", **log_data)

# Instancia global
production_logger = ProductionLogger()
```

### Alertas Simples con Herramientas Gratuitas

#### Sistema de Alertas por Email
```python
# src/core/alerting.py
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class Alert:
    severity: str  # "info", "warning", "critical"
    title: str
    message: str
    component: str
    timestamp: str

class EmailAlerting:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.alert_recipients = os.getenv("ALERT_RECIPIENTS", "").split(",")
        
        # Rate limiting: no más de 1 alerta del mismo tipo por hora
        self.alert_history = {}
    
    def _should_send_alert(self, alert: Alert) -> bool:
        """Verificar si debe enviar la alerta (rate limiting)"""
        key = f"{alert.component}:{alert.title}"
        current_time = time.time()
        
        if key in self.alert_history:
            last_sent = self.alert_history[key]
            if current_time - last_sent < 3600:  # 1 hora
                return False
        
        self.alert_history[key] = current_time
        return True
    
    def send_alert(self, alert: Alert) -> bool:
        """Enviar alerta por email"""
        if not self.smtp_user or not self.alert_recipients[0]:
            logger.warning("Email alerting not configured")
            return False
        
        if not self._should_send_alert(alert):
            logger.debug(f"Alert rate limited: {alert.title}")
            return False
        
        try:
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ", ".join(self.alert_recipients)
            msg['Subject'] = f"[GRUPO_GAD] {alert.severity.upper()}: {alert.title}"
            
            body = f"""
            ALERTA GRUPO_GAD
            =================
            
            Severidad: {alert.severity.upper()}
            Componente: {alert.component}
            Timestamp: {alert.timestamp}
            
            Mensaje:
            {alert.message}
            
            ---
            Sistema de Monitoreo GRUPO_GAD
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Alert sent: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
            return False

# Instancia global
email_alerting = EmailAlerting()
```

### Thresholds de Alerta Recomendados

#### Configuración de Umbrales
```python
# config/monitoring_thresholds.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ThresholdConfig:
    warning: float
    critical: float
    unit: str
    description: str

# Umbrales recomendados para GRUPO_GAD
MONITORING_THRESHOLDS = {
    # Recursos del sistema
    "cpu_usage_percent": ThresholdConfig(
        warning=70.0,
        critical=85.0,
        unit="%",
        description="Uso de CPU del sistema"
    ),
    
    "memory_usage_percent": ThresholdConfig(
        warning=75.0,
        critical=90.0,
        unit="%",
        description="Uso de memoria RAM"
    ),
    
    "disk_usage_percent": ThresholdConfig(
        warning=80.0,
        critical=95.0,
        unit="%",
        description="Uso de espacio en disco"
    ),
    
    # Performance de API
    "api_response_time_ms": ThresholdConfig(
        warning=1000.0,
        critical=2000.0,
        unit="ms",
        description="Tiempo de respuesta de la API"
    ),
    
    "api_error_rate_percent": ThresholdConfig(
        warning=5.0,
        critical=10.0,
        unit="%",
        description="Porcentaje de errores de API"
    ),
    
    # Base de datos
    "db_connection_count": ThresholdConfig(
        warning=15.0,
        critical=20.0,
        unit="connections",
        description="Número de conexiones activas a BD"
    ),
    
    "db_query_time_ms": ThresholdConfig(
        warning=500.0,
        critical=1000.0,
        unit="ms",
        description="Tiempo promedio de queries"
    ),
    
    # WebSocket
    "ws_connection_count": ThresholdConfig(
        warning=80.0,
        critical=100.0,
        unit="connections",
        description="Conexiones WebSocket activas"
    ),
    
    # Logs y errores
    "error_count_per_hour": ThresholdConfig(
        warning=10.0,
        critical=25.0,
        unit="errors/hour",
        description="Errores por hora en logs"
    ),
}

def get_threshold_status(metric_name: str, value: float) -> tuple[str, str]:
    """
    Obtener estado basado en umbrales
    Returns: (status, message)
    """
    if metric_name not in MONITORING_THRESHOLDS:
        return ("unknown", f"No threshold configured for {metric_name}")
    
    threshold = MONITORING_THRESHOLDS[metric_name]
    
    if value >= threshold.critical:
        return ("critical", f"{threshold.description}: {value}{threshold.unit} >= {threshold.critical}{threshold.unit}")
    elif value >= threshold.warning:
        return ("warning", f"{threshold.description}: {value}{threshold.unit} >= {threshold.warning}{threshold.unit}")
    else:
        return ("healthy", f"{threshold.description}: {value}{threshold.unit} - Normal")
```

## 4. ESCALABILIDAD Y OPTIMIZACIÓN

### Señales de que Necesitas Más Recursos

#### Script de Análisis de Capacidad
```bash
#!/bin/bash
# scripts/capacity_analysis.sh

echo "📈 ANÁLISIS DE CAPACIDAD - GRUPO_GAD"

# Función para análisis de tendencias
analyze_trend() {
    local metric_name=$1
    local current_value=$2
    local threshold_warning=$3
    local threshold_critical=$4
    
    if (( $(echo "$current_value >= $threshold_critical" | bc -l) )); then
        echo "🔴 $metric_name: CRÍTICO ($current_value) - Acción inmediata requerida"
        return 2
    elif (( $(echo "$current_value >= $threshold_warning" | bc -l) )); then
        echo "🟡 $metric_name: ADVERTENCIA ($current_value) - Planificar upgrade"
        return 1
    else
        echo "🟢 $metric_name: NORMAL ($current_value)"
        return 0
    fi
}

# 1. Análisis de CPU
CPU_USAGE=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}" | grep api | awk '{print $2}' | sed 's/%//')
analyze_trend "CPU Usage" "$CPU_USAGE" "70" "85"

# 2. Análisis de Memoria
MEMORY_USAGE=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemPerc}}" | grep api | awk '{print $2}' | sed 's/%//')
analyze_trend "Memory Usage" "$MEMORY_USAGE" "75" "90"

# 3. Análisis de conexiones concurrentes
CONCURRENT_REQUESTS=$(docker compose logs --since=1h api | grep -c "Request:" || echo "0")
analyze_trend "Requests/hour" "$CONCURRENT_REQUESTS" "1000" "2000"

# 4. Análisis de respuesta
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/api/v1/health | awk '{print $1*1000}')
analyze_trend "Response Time (ms)" "$RESPONSE_TIME" "1000" "2000"

# 5. Recomendaciones de escalabilidad
echo ""
echo "🚀 RECOMENDACIONES DE ESCALABILIDAD:"

if (( $(echo "$CPU_USAGE > 70" | bc -l) )); then
    echo "- Aumentar workers de Gunicorn (actual: 4, recomendado: 6-8)"
    echo "- Considerar instancia con más CPU cores"
fi

if (( $(echo "$MEMORY_USAGE > 75" | bc -l) )); then
    echo "- Aumentar RAM del contenedor"
    echo "- Optimizar queries de base de datos"
    echo "- Implementar cache Redis más agresivo"
fi

if (( $(echo "$RESPONSE_TIME > 1000" | bc -l) )); then
    echo "- Agregar índices a base de datos"
    echo "- Implementar connection pooling"
    echo "- Considerar CDN para assets estáticos"
fi

# 6. Estimación de capacidad máxima
echo ""
echo "📊 ESTIMACIÓN DE CAPACIDAD ACTUAL:"
echo "- Usuarios concurrentes soportados: ~$((100 - CPU_USAGE))"
echo "- Margen de crecimiento: $((100 - MEMORY_USAGE))%"
echo "- Tiempo antes de saturación: ~$((100 - CPU_USAGE))% de margen"
```

### Cómo Hacer Upgrade de Plan de Hosting

#### Guía de Upgrade para Railway
```bash
#!/bin/bash
# scripts/railway_upgrade_guide.sh

echo "🚀 GUÍA DE UPGRADE - RAILWAY HOSTING"

# Verificar métricas actuales
echo "📊 Métricas actuales del sistema:"
echo "CPU: $(docker stats --no-stream --format "{{.CPUPerc}}" | head -1)"
echo "Memory: $(docker stats --no-stream --format "{{.MemPerc}}" | head -1)"
echo "Disk: $(df -h / | tail -1 | awk '{print $5}')"

echo ""
echo "📋 PASOS PARA UPGRADE EN RAILWAY:"

echo ""
echo "1. 📈 EVALUAR NECESIDAD DE UPGRADE:"
echo "   - Hobby ($5/mes): 512MB RAM, 1 vCPU"
echo "   - Pro ($20/mes): 2GB RAM, 2 vCPU"
echo "   - Team ($99/mes): 8GB RAM, 4 vCPU"

echo ""
echo "2. 🔧 COMANDOS RAILWAY CLI:"
echo "   # Ver uso actual"
echo "   railway status"
echo "   railway metrics"
echo ""
echo "   # Cambiar plan"
echo "   railway login"
echo "   railway link  # Si no está linkeado"
echo "   # Ir al dashboard web para cambiar plan"

echo ""
echo "3. ⚙️ AJUSTAR CONFIGURACIÓN POST-UPGRADE:"

echo ""
echo "   # Actualizar workers según nuevos recursos"
echo "   # En gunicorn.conf.py:"
echo "   workers = int(os.environ.get('WORKERS', 6))  # Para Pro plan"
echo ""
echo "   # Actualizar variables de entorno"
echo "   railway variables set WORKERS=6"
echo "   railway variables set MAX_CONNECTIONS=2000"

echo ""
echo "4. 🔄 REDEPLOY DESPUÉS DEL UPGRADE:"
echo "   railway deploy"
echo "   # O push a main para auto-deploy"
echo "   git push origin main"

echo ""
echo "5. ✅ VERIFICACIÓN POST-UPGRADE:"
echo "   # Health check"
echo "   curl https://tu-dominio.com/api/v1/health"
echo ""
echo "   # Verificar métricas mejoradas"
echo "   railway metrics"
echo ""
echo "   # Verificar logs"
echo "   railway logs"

echo ""
echo "💡 TIPS DE OPTIMIZACIÓN POST-UPGRADE:"
echo "- Monitorear por 24-48h después del upgrade"
echo "- Ajustar connection pooling de BD si es necesario"
echo "- Considerar Redis si no lo tienes para caching"
echo "- Implementar health checks más frecuentes"
```

### Scripts de Automatización

#### Script de Deployment Completo
```bash
#!/bin/bash
# scripts/automated_deployment.sh

ENVIRONMENT=${1:-"production"}
BACKUP_BEFORE_DEPLOY=${2:-"yes"}
RUN_TESTS=${3:-"yes"}

echo "🚀 DEPLOYMENT AUTOMATIZADO - GRUPO_GAD"
echo "Entorno: $ENVIRONMENT"
echo "Backup: $BACKUP_BEFORE_DEPLOY"
echo "Tests: $RUN_TESTS"

# Función de logging
log_step() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Función de verificación de salud
health_check() {
    local url=$1
    local retries=${2:-30}
    
    for i in $(seq 1 $retries); do
        if curl -f "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
        echo -n "."
    done
    return 1
}

# 1. Validación pre-deployment
log_step "🔍 Ejecutando validaciones pre-deployment..."

if [ "$RUN_TESTS" = "yes" ]; then
    log_step "🧪 Ejecutando tests..."
    if ! pytest --tb=short -q; then
        echo "❌ Tests fallan. Abortando deployment."
        exit 1
    fi
    echo "✅ Tests passed"
fi

# 2. Backup si es requerido
if [ "$BACKUP_BEFORE_DEPLOY" = "yes" ]; then
    log_step "💾 Creando backup pre-deployment..."
    timestamp=$(date +"%Y%m%d_%H%M%S")
    
    # Backup de código actual
    git stash push -m "pre-deploy-backup-$timestamp"
    
    # Backup de base de datos
    if docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > "backup_pre_deploy_${timestamp}.sql"; then
        echo "✅ Backup completado"
    else
        echo "⚠️  Backup falló, continuando..."
    fi
fi

# 3. Build y deployment
log_step "🔨 Building aplicación..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker compose -f docker/docker-compose.prod.yml build --no-cache
else
    docker compose build --no-cache
fi

# 4. Stop servicios actuales
log_step "🛑 Deteniendo servicios actuales..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker compose -f docker/docker-compose.prod.yml down
else
    docker compose down
fi

# 5. Start nuevos servicios
log_step "▶️  Iniciando servicios actualizados..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker compose -f docker/docker-compose.prod.yml up -d
else
    docker compose up -d
fi

# 6. Aplicar migraciones
log_step "📊 Aplicando migraciones de base de datos..."
sleep 20  # Esperar que la BD esté lista

if [ "$ENVIRONMENT" = "production" ]; then
    docker compose -f docker/docker-compose.prod.yml exec api alembic upgrade head
else
    docker compose exec api alembic upgrade head
fi

# 7. Health check post-deployment
log_step "🏥 Verificando salud del sistema..."
echo -n "Esperando que la API esté disponible"
if health_check "http://localhost:8000/api/v1/health" 60; then
    echo ""
    echo "✅ API está respondiendo correctamente"
else
    echo ""
    echo "❌ API no responde. Iniciando rollback..."
    
    # Rollback automático
    if [ "$BACKUP_BEFORE_DEPLOY" = "yes" ]; then
        git stash pop
        docker compose down
        docker compose up -d
    fi
    exit 1
fi

# 8. Verificaciones adicionales
log_step "🔍 Ejecutando verificaciones adicionales..."

# Verificar endpoints críticos
ENDPOINTS=(
    "http://localhost:8000/api/v1/health"
    "http://localhost:8000/metrics"
    "http://localhost:8000/docs"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -f "$endpoint" >/dev/null 2>&1; then
        echo "✅ $endpoint - OK"
    else
        echo "⚠️  $endpoint - FAILED"
    fi
done

# 9. Limpieza post-deployment
log_step "🧹 Limpieza post-deployment..."
docker image prune -f
docker container prune -f

# 10. Reporte final
log_step "📋 DEPLOYMENT COMPLETADO"
echo ""
echo "🎉 Deployment exitoso en entorno: $ENVIRONMENT"
echo "⏰ Tiempo total: $(date)"
echo "📊 Servicios activos:"
docker compose ps

echo ""
echo "🔗 URLs de verificación:"
echo "- Health: http://localhost:8000/api/v1/health"
echo "- Docs: http://localhost:8000/docs"
echo "- Metrics: http://localhost:8000/metrics"

echo ""
echo "📝 Próximos pasos recomendados:"
echo "1. Monitorear logs por las próximas 2 horas"
echo "2. Ejecutar smoke tests en producción"
echo "3. Verificar métricas de performance"
echo "4. Notificar a stakeholders del deployment exitoso"
```

#### Script de Rollback Rápido
```bash
#!/bin/bash
# scripts/quick_rollback.sh

BACKUP_TIMESTAMP=${1:-"latest"}

echo "🔄 ROLLBACK RÁPIDO - GRUPO_GAD"
echo "Backup timestamp: $BACKUP_TIMESTAMP"

log_step() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 1. Detener servicios actuales
log_step "🛑 Deteniendo servicios actuales..."
docker compose down

# 2. Restaurar código desde backup
log_step "📂 Restaurando código..."
if [ "$BACKUP_TIMESTAMP" = "latest" ]; then
    git stash pop
else
    git stash list | grep "$BACKUP_TIMESTAMP"
    if [ $? -eq 0 ]; then
        # Encontrar el stash y aplicarlo
        STASH_ID=$(git stash list | grep "$BACKUP_TIMESTAMP" | cut -d: -f1)
        git stash apply "$STASH_ID"
    else
        echo "⚠️  Backup con timestamp $BACKUP_TIMESTAMP no encontrado"
        echo "Backups disponibles:"
        git stash list
        exit 1
    fi
fi

# 3. Restaurar base de datos si existe backup
log_step "🗄️  Buscando backup de base de datos..."
if [ -f "backup_pre_deploy_${BACKUP_TIMESTAMP}.sql" ]; then
    log_step "📊 Restaurando base de datos..."
    docker compose up -d db
    sleep 20
    
    docker compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB < "backup_pre_deploy_${BACKUP_TIMESTAMP}.sql"
    echo "✅ Base de datos restaurada"
else
    echo "⚠️  No se encontró backup de BD para $BACKUP_TIMESTAMP"
fi

# 4. Reconstruir y reiniciar servicios
log_step "🔨 Reconstruyendo servicios..."
docker compose build --no-cache
docker compose up -d

# 5. Verificar que el rollback funcionó
log_step "🏥 Verificando rollback..."
sleep 30

if curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    echo "✅ Rollback completado exitosamente"
    echo "🌐 API disponible en: http://localhost:8000"
else
    echo "❌ Rollback falló. Verificar logs manualmente."
    docker compose logs api
    exit 1
fi

echo ""
echo "🎯 ROLLBACK COMPLETADO"
echo "📋 Estado de servicios:"
docker compose ps

echo ""
echo "📝 Acciones recomendadas post-rollback:"
echo "1. Investigar la causa del problema original"
echo "2. Ejecutar tests para confirmar estabilidad"
echo "3. Monitorear sistema por próximas 2 horas"
echo "4. Planificar fix y nuevo deployment"
```

Esta documentación completa proporciona todo lo necesario para diagnosticar, mantener y monitorear eficazmente el sistema GRUPO_GAD en producción, con herramientas y scripts listos para usar.
