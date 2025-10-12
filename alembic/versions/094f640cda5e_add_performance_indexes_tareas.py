"""add_performance_indexes_tareas

Revision ID: 094f640cda5e
Revises: 41b34c160381
Create Date: 2025-10-12 04:23:26.926784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '094f640cda5e'
down_revision: Union[str, Sequence[str], None] = '41b34c160381'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add performance indexes for tareas table."""
    
    # Índice compuesto para filtrado por usuario, estado y ordenamiento por fecha
    # Optimiza: WHERE delegado_usuario_id = X AND estado IN (...) ORDER BY created_at DESC
    op.create_index(
        'idx_tareas_delegado_estado_created',
        'tareas',
        ['delegado_usuario_id', 'estado', 'created_at'],
        unique=False,
        postgresql_using='btree'
    )
    
    # Índice parcial para tareas activas (excluye eliminadas)
    # Optimiza: WHERE deleted_at IS NULL (condición muy común)
    op.create_index(
        'idx_tareas_active',
        'tareas',
        ['delegado_usuario_id', 'created_at'],
        unique=False,
        postgresql_where=sa.text('deleted_at IS NULL'),
        postgresql_using='btree'
    )
    
    # Índice para búsquedas por rango de fechas
    # Optimiza: WHERE created_at BETWEEN X AND Y
    op.create_index(
        'idx_tareas_created_at',
        'tareas',
        ['created_at'],
        unique=False,
        postgresql_using='btree'
    )
    
    # Índice para búsquedas por estado (análisis y reportes)
    # Optimiza: WHERE estado = X
    op.create_index(
        'idx_tareas_estado',
        'tareas',
        ['estado'],
        unique=False,
        postgresql_using='btree'
    )


def downgrade() -> None:
    """Downgrade schema: Remove performance indexes."""
    op.drop_index('idx_tareas_estado', table_name='tareas')
    op.drop_index('idx_tareas_created_at', table_name='tareas')
    op.drop_index('idx_tareas_active', table_name='tareas')
    op.drop_index('idx_tareas_delegado_estado_created', table_name='tareas')
