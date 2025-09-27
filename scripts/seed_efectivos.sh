#!/usr/bin/env bash
set -Eeuo pipefail

# Carga variables desde .env.production si existe en el directorio superior
if [ -f .env.production ]; then
  set -a
  source .env.production
  set +a
fi

: "${POSTGRES_USER:?POSTGRES_USER no definido}"
: "${POSTGRES_DB:?POSTGRES_DB no definido}"

echo "Sembrando efectivos (geom) en ${POSTGRES_DB}..."

# Crear el SQL directamente via stdin ya que los scripts pueden no estar en la imagen
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" << 'EOF'
-- ATENCIÓN: Ajusta los IDs a registros reales de tu tabla "efectivos".
-- Requiere que la migración de columna "geom geography(Point,4326)" esté aplicada.
-- Ejemplo: asignar coordenadas a dos efectivos con IDs 1 y 2.

-- Buenos Aires (ARG)
UPDATE efectivos
SET geom = ST_SetSRID(ST_MakePoint(-58.3816, -34.6037), 4326)::geography
WHERE id = 1;

-- Ciudad de México (MEX)
UPDATE efectivos
SET geom = ST_SetSRID(ST_MakePoint(-99.1332, 19.4326), 4326)::geography
WHERE id = 2;

-- Verificación opcional (distancia entre ambos):
-- SELECT ST_Distance(
--   (SELECT geom FROM efectivos WHERE id=1),
--   (SELECT geom FROM efectivos WHERE id=2)
-- ) AS distance_m;
EOF

echo "Listo."