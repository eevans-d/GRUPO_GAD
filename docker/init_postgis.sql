-- Init PostGIS extensions used by GRUPO_GAD
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
-- pgcrypto used for cryptographic helpers when required
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- This file is mounted into the Postgres image at /docker-entrypoint-initdb.d/
-- and will run on initial database creation. It is safe to rerun (uses IF NOT EXISTS).