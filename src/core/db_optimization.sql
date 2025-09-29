-- ============================================
-- GRUPO_GAD - ÍNDICES DE OPTIMIZACIÓN
-- Índices estratégicos basados en patrones de consulta comunes
-- ============================================

-- Establecer schema
SET search_path TO gad, public;

-- ============================================
-- ÍNDICES PARA TABLA DE USUARIOS
-- ============================================

-- Índice único compuesto para login eficiente (email case-insensitive)
CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_email_active 
ON gad.usuarios (LOWER(email)) 
WHERE is_active = true;

-- Índice para búsquedas por rol y nivel
CREATE INDEX IF NOT EXISTS idx_usuarios_rol_nivel 
ON gad.usuarios (rol, nivel_usuario) 
WHERE is_active = true;

-- Índice parcial para usuarios activos (consultas más comunes)
CREATE INDEX IF NOT EXISTS idx_usuarios_active_created 
ON gad.usuarios (created_at DESC) 
WHERE is_active = true;

-- ============================================
-- ÍNDICES PARA TABLA DE TAREAS
-- ============================================

-- Índice compuesto para consultas de tareas por estado y prioridad
CREATE INDEX IF NOT EXISTS idx_tareas_estado_prioridad 
ON gad.tareas (estado, prioridad, fecha_inicio DESC);

-- Índice para búsquedas por delegado (usuario asignado)
CREATE INDEX IF NOT EXISTS idx_tareas_delegado_estado 
ON gad.tareas (delegado_usuario_id, estado) 
WHERE estado != 'cancelada';

-- Índice para búsquedas por fecha y estado (reportes)
CREATE INDEX IF NOT EXISTS idx_tareas_fecha_estado 
ON gad.tareas (fecha_inicio DESC, estado) 
INCLUDE (titulo, prioridad);

-- Índice para tareas programadas futuras
CREATE INDEX IF NOT EXISTS idx_tareas_programadas 
ON gad.tareas (fecha_inicio ASC) 
WHERE estado = 'programada' AND fecha_inicio > CURRENT_TIMESTAMP;

-- Índice GIN para búsqueda en efectivos asignados (array)
CREATE INDEX IF NOT EXISTS idx_tareas_efectivos_gin 
ON gad.tareas USING GIN (efectivos_asignados);

-- Índice GIN para búsqueda en metadata JSONB
CREATE INDEX IF NOT EXISTS idx_tareas_metadata_gin 
ON gad.tareas USING GIN (metadata);

-- Índice espacial para consultas geográficas (si se usa ubicación)
CREATE INDEX IF NOT EXISTS idx_tareas_ubicacion_gist 
ON gad.tareas USING GIST (
    ll_to_earth(ubicacion_lat, ubicacion_lon)
) WHERE ubicacion_lat IS NOT NULL AND ubicacion_lon IS NOT NULL;

-- ============================================
-- ÍNDICES PARA TABLA DE EFECTIVOS
-- ============================================

-- Índice compuesto para disponibilidad y competencias
CREATE INDEX IF NOT EXISTS idx_efectivos_disponibilidad_competencias 
ON gad.efectivos (estado_disponibilidad, competencias_especiales) 
WHERE is_active = true;

-- Índice para búsquedas por rango y unidad
CREATE INDEX IF NOT EXISTS idx_efectivos_rango_unidad 
ON gad.efectivos (rango, unidad_asignada) 
WHERE is_active = true;

-- Índice GIN para búsqueda en competencias JSONB
CREATE INDEX IF NOT EXISTS idx_efectivos_competencias_gin 
ON gad.efectivos USING GIN (competencias_especiales);

-- ============================================
-- ÍNDICES PARA AUDITORÍA Y LOGS
-- ============================================

-- Índice para consultas de auditoría por usuario y fecha
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario_fecha 
ON gad.auditoria_operaciones (usuario_id, timestamp DESC);

-- Índice para consultas de auditoría por acción
CREATE INDEX IF NOT EXISTS idx_auditoria_accion_fecha 
ON gad.auditoria_operaciones (accion, timestamp DESC);

-- ============================================
-- ESTADÍSTICAS Y MANTENIMIENTO
-- ============================================

-- Actualizar estadísticas de todas las tablas del schema gad
ANALYZE gad.usuarios;
ANALYZE gad.tareas;
ANALYZE gad.efectivos;

-- ============================================
-- FUNCIONES DE MONITOREO DE ÍNDICES
-- ============================================

-- Función para monitorear el uso de índices
CREATE OR REPLACE FUNCTION gad.fn_monitor_index_usage()
RETURNS TABLE (
    schema_name text,
    table_name text,
    index_name text,
    index_scans bigint,
    tuples_read bigint,
    tuples_fetched bigint,
    usage_ratio numeric
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname::text,
        tablename::text,
        indexname::text,
        idx_scan,
        idx_tup_read,
        idx_tup_fetch,
        CASE 
            WHEN idx_tup_read > 0 
            THEN ROUND((idx_tup_fetch::numeric / idx_tup_read::numeric) * 100, 2)
            ELSE 0 
        END as usage_ratio
    FROM pg_stat_user_indexes pgsui
    JOIN pg_indexes pgi ON pgsui.indexname = pgi.indexname
    WHERE pgsui.schemaname = 'gad'
    ORDER BY idx_scan DESC, usage_ratio DESC;
END;
$$ LANGUAGE plpgsql;

-- Función para detectar índices no utilizados
CREATE OR REPLACE FUNCTION gad.fn_detect_unused_indexes()
RETURNS TABLE (
    schema_name text,
    table_name text,
    index_name text,
    index_size text,
    reason text
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        schemaname::text,
        tablename::text,
        indexname::text,
        pg_size_pretty(pg_relation_size(indexname::regclass))::text,
        CASE 
            WHEN idx_scan = 0 THEN 'Never used'
            WHEN idx_scan < 10 THEN 'Rarely used (< 10 scans)'
            ELSE 'Low usage'
        END::text as reason
    FROM pg_stat_user_indexes pgsui
    WHERE pgsui.schemaname = 'gad'
    AND (idx_scan = 0 OR idx_scan < 10)
    AND indexname NOT LIKE '%_pkey'  -- Excluir primary keys
    ORDER BY idx_scan ASC, pg_relation_size(indexname::regclass) DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- COMENTARIOS PARA DOCUMENTACIÓN
-- ============================================

COMMENT ON INDEX gad.idx_usuarios_email_active IS 
'Índice único para login eficiente con email case-insensitive, solo usuarios activos';

COMMENT ON INDEX gad.idx_tareas_estado_prioridad IS 
'Índice compuesto para consultas frecuentes de tareas por estado y prioridad';

COMMENT ON INDEX gad.idx_tareas_efectivos_gin IS 
'Índice GIN para búsquedas eficientes en array de efectivos asignados';

COMMENT ON FUNCTION gad.fn_monitor_index_usage() IS 
'Función para monitorear el uso y eficiencia de índices en el schema gad';

COMMENT ON FUNCTION gad.fn_detect_unused_indexes() IS 
'Función para detectar índices poco utilizados que podrían eliminarse';