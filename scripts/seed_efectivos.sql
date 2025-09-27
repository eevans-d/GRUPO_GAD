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