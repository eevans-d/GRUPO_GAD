# Configuraciones Optimizadas PostGIS para Sistemas Operativos/Tácticos

## Objetivo

Proporcionar configuraciones optimizadas para PostGIS en entornos operativos/tácticos que requieren alta disponibilidad, performance predecible y baja latencia para operaciones espaciales críticas.

## Arquitectura de Configuración

### 1. postgresql.conf Optimizado

#### Configuración Base para Operaciones Tácticas

```ini
# ===============================================
# CONFIGURACIÓN POSTGRESQL OPTIMIZADA POSTGIS
# Sistemas Operativos/Tácticos - High Performance
# ===============================================

# === CONEXIONES Y MEMORIA ===
# Configuración optimizada para 32GB RAM
shared_buffers = 8GB                     # 25% de RAM - Cache principal
effective_cache_size = 24GB              # 75% de RAM - Estimación OS cache
work_mem = 256MB                         # Memoria por operación sort/hash
maintenance_work_mem = 2GB               # Memoria para VACUUM/CREATE INDEX
autovacuum_work_mem = 1GB                # Memoria para autovacuum

# === AUTOVACUUM OPTIMIZADO ===
# Configuración crítica para datos espaciales dinámicos
autovacuum = on
autovacuum_max_workers = 6
autovacuum_naptime = 30s
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05
autovacuum_freeze_max_age = 200000000
autovacuum_multixact_freeze_max_age = 400000000
autovacuum_vacuum_cost_delay = 10ms
autovacuum_vacuum_cost_limit = 200

# === CHECKPOINT Y WAL CONFIGURATION ===
# Configuración para recovery rápido
checkpoint_timeout = 15min
max_wal_size = 4GB
min_wal_size = 1GB
checkpoint_completion_target = 0.9
checkpoint_warning = 30s

wal_level = replica
wal_buffers = 64MB
max_wal_senders = 10
max_replication_slots = 10

# === QUERY PLANNER ===
# Optimizado para consultas espaciales complejas
random_page_cost = 1.1                   # SSD-optimizado
effective_io_concurrency = 200           # SSD parallel I/O
cpu_tuple_cost = 0.01
cpu_index_tuple_cost = 0.005
cpu_operator_cost = 0.0025

# Planificador más agresivo para joins
from_collapse_limit = 8
join_collapse_limit = 8
parallel_leader_participation = on

# === WORKER PROCESSES ===
# Optimizado para consultas paralelas
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4

# === LOGGING Y PERFORMANCE ===
# Logging detallado para troubleshooting
log_destination = 'stderr,csvlog'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB

# Configuración crítica para performance monitoring
log_min_duration_statement = 500ms       # Log consultas > 500ms
log_statement = 'none'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = 10MB

# === SPATIAL DATA OPTIMIZATIONS ===
# Configuraciones específicas PostGIS
# PostGIS performance settings
postgis.gdal_enabled_drivers = 'ENABLED'
postgis.enable_outdb_rasters = false
postgis.gdal_config_options = 'GDAL_CACHEMAX=256'

# Geometry performance settings
max_connections = 200                    # High concurrent connections
superuser_reserved_connections = 3

# === RESOURCE LIMITS ===
# Prevenir resource exhaustion
max_locks_per_transaction = 64
max_pred_locks_per_transaction = 64

# === TIMEZONE ===
timezone = 'UTC'
log_timezone = 'UTC'

# === LOCALE ===
lc_messages = 'C'
lc_monetary = 'C'
lc_numeric = 'C'
lc_time = 'C'
default_text_search_config = 'pg_catalog.english'

# === SHARED PRELISTS ===
# Cache para funciones frecuentemente usadas
shared_preload_libraries = 'pg_stat_statements'

# === pg_stat_statements ===
pg_stat_statements.max = 10000
pg_stat_statements.track = all
pg_stat_statements.save = on

# === AUTOVACUUM DEDICADO ===
# Configuración específica para tablas con geometrías
autovacuum_vacuum_table = 'benchmark_locations'
autovacuum_vacuum_scale_factor = 0.05
autovacuum_analyze_table = 'benchmark_locations'
autovacuum_analyze_scale_factor = 0.02
```

#### Configuración Ultra Performance (64GB+ RAM)

