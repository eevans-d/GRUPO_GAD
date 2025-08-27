-- ============================================
-- GRUPO_GAD - SCHEMA DE BASE DE DATOS PRINCIPAL
-- PostgreSQL 15+ con extensiones avanzadas
-- ============================================

-- Crear schema principal
CREATE SCHEMA IF NOT EXISTS gad;

-- Establecer schema por defecto
SET search_path TO gad, public;

-- ============================================
-- EXTENSIONES REQUERIDAS
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUIDs
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Búsqueda de texto similar
CREATE EXTENSION IF NOT EXISTS "btree_gist";     -- Constraints excluyentes
CREATE EXTENSION IF NOT EXISTS "citext";         -- Texto case-insensitive

-- ============================================
-- TIPOS ENUM PERSONALIZADOS
-- ============================================

-- Estados de disponibilidad de efectivos
CREATE TYPE gad.estado_disponibilidad AS ENUM (
    'disponible',
    'en_tarea',
    'fuera_servicio',
    'no_disponible'
);

-- Estados de tareas
CREATE TYPE gad.estado_tarea AS ENUM (
    'programada',
    'en_curso',
    'finalizada',
    'cancelada',
    'pausada'
);

-- Niveles de usuario
CREATE TYPE gad.nivel_usuario AS ENUM (
    'nivel_1',  -- Efectivo básico
    'nivel_2',  -- Supervisor
    'nivel_3'   -- Administrador
);

-- Prioridades de tareas
CREATE TYPE gad.prioridad_tarea AS ENUM (
    'baja',
    'media',
    'alta',
    'urgente',
    'critica'
);

-- Tipos de tareas
CREATE TYPE gad.tipo_tarea AS ENUM (
    'patrullaje',
    'investigacion',
    'vigilancia',
    'intervencion',
    'administrativa',
    'entrenamiento'
);

