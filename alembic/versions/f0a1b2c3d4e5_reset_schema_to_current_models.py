"""reset_schema_to_current_models

Revision ID: f0a1b2c3d4e5
Revises: 094f640cda5e
Create Date: 2025-10-25 06:25:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


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
    nivel_autenticacion = sa.Enum("1", "2", "3", name="nivel_autenticacion")
    estado_disponibilidad = sa.Enum("activo", "en_tarea", "en_licencia", name="estado_disponibilidad_gad")
    estado_tarea = sa.Enum("programada", "en_curso", "finalizada", name="estado_tarea_gad")

    nivel_autenticacion.create(op.get_bind(), checkfirst=True)
    estado_disponibilidad.create(op.get_bind(), checkfirst=True)
    estado_tarea.create(op.get_bind(), checkfirst=True)

    # Create usuarios table
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("nivel", nivel_autenticacion, nullable=False, server_default="1"),
        schema="gad",
    )

    # Create efectivos table
    op.create_table(
        "efectivos",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("dni", sa.String(length=20), nullable=False, unique=True),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("especialidad", sa.String(length=50), nullable=True),
        sa.Column("estado_disponibilidad", estado_disponibilidad, nullable=False, server_default="activo"),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("gad.usuarios.id", ondelete="SET NULL"), nullable=True),
        schema="gad",
    )

    # Create tareas table
    op.create_table(
        "tareas",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False, unique=True),
        sa.Column("titulo", sa.String(length=100), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("inicio_programado", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("inicio_real", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fin_real", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", estado_tarea, nullable=False, server_default="programada"),
        sa.Column("delegado_usuario_id", sa.Integer(), sa.ForeignKey("gad.usuarios.id", ondelete="CASCADE"), nullable=False),
        schema="gad",
    )

    # Create association table tarea_asignaciones (many-to-many)
    op.create_table(
        "tarea_asignaciones",
        sa.Column("tarea_id", sa.Integer(), sa.ForeignKey("gad.tareas.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("efectivo_id", sa.Integer(), sa.ForeignKey("gad.efectivos.id", ondelete="CASCADE"), primary_key=True),
        schema="gad",
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