```ini
# CONFIGURACIÓN PARA HARDWARE DE ALTO RENDIMIENTO
# Optimizado para 64GB+ RAM y SSD NVMe

# === MEMORIA OPTIMIZADA ===
shared_buffers = 16GB                     # 25% de RAM
effective_cache_size = 48GB              # 75% de RAM
work_mem = 512MB                         # Operaciones complejas
maintenance_work_mem = 4GB               # Index builds rápidos

# === CHECKPOINT AGGRESSIVO ===
checkpoint_timeout = 10min
max_wal_size = 8GB
min_wal_size = 2GB
checkpoint_completion_target = 0.95

# === PARALLELISM MAXIMIZADO ===
max_worker_processes = 16
max_parallel_workers_per_gather = 8
max_parallel_workers = 16
max_parallel_maintenance_workers = 8

# === I/O OPTIMIZATION ===
random_page_cost = 1.05                  # NVMe ultra-fast
effective_io_concurrency = 400           # Máximo paralelismo I/O

# === CONNECTION POOL ===
max_connections = 400
superuser_reserved_connections = 3
```

### 2. Configuración pg_hba.conf Optimizada

```conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD
# IPv4 local connections:
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             192.168.1.0/24          scram-sha-256
# IPv6 local connections:
host    all             all             ::1/128                 scram-sha-256
# Allow replication connections from localhost, by a user with the replication privilege.
local   replication     all                                     scram-sha-256
host    replication     all             127.0.0.1/32            scram-sha-256
host    replication     all             ::1/128                 scram-sha-256

# Spatial data access
host    gis_data        spatial_app     192.168.1.0/24          scram-sha-256
host    operational     tactical_app    192.168.1.0/24          scram-sha-256

# Read replicas for scaling
host    all             app_readonly    192.168.2.0/24          scram-sha-256
```

### 3. Configuración de Índices Espaciales

#### Script de Creación de Índices Optimizados

```sql
-- CONFIGURACIÓN DE ÍNDICES ESPACIALES OPTIMIZADOS
-- PostGIS Production Ready Indexing Strategy

-- === PRIMARY SPATIAL INDEXES ===
-- Índices GiST principales para operaciones críticas

-- Tabla de efectivos operativos (más crítica)
CREATE INDEX CONCURRENTLY idx_efectivos_geom_gist 
ON efectivos USING GIST (geom) 
WITH (fillfactor = 90);

-- Índice compuesto para queries mixtas (estado + ubicación)
CREATE INDEX CONCURRENTLY idx_efectivos_state_geom_gist 
ON efectivos (estado_operativo, geom) 
USING GIST (geom) 
WITH (fillfactor = 90);

-- Índice para disponibilidad + ubicación
CREATE INDEX CONCURRENTLY idx_efectivos_disponibility_geom_gist 
ON efectivos (disponible, geom) 
USING GIST (geom) 
WITH (fillfactor = 90);

-- === SPATIAL INDEXES PARA TASK ASSIGNMENT ===
-- Optimizado para asignación por ubicación

-- Tareas con ubicación geográfica
CREATE INDEX CONCURRENTLY idx_tareas_geom_gist 
ON tareas USING GIST (geom) 
WITH (fillfactor = 85);

-- Índice para prioridad + ubicación (asignación urgente)
CREATE INDEX CONCURRENTLY idx_tareas_priority_geom_gist 
ON tareas (prioridad, geom) 
USING GIST (geom) 
WITH (fillfactor = 85);

-- === POLYGON/LINE GEOMETRIES ===
-- Para geocercas y operaciones de containment

-- Geocercas operativas
CREATE INDEX CONCURRENTLY idx_geofences_geom_gist 
ON geofences USING GIST (geom) 
WITH (fillfactor = 80);

-- Límites administrativos
CREATE INDEX CONCURRENTLY idx_admin_boundaries_geom_gist 
ON administrative_boundaries USING GIST (geom) 
WITH (fillfactor = 75);

-- === TEMPORAL-SPATIAL INDEXES ===
-- Para consultas histórico-operacionales

-- Índice para operaciones recientes (último año)
CREATE INDEX CONCURRENTLY idx_operations_2024_geom_gist 
ON operaciones_2024 USING GIST (geom) 
WHERE fecha_operacion >= '2024-01-01'
WITH (fillfactor = 85);

-- === COMPOUND INDEXES ===
-- Índices compuestos para operaciones complejas

-- Efectivos por categoría y ubicación
CREATE INDEX CONCURRENTLY idx_efectivos_category_geom_gist 
ON efectivos (categoria, estado_operativo, geom) 
USING GIST (geom) 
WITH (fillfactor = 90);

-- === PARTITION INDEXES ===
-- Para tablas particionadas por región

-- Partición por región (ejemplo)
CREATE INDEX CONCURRENTLY idx_region_north_geom_gist 
ON efectivos_north USING GIST (geom) 
WITH (fillfactor = 90);

CREATE INDEX CONCURRENTLY idx_region_south_geom_gist 
ON efectivos_south USING GIST (geom) 
WITH (fillfactor = 90);

-- === INDEX MAINTENANCE ===
-- Comandos para mantener índices optimizados

-- Reindex completo (schedule semanal)
REINDEX DATABASE gis_production;

-- Vacuum analyze específico para índices espaciales
ANALYZE efectivos;
ANALYZE tareas;
ANALYZE geofences;

-- === INDEX PERFORMANCE MONITORING ===
-- Queries para monitorear efectividad de índices

-- Estadísticas de uso de índices
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Índices no utilizados (candidatos para eliminación)
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- === CLUSTERING CONFIGURATION ===
-- Para reorganizar físicamente tablas críticas

-- Clustering por geometría (ejecutar en maintenance window)
CLUSTER efectivo USING idx_efectivos_geom_gist;

-- Clustering para tareas por prioridad
CLUSTER tareas USING idx_tareas_priority_geom_gist;
```

