CREATE SCHEMA IF NOT EXISTS gad;

-- Enums
CREATE TYPE gad.nivel_autenticacion AS ENUM ('1', '2', '3');
CREATE TYPE gad.estado_disponibilidad AS ENUM ('activo', 'en_tarea', 'en_licencia');
CREATE TYPE gad.estado_tarea AS ENUM ('programada', 'en_curso', 'finalizada');
CREATE TYPE gad.estado_licencia AS ENUM ('pendiente', 'aprobada', 'rechazada');
CREATE TYPE gad.estado_turno AS ENUM ('programado', 'en_curso', 'finalizado');

-- Tablas
CREATE TABLE gad.usuarios (
  id SERIAL PRIMARY KEY,
  telegram_id BIGINT UNIQUE NOT NULL,
  nombre VARCHAR(100) NOT NULL,
  nivel gad.nivel_autenticacion NOT NULL DEFAULT '1'
);

CREATE TABLE gad.efectivos (
  id SERIAL PRIMARY KEY,
  dni VARCHAR(20) UNIQUE NOT NULL,
  nombre VARCHAR(100) NOT NULL,
  especialidad VARCHAR(50),
  estado_disponibilidad gad.estado_disponibilidad NOT NULL DEFAULT 'activo',
  usuario_id INTEGER REFERENCES gad.usuarios(id)
);

CREATE TABLE gad.tareas (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(20) UNIQUE NOT NULL,
  titulo VARCHAR(100) NOT NULL,
  tipo VARCHAR(50) NOT NULL,
  inicio_programado TIMESTAMP WITH TIME ZONE NOT NULL,
  inicio_real TIMESTAMP WITH TIME ZONE,
  fin_real TIMESTAMP WITH TIME ZONE,
  estado gad.estado_tarea NOT NULL DEFAULT 'programada',
  delegado_usuario_id INTEGER REFERENCES gad.usuarios(id) NOT NULL
);

CREATE TABLE gad.tarea_asignaciones (
  id SERIAL PRIMARY KEY,
  tarea_id INTEGER REFERENCES gad.tareas(id) ON DELETE CASCADE,
  efectivo_id INTEGER REFERENCES gad.efectivos(id) ON DELETE CASCADE,
  UNIQUE (tarea_id, efectivo_id)
);

CREATE TABLE gad.turnos (
  id SERIAL PRIMARY KEY,
  efectivo_id INTEGER REFERENCES gad.efectivos(id) NOT NULL,
  inicio TIMESTAMP WITH TIME ZONE NOT NULL,
  fin TIMESTAMP WITH TIME ZONE NOT NULL CHECK (fin > inicio),
  estado gad.estado_turno NOT NULL DEFAULT 'programado'
);

CREATE TABLE gad.licencias (
  id SERIAL PRIMARY KEY,
  efectivo_id INTEGER REFERENCES gad.efectivos(id) NOT NULL,
  inicio TIMESTAMP WITH TIME ZONE NOT NULL,
  fin TIMESTAMP WITH TIME ZONE NOT NULL CHECK (fin > inicio),
  motivo VARCHAR(200),
  estado gad.estado_licencia NOT NULL DEFAULT 'pendiente'
);

-- Índices
CREATE INDEX idx_efectivos_estado ON gad.efectivos(estado_disponibilidad);
CREATE INDEX idx_tareas_estado ON gad.tareas(estado);
CREATE INDEX idx_tareas_tipo ON gad.tareas(tipo);
CREATE INDEX idx_turnos_efectivo ON gad.turnos(efectivo_id, inicio);

-- Vista para auto-mejora (P50/P75)
CREATE MATERIALIZED VIEW gad.mv_metricas_duraciones AS
SELECT tipo,
       CASE WHEN EXTRACT(HOUR FROM inicio_real) BETWEEN 6 AND 18 THEN 'dia' ELSE 'noche' END AS franja,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (fin_real - inicio_real)) AS p50,
       PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY (fin_real - inicio_real)) AS p75,
       COUNT(*) AS n
FROM gad.tareas WHERE estado = 'finalizada' AND fin_real IS NOT NULL
GROUP BY tipo, franja HAVING COUNT(*) >= 5;

CREATE UNIQUE INDEX idx_mv_metricas ON gad.mv_metricas_duraciones(tipo, franja);