-- ============================================
-- TABLA DE USUARIOS
-- ============================================
CREATE TABLE gad.usuarios (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT uuid_generate_v4(),
    dni VARCHAR(20) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email CITEXT UNIQUE NOT NULL,
    telefono VARCHAR(20),
    telegram_id BIGINT UNIQUE,
    nivel gad.nivel_usuario NOT NULL DEFAULT 'nivel_1',
    
    -- Campos de seguridad
    hashed_password VARCHAR(255) NOT NULL,
    verificado BOOLEAN NOT NULL DEFAULT false,
    ultimo_acceso TIMESTAMP WITH TIME ZONE,
    intentos_fallidos INTEGER DEFAULT 0,
    bloqueado_hasta TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT uk_usuarios_dni UNIQUE (dni),
    CONSTRAINT uk_usuarios_telegram_id UNIQUE (telegram_id),
    CONSTRAINT uk_usuarios_email UNIQUE (email),
    CONSTRAINT chk_usuarios_nombre CHECK (LENGTH(TRIM(nombre)) >= 2),
    CONSTRAINT chk_usuarios_apellido CHECK (LENGTH(TRIM(apellido)) >= 2),
    CONSTRAINT chk_usuarios_dni CHECK (LENGTH(TRIM(dni)) >= 5),
    CONSTRAINT chk_usuarios_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- ============================================
-- TABLA DE EFECTIVOS
-- ============================================
CREATE TABLE gad.efectivos (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT uuid_generate_v4(),
    usuario_id INTEGER NOT NULL REFERENCES gad.usuarios(id) ON DELETE CASCADE,
    codigo_interno VARCHAR(50) NOT NULL,
    rango VARCHAR(50),
    unidad VARCHAR(100),
    especialidad VARCHAR(100),
    estado_disponibilidad gad.estado_disponibilidad NOT NULL DEFAULT 'disponible',
    ultima_actualizacion_estado TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT uk_efectivos_usuario_id UNIQUE (usuario_id),
    CONSTRAINT uk_efectivos_codigo_interno UNIQUE (codigo_interno),
    CONSTRAINT chk_efectivos_codigo CHECK (LENGTH(TRIM(codigo_interno)) >= 3)
);

-- ============================================
-- TABLA DE TAREAS
-- ============================================
CREATE TABLE gad.tareas (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL DEFAULT uuid_generate_v4(),
    codigo VARCHAR(50) NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    tipo gad.tipo_tarea NOT NULL,
    prioridad gad.prioridad_tarea NOT NULL DEFAULT 'media',
    
    -- Fechas y tiempos
    inicio_programado TIMESTAMP WITH TIME ZONE NOT NULL,
    fin_programado TIMESTAMP WITH TIME ZONE,
    inicio_real TIMESTAMP WITH TIME ZONE,
    fin_real TIMESTAMP WITH TIME ZONE,
    tiempo_pausado INTERVAL DEFAULT '0 seconds',
    pausado_en TIMESTAMP WITH TIME ZONE,
    
    -- Estados
    estado gad.estado_tarea NOT NULL DEFAULT 'programada',
    
    -- Relaciones
    delegado_usuario_id INTEGER NOT NULL REFERENCES gad.usuarios(id),
    creado_por_usuario_id INTEGER NOT NULL REFERENCES gad.usuarios(id),
    
    -- Ubicación geográfica (opcional)
    ubicacion_lat NUMERIC(10, 8),
    ubicacion_lon NUMERIC(11, 8),
    ubicacion_descripcion TEXT,
    
    -- Efectivos asignados
    efectivos_asignados INTEGER[] DEFAULT '{}',
    
    -- Métricas calculadas (STORED)
    duracion_real_horas NUMERIC GENERATED ALWAYS AS (
        CASE 
            WHEN fin_real IS NOT NULL AND inicio_real IS NOT NULL 
            THEN EXTRACT(EPOCH FROM (fin_real - inicio_real - COALESCE(tiempo_pausado, '0 seconds'))) / 3600.0
            ELSE NULL
        END
    ) STORED,
    
    -- Metadata y notas
    notas JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT uk_tareas_codigo UNIQUE (codigo),
    CONSTRAINT chk_tareas_codigo CHECK (codigo ~ '^[A-Z0-9\-_]{3,20}$'),
    CONSTRAINT chk_tareas_titulo CHECK (LENGTH(TRIM(titulo)) >= 5),
    CONSTRAINT chk_tareas_fechas CHECK (
        fin_programado IS NULL OR fin_programado > inicio_programado
    ),
    CONSTRAINT chk_tareas_fechas_reales CHECK (
        (inicio_real IS NULL AND fin_real IS NULL) OR
        (inicio_real IS NOT NULL AND fin_real IS NULL) OR
        (inicio_real IS NOT NULL AND fin_real IS NOT NULL AND fin_real >= inicio_real)
    ),
    CONSTRAINT chk_tareas_coordenadas CHECK (
        (ubicacion_lat IS NULL AND ubicacion_lon IS NULL) OR
        (ubicacion_lat IS NOT NULL AND ubicacion_lon IS NOT NULL AND 
         ubicacion_lat BETWEEN -90 AND 90 AND ubicacion_lon BETWEEN -180 AND 180)
    ),
    CONSTRAINT exclude_tareas_solapadas EXCLUDE USING gist (
        delegado_usuario_id WITH =,
        tstzrange(inicio_programado, fin_programado) WITH &&
    ) WHERE (estado IN ('programada', 'en_curso'))
);

-- ============================================
-- TABLA DE HISTORIAL DE ESTADOS
-- ============================================
CREATE TABLE gad.historial_estados (
    id SERIAL PRIMARY KEY,
    tarea_id INTEGER NOT NULL REFERENCES gad.tareas(id) ON DELETE CASCADE,
    estado_anterior gad.estado_tarea,
    estado_nuevo gad.estado_tarea NOT NULL,
    usuario_id INTEGER REFERENCES gad.usuarios(id),
    motivo TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLA DE MÉTRICAS DE TAREAS
-- ============================================
CREATE TABLE gad.metricas_tareas (
    id SERIAL PRIMARY KEY,
    tipo_tarea gad.tipo_tarea NOT NULL,
    prioridad gad.prioridad_tarea NOT NULL,
    
    -- Métricas acumuladas
    total_tareas INTEGER NOT NULL DEFAULT 0,
    total_horas REAL NOT NULL DEFAULT 0.0,
    tiempo_promedio_horas REAL,
    tasa_exito DECIMAL(5,2) DEFAULT 0.00,
    
    -- Métricas de rendimiento
    duracion_p25 REAL,  -- 25th percentile
    duracion_p50 REAL,  -- 50th percentile (mediana)
    duracion_p75 REAL,  -- 75th percentile
    duracion_min REAL,
    duracion_max REAL,
    
    -- Fecha de última actualización
    ultima_actualizacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT uk_metricas_tipo_prioridad UNIQUE (tipo_tarea, prioridad)
);

-- ============================================
-- VISTAS MATERIALIZADAS PARA MÉTRICAS
-- ============================================

-- Vista materializada para métricas de duraciones por tipo
CREATE MATERIALIZED VIEW gad.mv_metricas_duraciones AS
SELECT 
    tipo,
    COUNT(*) as total_tareas,
    AVG(EXTRACT(EPOCH FROM (fin_real - inicio_real))/3600) as duracion_promedio_horas,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (fin_real - inicio_real))/3600) as duracion_mediana_horas,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (fin_real - inicio_real))/3600) as duracion_p25_horas,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (fin_real - inicio_real))/3600) as duracion_p75_horas,
    MIN(EXTRACT(EPOCH FROM (fin_real - inicio_real))/3600) as duracion_min_horas,
    MAX(EXTRACT(EPOCH FROM (fin_real - inicio_real))/3600) as duracion_max_horas