### 4. Configuración de Connection Pooling

#### Configuración asyncpg Optimizada

```python
# CONFIGURACIÓN OPTIMIZADA DE CONNECTION POOLING
# Para sistemas operativos/tácticos

import asyncpg
from asyncpg.pool import Pool
import asyncio
import logging

class OptimizedPostGISPool:
    def __init__(self):
        self.pool_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'gis_production',
            'user': 'spatial_app',
            'password': 'secure_password',
            'min_size': 20,                # Pool mínimo activo
            'max_size': 100,               # Pool máximo
            'max_queries': 50000,          # Queries antes de re-connection
            'max_inactive_connection_lifetime': 3600.0,  # 1 hora
            'command_timeout': 60,         # Timeout por comando
            'server_settings': {
                'jit': 'off',              # Disable JIT para spatial ops
                'work_mem': '256MB',
                'maintenance_work_mem': '2GB',
                'effective_cache_size': '24GB',
                'random_page_cost': '1.1',
                'effective_io_concurrency': '200'
            },
            'command': 'postgresql'
        }
        
        # Pool de configuración para diferentes tipos de consultas
        self.pools = {
            'spatial_critical': self._create_pool_config(
                min_size=30, max_size=80, command_timeout=30
            ),
            'spatial_batch': self._create_pool_config(
                min_size=10, max_size=40, command_timeout=120
            ),
            'analytics': self._create_pool_config(
                min_size=5, max_size=20, command_timeout=300
            ),
            'maintenance': self._create_pool_config(
                min_size=2, max_size=10, command_timeout=600
            )
        }
        
    def _create_pool_config(self, min_size: int, max_size: int, command_timeout: int):
        """Crear configuración específica para tipo de pool"""
        config = self.pool_config.copy()
        config.update({
            'min_size': min_size,
            'max_size': max_size,
            'command_timeout': command_timeout
        })
        return config
        
    async def get_pool(self, pool_type: str = 'spatial_critical') -> Pool:
        """Obtener pool de conexiones optimizado"""
        if pool_type not in self.pools:
            pool_type = 'spatial_critical'
            
        config = self.pools[pool_type]
        pool = await asyncpg.create_pool(**config)
        return pool
        
    async def create_spatial_pool(self) -> Pool:
        """Pool especializado para operaciones espaciales críticas"""
        return await self.get_pool('spatial_critical')
        
    async def create_batch_pool(self) -> Pool:
        """Pool para operaciones batch/masivas"""
        return await self.get_pool('spatial_batch')
        
    async def create_analytics_pool(self) -> Pool:
        """Pool para consultas analíticas"""
        return await self.get_pool('analytics')

# Configuración específica para FastAPI
class SpatialDatabaseManager:
    def __init__(self):
        self.pools = {}
        
    async def initialize_pools(self):
        """Inicializar pools de conexiones"""
        pool_manager = OptimizedPostGISPool()
        
        self.pools['spatial'] = await pool_manager.create_spatial_pool()
        self.pools['batch'] = await pool_manager.create_batch_pool()
        self.pools['analytics'] = await pool_manager.create_analytics_pool()
        
        logging.info("Pools de PostGIS inicializados")
        
    async def get_spatial_pool(self):
        """Obtener pool para consultas espaciales críticas"""
        return self.pools.get('spatial')
        
    async def get_batch_pool(self):
        """Obtener pool para operaciones batch"""
        return self.pools.get('batch')
        
    async def close_pools(self):
        """Cerrar todos los pools"""
        for pool in self.pools.values():
            if pool:
                await pool.close()
        logging.info("Pools de PostGIS cerrados")

# Configuración de ejemplo para FastAPI
SPATIAL_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'gis_production',
    'user': 'spatial_app',
    'password': 'secure_password',
    'min_size': 20,
    'max_size': 100,
    'max_queries': 50000,
    'max_inactive_connection_lifetime': 3600.0,
    'command_timeout': 60,
    'server_settings': {
        'jit': 'off',                       # Disable para operaciones espaciales
        'work_mem': '256MB',               # Memoria por operación
        'maintenance_work_mem': '2GB',     # Memoria para maintenance
        'effective_cache_size': '24GB',    # Cache estimado del OS
        'random_page_cost': '1.1',         # SSD-optimizado
        'effective_io_concurrency': '200', # Paralelismo I/O
        'max_parallel_workers_per_gather': '4',
        'max_worker_processes': '8'
    }
}
```

