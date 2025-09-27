"""add_geom_to_efectivos

Revision ID: 41b34c160381
Revises: e062d9a5b51f
Create Date: 2025-09-27 07:34:49.491212

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '41b34c160381'
down_revision: Union[str, Sequence[str], None] = 'e062d9a5b51f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add geom column to efectivos table with PostGIS support."""
    # Check if table exists before attempting to modify it
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Only proceed if efectivos table exists
    if 'efectivos' in inspector.get_table_names():
        # Check if we're using PostgreSQL (PostGIS support)
        if bind.dialect.name == 'postgresql':
            # Add geography column for storing Point geometries with SRID 4326
            op.execute("ALTER TABLE efectivos ADD COLUMN geom geography(POINT, 4326)")
            
            # Create GiST index for spatial queries
            op.execute("CREATE INDEX IF NOT EXISTS ix_efectivos_geom_gist ON efectivos USING GIST (geom)")
        else:
            # For non-PostgreSQL databases (like SQLite), add a simple column
            # This won't support spatial operations but allows the schema to be compatible
            op.add_column('efectivos', sa.Column('geom', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove geom column and index from efectivos table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Only proceed if efectivos table exists
    if 'efectivos' in inspector.get_table_names():
        if bind.dialect.name == 'postgresql':
            # Drop the spatial index first
            op.execute("DROP INDEX IF EXISTS ix_efectivos_geom_gist")
        
        # Drop the geom column
        op.drop_column('efectivos', 'geom')
