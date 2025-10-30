"""add_audit_trail_tables

Revision ID: 8a888f8e3bc5
Revises: f0a1b2c3d4e5
Create Date: 2025-10-30 15:17:00.630833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, INET, UUID


# revision identifiers, used by Alembic.
revision: str = '8a888f8e3bc5'
down_revision: Union[str, Sequence[str], None] = '094f640cda5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Create ENUM types for audit trail
    audit_event_type_enum = ENUM(
        'login', 'logout', 'login_failed', 'permission_denied', 'token_refresh',
        'create', 'read', 'update', 'delete', 'bulk_update', 'bulk_delete',
        'task_assigned', 'task_completed', 'task_status_changed', 'emergency_created',
        'user_created', 'user_disabled', 'role_changed', 'system_config_changed',
        'data_export', 'data_import', 'backup_created', 'maintenance_start', 'maintenance_end',
        name='audit_event_type'
    )
    audit_event_type_enum.create(op.get_bind())
    
    audit_severity_enum = ENUM(
        'low', 'medium', 'high', 'critical',
        name='audit_severity'
    )
    audit_severity_enum.create(op.get_bind())
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(36), nullable=False, unique=True),
        sa.Column('event_type', audit_event_type_enum, nullable=False),
        sa.Column('severity', audit_severity_enum, nullable=False, server_default='low'),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('telegram_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('http_method', sa.String(10), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('referer', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('action_description', sa.Text(), nullable=False),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('compliance_tags', sa.String(500), nullable=True),
        sa.Column('retention_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )
    
    # Create audit_sessions table
    op.create_table(
        'audit_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=False, unique=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('telegram_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_activity', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('termination_reason', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    
    # Create indexes for audit tables for performance
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_event_type', 'audit_logs', ['event_type'])
    op.create_index('ix_audit_logs_severity', 'audit_logs', ['severity'])
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('ix_audit_logs_ip_address', 'audit_logs', ['ip_address'])
    op.create_index('ix_audit_logs_retention', 'audit_logs', ['retention_until'])
    
    op.create_index('ix_audit_sessions_user_id', 'audit_sessions', ['user_id'])
    op.create_index('ix_audit_sessions_started_at', 'audit_sessions', ['started_at'])
    op.create_index('ix_audit_sessions_is_active', 'audit_sessions', ['is_active'])


def downgrade() -> None:
    """Downgrade schema."""
    
    # Drop indexes first
    op.drop_index('ix_audit_sessions_is_active', table_name='audit_sessions')
    op.drop_index('ix_audit_sessions_started_at', table_name='audit_sessions')
    op.drop_index('ix_audit_sessions_user_id', table_name='audit_sessions')
    
    op.drop_index('ix_audit_logs_retention', table_name='audit_logs')
    op.drop_index('ix_audit_logs_ip_address', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource', table_name='audit_logs')
    op.drop_index('ix_audit_logs_severity', table_name='audit_logs')
    op.drop_index('ix_audit_logs_event_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    
    # Drop tables
    op.drop_table('audit_sessions')
    op.drop_table('audit_logs')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS audit_severity')
    op.execute('DROP TYPE IF EXISTS audit_event_type')