### 5. Configuración de Monitoring y Alertas

#### Configuración Prometheus para PostGIS

```yaml
# prometheus.yml - Configuración optimizada para PostGIS
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "postgis_rules.yml"
  - "spatial_performance_rules.yml"

scrape_configs:
  - job_name: 'postgis'
    static_configs:
      - targets: ['localhost:9187']  # postgres_exporter
    scrape_interval: 10s
    metrics_path: /metrics
    
  - job_name: 'postgis-spatial'
    static_configs:
      - targets: ['localhost:9187']
    scrape_interval: 5s
    metrics_path: /metrics
    params:
      include: ['pg_stat_database','pg_stat_user_tables','pg_stat_user_indexes']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Reglas de alertas específicas para PostGIS
alerting_rules:
  groups:
  - name: postgis_performance
    rules:
    - alert: PostGISHighLatency
      expr: pg_stat_database_blk_read_time{dbname="gis_production"} > 100
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "PostGIS high read latency detected"
        
    - alert: PostGISSpatialQuerySlow
      expr: rate(pg_stat_statements_mean_time_seconds[5m]) > 1.0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "Spatial queries taking >1s average"
        
    - alert: PostGISIndexBloat
      expr: pg_stat_user_indexes_idx_scan > 0
      for: 0s
      labels:
        severity: info
      annotations:
        summary: "Check index usage patterns"
        
  - name: connection_pool
    rules:
    - alert: PostGISConnectionPoolExhausted
      expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
      for: 1m
      labels:
        severity: warning
      annotations:
        summary: "PostGIS connection pool near exhaustion"
```

### 6. Configuración de Backup Optimizada

#### Script de Backup para Datos Espaciales

