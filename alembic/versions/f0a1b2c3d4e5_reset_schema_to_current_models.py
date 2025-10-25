"""reset_schema_to_current_models

Revision ID: f0a1b2c3d4e5
Revises: 094f640cda5e
Create Date: 2025-10-25 06:25:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "094f640cda5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Reset database schema to match current SQLAlchemy models.

    This migration is intended for staging to reconcile legacy tables with the
    current domain models (gad schema). It drops legacy tables if present and
    recreates minimal structures required by the app.
    """
    # Ensure target schema exists
    op.execute("CREATE SCHEMA IF NOT EXISTS gad")

    # Drop legacy objects if they exist (defensive)
    for tbl in [
        "tarea_asignaciones",
        "historial_estados",
        "tareas",
        "efectivos",
        "usuarios",
        "metricas_tareas",
    ]:
        op.execute(f'DROP TABLE IF EXISTS "{tbl}" CASCADE')

    # Drop legacy enums if created previously
    for enum_name in [
        "tipo_tarea",
        "prioridad_tarea",
        "estado_tarea",
        "estado_disponibilidad",
        "nivel_usuario",
    ]:
        op.execute(f"DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN DROP TYPE {enum_name}; END IF; END $$;")

    # Define enums that match current models
        # Define enums that match current models (use PostgreSQL ENUM explicitly)
        # Create types defensively if they don't exist
        op.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'nivel_autenticacion') THEN
                    CREATE TYPE nivel_autenticacion AS ENUM ('1', '2', '3');
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_disponibilidad_gad') THEN
                    CREATE TYPE estado_disponibilidad_gad AS ENUM ('activo', 'en_tarea', 'en_licencia');
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'estado_tarea_gad') THEN
                    CREATE TYPE estado_tarea_gad AS ENUM ('programada', 'en_curso', 'finalizada');
                END IF;
            END$$;
            """
        )

    nivel_autenticacion = sa.Enum(
        "1",
        "2",
        "3",
        name="nivel_autenticacion",
        create_type=False,
    )
    estado_disponibilidad = sa.Enum(
        "activo",
        "en_tarea",
        "en_licencia",
        name="estado_disponibilidad_gad",
        create_type=False,
    )
    estado_tarea = sa.Enum(
        "programada",
        "en_curso",
        "finalizada",
        name="estado_tarea_gad",
        create_type=False,
    )
    estado_tarea.create(op.get_bind(), checkfirst=True)

    # Create usuarios table (raw SQL to avoid ENUM auto-creation by SQLAlchemy)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS gad.usuarios (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            nombre VARCHAR(100) NOT NULL,
            nivel nivel_autenticacion NOT NULL DEFAULT '1'
        );
        """
    )

    # Create efectivos table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS gad.efectivos (
            id SERIAL PRIMARY KEY,
            dni VARCHAR(20) NOT NULL UNIQUE,
            nombre VARCHAR(100) NOT NULL,
            especialidad VARCHAR(50),
            estado_disponibilidad estado_disponibilidad_gad NOT NULL DEFAULT 'activo',
            usuario_id INTEGER NULL REFERENCES gad.usuarios(id) ON DELETE SET NULL
        );
        """
    )

    # Create tareas table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS gad.tareas (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(20) NOT NULL UNIQUE,
            titulo VARCHAR(100) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            inicio_programado TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            inicio_real TIMESTAMPTZ NULL,
            fin_real TIMESTAMPTZ NULL,
            estado estado_tarea_gad NOT NULL DEFAULT 'programada',
            delegado_usuario_id INTEGER NOT NULL REFERENCES gad.usuarios(id) ON DELETE CASCADE
        );
        """
    )

    # Create association table tarea_asignaciones (many-to-many)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS gad.tarea_asignaciones (
            tarea_id INTEGER NOT NULL REFERENCES gad.tareas(id) ON DELETE CASCADE,
            efectivo_id INTEGER NOT NULL REFERENCES gad.efectivos(id) ON DELETE CASCADE,
            PRIMARY KEY (tarea_id, efectivo_id)
        );
        """
    )


def downgrade() -> None:
    # Drop association first
    op.drop_table("tarea_asignaciones", schema="gad")
    # Drop dependents
    op.drop_table("tareas", schema="gad")
    op.drop_table("efectivos", schema="gad")
    op.drop_table("usuarios", schema="gad")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS nivel_autenticacion")
    op.execute("DROP TYPE IF EXISTS estado_disponibilidad_gad")
    op.execute("DROP TYPE IF EXISTS estado_tarea_gad")