FROM gad.tareas
WHERE estado = 'finalizada'
    AND inicio_real IS NOT NULL
    AND fin_real IS NOT NULL
    AND fin_real > inicio_real
GROUP BY tipo
HAVING COUNT(*) >= 5;

-- ============================================
-- ÍNDICES OPTIMIZADOS
-- ============================================

-- Índices en usuarios
CREATE INDEX idx_usuarios_email ON gad.usuarios USING btree (email);
CREATE INDEX idx_usuarios_telegram_id ON gad.usuarios USING btree (telegram_id);
CREATE INDEX idx_usuarios_nivel ON gad.usuarios USING btree (nivel);
CREATE INDEX idx_usuarios_created_at ON gad.usuarios USING btree (created_at);
CREATE INDEX idx_usuarios_nombre_trgm ON gad.usuarios USING gin (nombre gin_trgm_ops);
CREATE INDEX idx_usuarios_apellido_trgm ON gad.usuarios USING gin (apellido gin_trgm_ops);

-- Índices en efectivos
CREATE INDEX idx_efectivos_usuario_id ON gad.efectivos USING btree (usuario_id);
CREATE INDEX idx_efectivos_estado ON gad.efectivos USING btree (estado_disponibilidad);
CREATE INDEX idx_efectivos_unidad ON gad.efectivos USING btree (unidad);
CREATE INDEX idx_efectivos_especialidad ON gad.efectivos USING btree (especialidad);

-- Índices en tareas
CREATE INDEX idx_tareas_codigo ON gad.tareas USING btree (codigo);
CREATE INDEX idx_tareas_estado ON gad.tareas USING btree (estado);
CREATE INDEX idx_tareas_tipo ON gad.tareas USING btree (tipo);
CREATE INDEX idx_tareas_prioridad ON gad.tareas USING btree (prioridad);
CREATE INDEX idx_tareas_delegado ON gad.tareas USING btree (delegado_usuario_id);
CREATE INDEX idx_tareas_creador ON gad.tareas USING btree (creado_por_usuario_id);
CREATE INDEX idx_tareas_fechas ON gad.tareas USING btree (inicio_programado, fin_programado);
CREATE INDEX idx_tareas_created_at ON gad.tareas USING btree (created_at);
CREATE INDEX idx_tareas_efectivos_asignados ON gad.tareas USING gin (efectivos_asignados);
CREATE INDEX idx_tareas_titulo_trgm ON gad.tareas USING gin (titulo gin_trgm_ops);
CREATE INDEX idx_tareas_descripcion_trgm ON gad.tareas USING gin (descripcion gin_trgm_ops);