```bash
#!/bin/bash
# BACKUP OPTIMIZADO PARA POSTGIS - Sistemas Operativos/Tácticos

set -e

# Configuración
BACKUP_DIR="/backup/postgis"
DATE=$(date +%Y%m%d_%H%M%S)
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="gis_production"
DB_USER="postgres"
S3_BUCKET="gis-backups-prod"
RETENTION_DAYS=30

# Crear directorio de backup
mkdir -p $BACKUP_DIR

echo "Iniciando backup PostGIS: $DATE"

# 1. Backup lógico con compresión optimizada
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER \
  --format=custom \
  --verbose \
  --clean \
  --if-exists \
  --create \
  --file="$BACKUP_DIR/gis_production_$DATE.dump" \
  $DB_NAME

# 2. Backup específico de geometrías (metadata)
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER \
  --schema-only \
  --format=plain \
  --file="$BACKUP_DIR/schema_$DATE.sql" \
  $DB_NAME

# 3. Compresión adicional para transporte
gzip "$BACKUP_DIR/gis_production_$DATE.dump"
gzip "$BACKUP_DIR/schema_$DATE.sql"

# 4. Verificar integridad del backup
if ! pg_restore --list "$BACKUP_DIR/gis_production_$DATE.dump.gz" > /dev/null; then
  echo "ERROR: Backup corrupted!"
  exit 1
fi

# 5. Estadísticas del backup
BACKUP_SIZE=$(du -sh "$BACKUP_DIR/gis_production_$DATE.dump.gz" | cut -f1)
echo "Backup completado: $BACKUP_SIZE"

# 6. Upload a S3 si está configurado
if command -v aws &> /dev/null; then
  aws s3 cp "$BACKUP_DIR/gis_production_$DATE.dump.gz" \
    "s3://$S3_BUCKET/backups/" \
    --storage-class STANDARD_IA
fi

# 7. Limpiar backups antiguos
find $BACKUP_DIR -name "*.dump.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# 8. Log de backup
echo "$DATE - Backup completed - Size: $BACKUP_SIZE" >> /var/log/postgis_backup.log

echo "Backup PostGIS completado exitosamente"
```

### 7. Configuración de Archivado WAL

#### Configuración de Archive para Recovery Rápido

```ini
# postgresql.conf - Archive settings optimizados

# WAL Archive configuration
wal_level = replica
archive_mode = on
archive_command = '/usr/local/bin/archive_wal.sh %p %f'
archive_timeout = 300                    # Archive cada 5 minutos
max_wal_senders = 10
max_replication_slots = 10
```

#### Script de Archive WAL

```bash
#!/bin/bash
# /usr/local/bin/archive_wal.sh

WAL_FILE=$1
ARCHIVE_FILE=$2
ARCHIVE_DIR="/var/lib/postgresql/archive_wal"
LOG_FILE="/var/log/wal_archive.log"

# Crear directorio de archive si no existe
mkdir -p $ARCHIVE_DIR

# Copiar archivo WAL al directorio de archive
cp "$WAL_FILE" "$ARCHIVE_DIR/$ARCHIVE_FILE"

# Verificar integridad
if [ -f "$ARCHIVE_DIR/$ARCHIVE_FILE" ]; then
  echo "$(date): WAL $ARCHIVE_FILE archived successfully" >> $LOG_FILE
  exit 0
else
  echo "$(date): Failed to archive WAL $ARCHIVE_FILE" >> $LOG_FILE
  exit 1
fi
```

### 8. Configuración de Replication

#### Configuración de Réplica para Read Scaling

```ini
# primary: postgresql.conf (nodo principal)

# Replication configuration
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = 1GB
synchronous_standby_names = '1 (standby_1)'

# Archive settings
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/archive_wal/%f'

# Replication user
# CREATE USER replicator REPLICATION LOGIN ENCRYPTED PASSWORD 'replica_password';
```

```ini
# standby: postgresql.conf (nodo réplica)

# Standby configuration
hot_standby = on
max_standby_streaming_delay = 30s
wal_receiver_status_interval = 10s

# Recovery configuration
restore_command = 'cp /var/lib/postgresql/archive_wal/%f %p'
standby_mode = on
primary_conninfo = 'host=primary_db port=5432 user=replicator application_name=standby_1'
```

### 9. Optimizaciones de Sistema Operativo

#### Configuración Linux para PostGIS

