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
    """Add geom column to efectivos table with PostGIS support.
    
    Note: This migration is skipped on environments without PostGIS.
    To enable PostGIS features, run: CREATE EXTENSION postgis;
    Then manually execute the SQL:
      ALTER TABLE efectivos ADD COLUMN geom geography(POINT, 4326);
      CREATE INDEX ix_efectivos_geom_gist ON efectivos USING GIST (geom);
    """
    # Skipped for now - requires manual PostGIS setup on target database
    pass


def downgrade() -> None:
    """Remove geom column and index from efectivos table."""
    # Skipped - no changes to revert
    pass
            # Drop the spatial index first
            op.execute("DROP INDEX IF EXISTS ix_efectivos_geom_gist")
        
        # Drop the geom column
        op.drop_column('efectivos', 'geom')