-- Índices en historial de estados
CREATE INDEX idx_historial_tarea ON gad.historial_estados USING btree (tarea_id);
CREATE INDEX idx_historial_usuario ON gad.historial_estados USING btree (usuario_id);
CREATE INDEX idx_historial_fecha ON gad.historial_estados USING btree (created_at);

-- Índices en métricas
CREATE INDEX idx_metricas_tipo ON gad.metricas_tareas USING btree (tipo_tarea);
CREATE INDEX idx_metricas_prioridad ON gad.metricas_tareas USING btree (prioridad);

-- Índice en la vista materializada
CREATE INDEX idx_mv_metricas_tipo ON gad.mv_metricas_duraciones(tipo);

-- ============================================
-- TRIGGERS Y FUNCIONES
-- ============================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION gad.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para actualizar timestamps
CREATE TRIGGER update_usuarios_updated_at 
    BEFORE UPDATE ON gad.usuarios 
    FOR EACH ROW EXECUTE FUNCTION gad.update_updated_at_column();

CREATE TRIGGER update_efectivos_updated_at 
    BEFORE UPDATE ON gad.efectivos 
    FOR EACH ROW EXECUTE FUNCTION gad.update_updated_at_column();

CREATE TRIGGER update_tareas_updated_at 
    BEFORE UPDATE ON gad.tareas 
    FOR EACH ROW EXECUTE FUNCTION gad.update_updated_at_column();

-- Función para registrar cambios de estado
CREATE OR REPLACE FUNCTION gad.registrar_cambio_estado()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado THEN
        INSERT INTO gad.historial_estados (
            tarea_id, 
            estado_anterior, 
            estado_nuevo, 
            usuario_id,
            motivo
        ) VALUES (
            NEW.id,
            OLD.estado,
            NEW.estado,
            NULL, -- Se puede actualizar con el usuario que hizo el cambio
            CASE 
                WHEN NEW.estado = 'en_curso' THEN 'Tarea iniciada'
                WHEN NEW.estado = 'finalizada' THEN 'Tarea completada'
                WHEN NEW.estado = 'cancelada' THEN 'Tarea cancelada'
                WHEN NEW.estado = 'pausada' THEN 'Tarea pausada'
                ELSE 'Cambio de estado'
            END
        );
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para registrar cambios de estado en tareas
CREATE TRIGGER trigger_registrar_cambio_estado
    AFTER UPDATE OF estado ON gad.tareas
    FOR EACH ROW EXECUTE FUNCTION gad.registrar_cambio_estado();

-- ============================================
-- DATOS INICIALES (SEED DATA)
-- ============================================

-- Insertar usuarios administradores por defecto
INSERT INTO gad.usuarios (
    dni, nombre, apellido, email, hashed_password, nivel, verificado
) VALUES 
('ADMIN001', 'Administrador', 'Sistema', 'admin@gad.local', 
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', 
 'nivel_3', true),
('SUPER001', 'Supervisor', 'Principal', 'supervisor@gad.local',
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
 'nivel_2', true);

-- Insertar métricas iniciales
INSERT INTO gad.metricas_tareas (tipo_tarea, prioridad) VALUES
('patrullaje', 'baja'),
('patrullaje', 'media'),
('patrullaje', 'alta'),
('investigacion', 'baja'),
('investigacion', 'media'),
('investigacion', 'alta'),
('vigilancia', 'baja'),
('vigilancia', 'media'),
('vigilancia', 'alta');

-- ============================================
-- PERMISOS Y SEGURIDAD
-- ============================================

-- Crear roles específicos
CREATE ROLE gad_readonly;
CREATE ROLE gad_readwrite;

-- Otorgar permisos básicos
GRANT USAGE ON SCHEMA gad TO gad_readonly, gad_readwrite;
GRANT SELECT ON ALL TABLES IN SCHEMA gad TO gad_readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA gad TO gad_readwrite;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA gad TO gad_readwrite;