```bash
#!/bin/bash
# OPTIMIZACIONES DEL SISTEMA OPERATIVO PARA POSTGIS
# Sistemas operativos/tácticos

# === KERNEL PARAMETERS ===
# /etc/sysctl.conf optimizations

# Memory management
vm.swappiness = 1                         # Minimizar swap
vm.dirty_ratio = 15                       # Flush dirty pages más frecuente
vm.dirty_background_ratio = 5             # Background flush
vm.vfs_cache_pressure = 50                # Mantener cache de inodes

# Network optimizations para conexiones concurrentes
net.core.somaxconn = 1024                 # Socket connections
net.core.netdev_max_backlog = 5000        # Network device queue
net.core.rmem_max = 16777216              # Socket buffer size
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# File system optimizations
fs.file-max = 6815744                     # Maximum file descriptors
fs.nr_open = 1048576                      # Maximum open files per process

# === LIMITS CONFIGURATION ===
# /etc/security/limits.conf

postgres soft nofile 65536
postgres hard nofile 65536
postgres soft nproc 65536
postgres hard nproc 65536

# === MOUNT OPTIONS ===
# /etc/fstab - Optimizaciones para data directory

/dev/mapper/postgres-lv /var/lib/postgresql/data ext4 defaults,noatime,discard 0 2

# === SERVICE CONFIGURATION ===
# /etc/systemd/system/postgresql.service

[Unit]
Description=PostgreSQL database server optimized
After=network.target

[Service]
Type=notify
User=postgres
Group=postgres
ExecStart=/usr/lib/postgresql/15/bin/postgres -D /var/lib/postgresql/15/main
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
KillSignal=SIGINT
TimeoutStopSec=30
PrivateTmp=true
Restart=always
RestartSec=10

# Memory optimizations
MemoryLimit=32G
OOMScoreAdjust=-500

# CPU optimizations
CPUAccounting=true
CPUQuota=400%

[Install]
WantedBy=multi-user.target

# === CONFIGURACIÓN I/O SCHEDULER ===
# Para SSD/NVMe storage

echo noop > /sys/block/sda/queue/scheduler
echo deadline > /sys/block/sdb/queue/scheduler

# === NETWORK TUNING ===
# TCP optimizations para alta concurrencia

sysctl -w net.ipv4.tcp_fin_timeout=15
sysctl -w net.ipv4.tcp_keepalive_time=600
sysctl -w net.ipv4.tcp_keepalive_intvl=60
sysctl -w net.ipv4.tcp_keepalive_probes=9
sysctl -w net.ipv4.tcp_tw_reuse=1
```

### 10. Configuración de Disaster Recovery

#### Plan de Recovery para Sistemas Tácticos

```bash
#!/bin/bash
# DISASTER RECOVERY SCRIPT PARA POSTGIS
# Recovery rápido para sistemas operativos/tácticos

set -e

# Configuración
PRIMARY_DB="gis_production"
STANDBY_DB="gis_standby"
BACKUP_DIR="/backup/postgis"
RECOVERY_POINT="20241201_120000"

echo "Iniciando Disaster Recovery PostGIS"
echo "Recovery point: $RECOVERY_POINT"

# 1. Detener servicios en standby
sudo systemctl stop postgresql

# 2. Limpiar data directory en standby
sudo -u postgres rm -rf /var/lib/postgresql/15/main/*

# 3. Restaurar backup completo
sudo -u postgres pg_basebackup -h $PRIMARY_DB -D /var/lib/postgresql/15/main -U replicator -v -P -W

# 4. Configurar recovery.conf
sudo -u postgres cat > /var/lib/postgresql/15/main/recovery.conf << EOF
standby_mode = on
primary_conninfo = 'host=$PRIMARY_DB port=5432 user=replicator application_name=standby_1'
restore_command = 'cp /var/lib/postgresql/archive_wal/%f %p'
EOF

# 5. Configurar hot standby
sudo -u postgres sed -i 's/#hot_standby = off/hot_standby = on/' /var/lib/postgresql/15/main/postgresql.conf

# 6. Ajustar permisos
sudo chown -R postgres:postgres /var/lib/postgresql/15/main/
sudo chmod 700 /var/lib/postgresql/15/main/

# 7. Iniciar servicios
sudo systemctl start postgresql

# 8. Verificar replication status
sudo -u postgres psql -c "SELECT * FROM pg_stat_replication;"

# 9. Test de conectividad desde aplicación
echo "Testing application connectivity..."
curl -f http://localhost:8000/health/database || echo "Database connectivity test failed"

echo "Disaster Recovery completado"
```

## Deployment Scripts

### 1. Deployment Script Completo

