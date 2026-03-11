"""001_initial_migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema with UUID-based models."""
    
    # ENUM types
    userplan_enum = sa.Enum('free', 'pro', 'enterprise', name='userplan')
    userplan_enum.create(op.get_bind())
    
    jobstatus_enum = sa.Enum('pending', 'processing', 'done', 'failed', name='jobstatus')
    jobstatus_enum.create(op.get_bind())
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('tg_id', sa.BigInteger(), unique=True, nullable=True, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=True, index=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('plan', userplan_enum, nullable=False, server_default='free'),
        sa.Column('daily_limit', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
    )
    
    # File records table
    op.create_table(
        'file_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('storage_path', sa.String(), nullable=False, index=True),
        sa.Column('original_name', sa.String(512), nullable=False),
        sa.Column('mime_type', sa.String(128), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('sha256_hash', sa.String(64), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True, index=True),
    )
    
    # Conversion jobs table
    op.create_table(
        'conversion_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('status', jobstatus_enum, nullable=False, server_default='pending', index=True),
        sa.Column('source_format', sa.String(16), nullable=False, server_default='pdf'),
        sa.Column('target_format', sa.String(16), nullable=False),
        sa.Column('source_file_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_records.id'), nullable=True),
        sa.Column('result_file_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('file_records.id'), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True, index=True),
    )
    
    # Additional indexes
    op.create_index('ix_conversion_jobs_user_status', 'conversion_jobs', ['user_id', 'status'])


def downgrade() -> None:
    """Drop initial schema."""
    op.drop_table('conversion_jobs')
    op.drop_table('file_records')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS jobstatus')
    op.execute('DROP TYPE IF EXISTS userplan')
