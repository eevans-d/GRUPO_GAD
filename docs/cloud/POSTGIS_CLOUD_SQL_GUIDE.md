# 🗺️ Guía Específica: PostgreSQL + PostGIS en Cloud SQL

**Configuraciones y mejores prácticas para datos geoespaciales en GCP**

---

## 📋 Tabla de Contenidos

1. [Creación de Instancia Optimizada](#1-creación-de-instancia-optimizada)
2. [Habilitar PostGIS](#2-habilitar-postgis)
3. [Migración de Datos Geoespaciales](#3-migración-de-datos-geoespaciales)
4. [Optimización de Queries Espaciales](#4-optimización-de-queries-espaciales)
5. [Backups y Restauración](#5-backups-y-restauración)
6. [Troubleshooting Común](#6-troubleshooting-común)

---

## 1. Creación de Instancia Optimizada

### Comando de Creación Completo

```bash
gcloud sql instances create grupo-gad-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --region=us-central1 \
  --network=grupo-gad-vpc \
  --no-assign-ip \
  --availability-type=REGIONAL \
  --storage-type=SSD \
  --storage-size=50GB \
  --storage-auto-increase \
  --storage-auto-increase-limit=500GB \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --retained-backups-count=30 \
  --retained-transaction-log-days=7 \
  --enable-point-in-time-recovery \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=4 \
  --maintenance-release-channel=production \
  --database-flags=\
max_connections=200,\
shared_buffers=2048MB,\
effective_cache_size=6144MB,\
maintenance_work_mem=512MB,\
checkpoint_completion_target=0.9,\
wal_buffers=16MB,\
default_statistics_target=100,\
random_page_cost=1.1,\
effective_io_concurrency=200,\
work_mem=10485kB,\
min_wal_size=1GB,\
max_wal_size=4GB,\
max_worker_processes=4,\
max_parallel_workers_per_gather=2,\
max_parallel_workers=4,\
max_parallel_maintenance_workers=2
```

### Configuraciones Específicas para PostGIS

```bash
# Flags adicionales para optimizar operaciones geoespaciales
gcloud sql instances patch grupo-gad-db \
  --database-flags=\
shared_buffers=2048MB,\
work_mem=50MB,\
maintenance_work_mem=512MB,\
random_page_cost=1.1,\
effective_io_concurrency=200,\
max_worker_processes=8,\
max_parallel_workers_per_gather=4
```

---

## 2. Habilitar PostGIS

### Método 1: Via psql

```bash
# Conectar a la instancia
gcloud sql connect grupo-gad-db --user=postgres --quiet

# Dentro de psql
\c gad_db

-- Habilitar extensiones
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
CREATE EXTENSION IF NOT EXISTS postgis_sfcgal;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
CREATE EXTENSION IF NOT EXISTS address_standardizer;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Verificar versiones
SELECT PostGIS_version();
SELECT PostGIS_full_version();

-- Verificar extensiones instaladas
\dx

-- Debe mostrar algo como:
--  postgis        | 3.3.2     | public     | PostGIS geometry and geography spatial types
```

### Método 2: Via Script SQL Automatizado

Crear archivo `scripts/cloud/init_postgis_cloud.sql`:

```sql
-- ================================================================
-- Script de Inicialización PostGIS para Cloud SQL
-- Proyecto: GRUPO_GAD
-- ================================================================

-- Conectar a la base de datos principal
\c gad_db

-- Habilitar extensiones esenciales
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Crear esquema para datos espaciales (opcional)
CREATE SCHEMA IF NOT EXISTS spatial;

-- Verificar instalación
DO $$
BEGIN
    RAISE NOTICE 'PostGIS version: %', PostGIS_version();
    RAISE NOTICE 'PostGIS full version: %', PostGIS_full_version();
END
$$;

-- Crear función helper para validar geometrías
CREATE OR REPLACE FUNCTION validate_geometry(geom geometry)
RETURNS boolean AS $$
BEGIN
    RETURN ST_IsValid(geom);
EXCEPTION
    WHEN OTHERS THEN
        RETURN false;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Crear índices espaciales para tablas existentes (ejemplo)
-- Descomentar y ajustar según tus tablas

-- CREATE INDEX IF NOT EXISTS idx_ubicaciones_geom 
--   ON ubicaciones USING GIST (geom);

-- CREATE INDEX IF NOT EXISTS idx_zonas_geom 
--   ON zonas USING GIST (geometria);

-- Grants de permisos para usuario de aplicación
GRANT USAGE ON SCHEMA public TO gad_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gad_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gad_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO gad_user;

-- Verificación final
SELECT 
    e.extname AS "Extension",
    e.extversion AS "Version",
    n.nspname AS "Schema"
FROM pg_extension e
JOIN pg_namespace n ON e.extnamespace = n.oid
WHERE e.extname LIKE 'postgis%' OR e.extname IN ('pgcrypto', 'uuid-ossp')
ORDER BY e.extname;
```

Ejecutar:

```bash
# Via Cloud SQL Proxy
export PGPASSWORD=$(gcloud secrets versions access latest --secret="POSTGRES_PASSWORD")
psql "host=127.0.0.1 port=5432 dbname=gad_db user=postgres" \
  -f scripts/cloud/init_postgis_cloud.sql
```

---

## 3. Migración de Datos Geoespaciales

### Preparar Datos Locales para Exportación

```bash
# 1. Dump completo con formato custom (más eficiente)
pg_dump -Fc \
  -h localhost \
  -U gad_user \
  -d gad_db \
  -f grupo_gad_backup.dump

# 2. Dump solo schema (para verificación)
pg_dump -h localhost -U gad_user -d gad_db --schema-only \
  > schema_only.sql

# 3. Dump solo datos geoespaciales (si tienes tablas específicas)
pg_dump -h localhost -U gad_user -d gad_db \
  --table=ubicaciones \
  --table=zonas_operativas \
  > geodata_only.sql
```

### Subir a Cloud Storage

```bash
# Crear bucket temporal para migración
gsutil mb -l us-central1 gs://grupo-gad-migration-temp/

# Subir dump
gsutil cp grupo_gad_backup.dump gs://grupo-gad-migration-temp/

# Configurar permisos para Cloud SQL
gsutil iam ch \
  serviceAccount:$(gcloud sql instances describe grupo-gad-db \
    --format="value(serviceAccountEmailAddress)"):objectViewer \
  gs://grupo-gad-migration-temp
```

### Importar a Cloud SQL

```bash
# Método 1: Import completo
gcloud sql import sql grupo-gad-db \
  gs://grupo-gad-migration-temp/grupo_gad_backup.dump \
  --database=gad_db

# Método 2: Import vía psql (para más control)
./cloud_sql_proxy -instances=grupo-gad-prod:us-central1:grupo-gad-db=tcp:5432 &

pg_restore -h localhost -p 5432 -U gad_user -d gad_db \
  --verbose \
  --no-owner \
  --no-acl \
  grupo_gad_backup.dump
```

### Verificar Integridad de Datos Geoespaciales

```sql
-- Conectar a Cloud SQL
-- gcloud sql connect grupo-gad-db --user=gad_user --database=gad_db

-- 1. Verificar conteo de registros
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- 2. Verificar geometrías válidas
SELECT 
    'ubicaciones' as tabla,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE ST_IsValid(geom)) as validas,
    COUNT(*) FILTER (WHERE NOT ST_IsValid(geom)) as invalidas
FROM ubicaciones;

-- 3. Verificar SRIDs (sistemas de referencia espacial)
SELECT DISTINCT 
    ST_SRID(geom) as srid,
    COUNT(*) as count
FROM ubicaciones
GROUP BY ST_SRID(geom);

-- 4. Verificar extensión espacial de datos
SELECT 
    ST_AsText(ST_Extent(geom)) as bounding_box,
    ST_AsText(ST_Centroid(ST_Extent(geom))) as centroid
FROM ubicaciones;

-- 5. Verificar índices espaciales
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexdef LIKE '%GIST%'
ORDER BY tablename;
```

---

## 4. Optimización de Queries Espaciales

### Crear Índices Espaciales Optimizados

```sql
-- Índices GIST básicos (más rápidos para queries espaciales generales)
CREATE INDEX idx_ubicaciones_geom ON ubicaciones USING GIST(geom);

-- Índices con opciones de compresión
CREATE INDEX idx_zonas_geom ON zonas_operativas 
USING GIST(geometria) WITH (FILLFACTOR=90);

-- Índices parciales (solo para geometrías válidas)
CREATE INDEX idx_ubicaciones_validas ON ubicaciones USING GIST(geom)
WHERE ST_IsValid(geom);

-- Índices compuestos (espacial + atributo)
CREATE INDEX idx_ubicaciones_geom_tipo ON ubicaciones 
USING GIST(geom, tipo_ubicacion);

-- Estadísticas de geometrías (mejora el query planner)
ANALYZE ubicaciones;
```

### Queries Optimizadas con PostGIS

```sql
-- Búsqueda por distancia (con índice espacial)
EXPLAIN ANALYZE
SELECT id, nombre, ST_Distance(geom, ST_SetSRID(ST_MakePoint(-99.1332, 19.4326), 4326)) as distancia
FROM ubicaciones
WHERE ST_DWithin(
    geom,
    ST_SetSRID(ST_MakePoint(-99.1332, 19.4326), 4326),
    0.1  -- ~11 km en grados decimales
)
ORDER BY distancia
LIMIT 10;

-- Búsqueda por contención (punto dentro de polígono)
SELECT z.id, z.nombre
FROM zonas_operativas z
WHERE ST_Contains(z.geometria, ST_SetSRID(ST_MakePoint(-99.1332, 19.4326), 4326));

-- Intersección de geometrías
SELECT 
    u.id as ubicacion_id,
    z.id as zona_id,
    ST_Area(ST_Intersection(u.geom, z.geometria)) as area_interseccion
FROM ubicaciones u
JOIN zonas_operativas z ON ST_Intersects(u.geom, z.geometria)
WHERE ST_Area(ST_Intersection(u.geom, z.geometria)) > 0.001;

-- Buffer alrededor de punto (crear zona de influencia)
SELECT 
    ST_AsGeoJSON(ST_Buffer(geom::geography, 1000)::geometry) as buffer_1km
FROM ubicaciones
WHERE id = 123;
```

### Configuraciones de Query Performance

```sql
-- Aumentar work_mem para queries complejas (sesión específica)
SET work_mem = '256MB';

-- Deshabilitar nested loops para queries espaciales grandes
SET enable_nestloop = OFF;

-- Ver plan de ejecución detallado
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT ...;
```

---

## 5. Backups y Restauración

### Backups Automáticos

```bash
# Ya configurados en la creación de instancia, verificar:
gcloud sql instances describe grupo-gad-db \
  --format="value(settings.backupConfiguration)"

# Crear backup manual antes de cambios importantes
gcloud sql backups create \
  --instance=grupo-gad-db \
  --description="Pre-migration spatial data backup $(date +%Y-%m-%d)"

# Listar backups disponibles
gcloud sql backups list --instance=grupo-gad-db
```

### Export Manual de Datos Espaciales

```bash
# Export completo de base de datos
gcloud sql export sql grupo-gad-db \
  gs://grupo-gad-backups/manual/full_backup_$(date +%Y%m%d_%H%M%S).sql.gz \
  --database=gad_db

# Export solo de tablas espaciales específicas
gcloud sql export sql grupo-gad-db \
  gs://grupo-gad-backups/spatial/geodata_$(date +%Y%m%d).sql.gz \
  --database=gad_db \
  --table=ubicaciones,zonas_operativas
```

### Restauración Completa

```bash
# Opción 1: Restaurar desde backup automático
gcloud sql backups restore BACKUP_ID \
  --backup-instance=grupo-gad-db \
  --backup-id=BACKUP_ID

# Opción 2: Restaurar desde export SQL
gcloud sql import sql grupo-gad-db \
  gs://grupo-gad-backups/manual/full_backup_20251010.sql.gz \
  --database=gad_db

# Opción 3: Point-in-time recovery (PITR)
gcloud sql instances restore-backup grupo-gad-db \
  --backup-id=BACKUP_ID \
  --backup-instance=grupo-gad-db

# Verificar restauración
gcloud sql connect grupo-gad-db --user=gad_user --database=gad_db
```

### Script de Backup Automatizado

Crear `scripts/cloud/backup_postgis_cloud.sh`:

```bash
#!/usr/bin/env bash
# Backup automatizado de PostGIS en Cloud SQL

set -euo pipefail

PROJECT_ID="grupo-gad-prod"
INSTANCE_NAME="grupo-gad-db"
DATABASE="gad_db"
BUCKET="gs://grupo-gad-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🗄️  Iniciando backup de PostGIS..."

# Crear backup automático
gcloud sql backups create \
  --instance=${INSTANCE_NAME} \
  --description="Automated backup ${TIMESTAMP}"

# Export a Cloud Storage
gcloud sql export sql ${INSTANCE_NAME} \
  ${BUCKET}/automated/backup_${TIMESTAMP}.sql.gz \
  --database=${DATABASE}

# Limpiar backups antiguos (> 30 días)
gsutil -m rm ${BUCKET}/automated/backup_$(date -d '30 days ago' +%Y%m%d)*.sql.gz 2>/dev/null || true

echo "✅ Backup completado: ${BUCKET}/automated/backup_${TIMESTAMP}.sql.gz"
```

---

## 6. Troubleshooting Común

### Problema: Extensión PostGIS no disponible

```bash
# Verificar versión de PostgreSQL
gcloud sql instances describe grupo-gad-db \
  --format="value(databaseVersion)"

# PostGIS requiere PostgreSQL 12+
# Si es versión antigua, crear nueva instancia y migrar
```

### Problema: Queries espaciales lentas

```sql
-- 1. Verificar índices espaciales
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes
WHERE indexdef LIKE '%GIST%';

-- 2. Re-crear índice si está fragmentado
REINDEX INDEX idx_ubicaciones_geom;

-- 3. Actualizar estadísticas
ANALYZE ubicaciones;

-- 4. Vacuum para liberar espacio
VACUUM ANALYZE ubicaciones;
```

### Problema: Geometrías inválidas después de migración

```sql
-- Detectar geometrías inválidas
SELECT id, ST_IsValidReason(geom) as reason
FROM ubicaciones
WHERE NOT ST_IsValid(geom);

-- Reparar geometrías inválidas
UPDATE ubicaciones
SET geom = ST_MakeValid(geom)
WHERE NOT ST_IsValid(geom);

-- Verificar reparación
SELECT COUNT(*) as geometrias_invalidas
FROM ubicaciones
WHERE NOT ST_IsValid(geom);
```

### Problema: SRID inconsistente

```sql
-- Detectar SRIDs diferentes
SELECT DISTINCT ST_SRID(geom) as srid, COUNT(*) as count
FROM ubicaciones
GROUP BY ST_SRID(geom);

-- Estandarizar a SRID 4326 (WGS 84 - estándar mundial)
UPDATE ubicaciones
SET geom = ST_Transform(ST_SetSRID(geom, SRID_ACTUAL), 4326)
WHERE ST_SRID(geom) != 4326;
```

### Problema: Out of Memory en queries complejas

```bash
# Aumentar work_mem en la instancia
gcloud sql instances patch grupo-gad-db \
  --database-flags=work_mem=100MB

# O temporalmente en sesión
# SET work_mem = '256MB';
```

---

## 📊 Monitoreo de Rendimiento PostGIS

### Queries de Diagnóstico

```sql
-- Queries lentas (> 1 segundo)
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC
LIMIT 10;

-- Tamaño de tablas espaciales
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Uso de cache en índices espaciales
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE indexname LIKE '%geom%'
ORDER BY idx_scan DESC;
```

---

## 📚 Referencias

- [PostGIS Documentation](https://postgis.net/documentation/)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [PostGIS Performance Tips](https://postgis.net/workshops/postgis-intro/performance.html)
- [Spatial Indexes in PostGIS](https://postgis.net/docs/using_postgis_dbmanagement.html#spatial_index)

---

*Actualizado: 10 de Octubre, 2025*  
*Versión: 1.0.0*