```bash
#!/bin/bash
# DEPLOYMENT SCRIPT PARA POSTGIS OPTIMIZADO

set -e

echo "=== DEPLOYMENT POSTGIS OPTIMIZADO ==="

# 1. Backup pre-deployment
./backup_script.sh

# 2. Install PostgreSQL 15 + PostGIS
sudo apt-get update
sudo apt-get install -y postgresql-15 postgresql-contrib-15 postgresql-15-postgis-3

# 3. Configurar sistema
./optimize_os.sh

# 4. Configurar PostgreSQL
sudo cp optimized_postgresql.conf /etc/postgresql/15/main/postgresql.conf
sudo cp optimized_pg_hba.conf /etc/postgresql/15/main/pg_hba.conf

# 5. Configurar PostGIS
sudo -u postgres psql -c "CREATE EXTENSION postgis;"
sudo -u postgres psql -c "CREATE EXTENSION postgis_topology;"
sudo -u postgres psql -c "CREATE EXTENSION fuzzystrmatch;"

# 6. Crear índices optimizados
sudo -u postgres psql -f create_spatial_indexes.sql

# 7. Configurar monitoreo
sudo cp prometheus.yml /etc/prometheus/
sudo systemctl restart prometheus

# 8. Configurar backup automático
sudo cp backup_script.sh /usr/local/bin/
sudo crontab -l > mycron 2>/dev/null || true
echo "0 2 * * * /usr/local/bin/backup_script.sh" >> mycron
sudo crontab mycron
rm mycron

# 9. Restart PostgreSQL
sudo systemctl restart postgresql

# 10. Verificar deployment
./verify_deployment.sh

echo "=== DEPLOYMENT COMPLETADO ==="
```

### 2. Verificación de Deployment

```bash
#!/bin/bash
# VERIFICACIÓN DE DEPLOYMENT POSTGIS

echo "=== VERIFICANDO DEPLOYMENT POSTGIS ==="

# 1. Verificar servicios
sudo systemctl status postgresql | head -5

# 2. Verificar PostGIS
sudo -u postgres psql -c "SELECT PostGIS_Version();"

# 3. Verificar índices espaciales
sudo -u postgres psql -c "
SELECT schemaname, tablename, indexname, indexdef 
FROM pg_indexes 
WHERE indexname LIKE '%gist%';"

# 4. Test de performance básica
sudo -u postgres psql -c "
EXPLAIN ANALYZE 
SELECT COUNT(*) FROM efectivos 
WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)::geography, 10000);"

# 5. Verificar monitoreo
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.job == "postgis") | .health'

# 6. Verificar backup
ls -la /backup/postgis/ | head -3

echo "=== VERIFICACIÓN COMPLETADA ==="
```

## Monitoreo y Alertas

### 1. Métricas Clave a Monitorear

#### Dashboard Grafana para PostGIS

```json
{
  "dashboard": {
    "title": "PostGIS Performance - Sistemas Tácticos",
    "panels": [
      {
        "title": "Spatial Query Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(pg_stat_statements_mean_time_seconds{dbname='gis_production'}[5m])",
            "legendFormat": "Average Query Time"
          },
          {
            "expr": "pg_stat_database_blk_read_time{dbname='gis_production'}",
            "legendFormat": "Block Read Time"
          }
        ]
      },
      {
        "title": "Connection Pool Status",
        "type": "stat",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "Active Connections"
          },
          {
            "expr": "pg_settings_max_connections",
            "legendFormat": "Max Connections"
          }
        ]
      },
      {
        "title": "Spatial Index Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(pg_stat_user_indexes_idx_scan[5m])",
            "legendFormat": "Index Scans"
          }
        ]
      }
    ]
  }
}
```

### 2. Alertas Críticas

#### Alertmanager Configuration

```yaml
# alertmanager.yml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/alerts'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

## Conclusión

Esta configuración optimizada de PostGIS proporciona:

1. **Performance Predictible**: Configuraciones específicas para operaciones espaciales críticas
2. **Alta Disponibilidad**: Replication, backup automatizado y recovery rápido
3. **Escalabilidad**: Connection pooling optimizado y índices espaciales eficientes
4. **Monitoreo Integral**: Métricas específicas y alertas para operaciones espaciales
5. **Disaster Recovery**: Procedures automatizados para recovery en sistemas tácticos

**Nota**: Todas las configuraciones deben ser validadas en entornos de testing antes de deployment en producción.