-- Otorgar permisos al usuario de aplicación
GRANT gad_readwrite TO gad_user;

-- ============================================
-- FUNCIONES DE SOPORTE
-- ============================================

-- Función para sugerir dotación basada en métricas
CREATE OR REPLACE FUNCTION gad.fn_sugerir_dotacion(
    p_tipo_tarea gad.tipo_tarea,
    p_prioridad gad.prioridad_tarea,
    p_horas_estimadas NUMERIC DEFAULT 8.0
) RETURNS TABLE(
    sugerencia_efectivos INTEGER,
    confianza TEXT,
    metricas JSONB
) AS $$
DECLARE
    v_metricas RECORD;
    v_sugerencia INTEGER;
    v_confianza TEXT;
BEGIN
    -- Obtener métricas históricas
    SELECT * INTO v_metricas
    FROM gad.metricas_tareas
    WHERE tipo_tarea = p_tipo_tarea 
      AND prioridad = p_prioridad;
    
    -- Si no hay métricas suficientes, sugerencia por defecto
    IF NOT FOUND OR v_metricas.total_tareas < 5 THEN
        v_sugerencia := 2;
        v_confianza := 'BAJA';
        RETURN QUERY SELECT 
            v_sugerencia,
            v_confianza,
            jsonb_build_object(
                'mensaje', 'No hay suficientes datos históricos',
                'tareas_historicas', COALESCE(v_metricas.total_tareas, 0)
            );
    ELSE
        -- Calcular sugerencia basada en métricas
        v_sugerencia := GREATEST(1, 
            CEIL(p_horas_estimadas / NULLIF(v_metricas.duracion_p50, 0))
        );
        
        -- Determinar nivel de confianza
        IF v_metricas.total_tareas >= 20 THEN
            v_confianza := 'ALTA';
        ELSIF v_metricas.total_tareas >= 10 THEN
            v_confianza := 'MEDIA';
        ELSE
            v_confianza := 'BAJA';
        END IF;
        
        RETURN QUERY SELECT 
            v_sugerencia,
            v_confianza,
            jsonb_build_object(
                'tareas_historicas', v_metricas.total_tareas,
                'duracion_promedio_horas', v_metricas.duracion_promedio_horas,
                'duracion_mediana_horas', v_metricas.duracion_p50,
                'horas_estimadas', p_horas_estimadas
            );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VISTAS PARA REPORTES
-- ============================================

-- Vista para tareas activas con detalles
CREATE VIEW gad.v_tareas_activas AS
SELECT 
    t.id,
    t.codigo,
    t.titulo,
    t.tipo,
    t.prioridad,
    t.estado,
    t.inicio_programado,
    t.fin_programado,
    t.inicio_real,
    u.nombre || ' ' || u.apellido as delegado_nombre,
    e.unidad,
    array_length(t.efectivos_asignados, 1) as efectivos_asignados_count
FROM gad.tareas t
JOIN gad.usuarios u ON t.delegado_usuario_id = u.id
LEFT JOIN gad.efectivos e ON t.delegado_usuario_id = e.usuario_id
WHERE t.estado IN ('programada', 'en_curso', 'pausada')
  AND t.deleted_at IS NULL;

-- Vista para métricas operativas
CREATE VIEW gad.v_metricas_operativas AS
SELECT 
    COUNT(*) FILTER (WHERE estado = 'programada') as tareas_programadas,
    COUNT(*) FILTER (WHERE estado = 'en_curso') as tareas_en_curso,
    COUNT(*) FILTER (WHERE estado = 'pausada') as tareas_pausadas,
    COUNT(*) FILTER (WHERE estado = 'finalizada' AND DATE(fin_real) = CURRENT_DATE) as tareas_finalizadas_hoy,
    COUNT(*) FILTER (WHERE estado = 'cancelada' AND DATE(updated_at) = CURRENT_DATE) as tareas_canceladas_hoy,
    COUNT(*) as tareas_totales
FROM gad.tareas
WHERE deleted_at IS NULL;
