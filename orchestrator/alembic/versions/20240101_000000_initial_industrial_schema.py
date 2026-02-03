"""Initial Industrial Schema

Revision ID: initial_industrial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_industrial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        CREATE TYPE session_status AS ENUM (
            'pending', 'queued', 'running', 'paused', 
            'completed', 'partially_completed', 'failed', 
            'timeout', 'stopped', 'cancelled', 'orphaned', 'degraded'
        );
    """)
    
    op.execute("""
        CREATE TYPE session_type AS ENUM (
            'planning', 'execution', 'review', 'debug', 'integration'
        );
    """)
    
    op.execute("""
        CREATE TYPE session_priority AS ENUM (
            '0', '1', '2', '3', '4'
        );
    """)
    
    # Create sessions table
    op.create_table('sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('session_type', sa.Enum(
            'PLANNING', 'EXECUTION', 'REVIEW', 'DEBUG', 'INTEGRATION',
            name='session_type'
        ), nullable=False, server_default='EXECUTION'),
        sa.Column('priority', sa.Enum(
            'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'DEFERRED',
            name='session_priority'
        ), nullable=False, server_default='MEDIUM'),
        sa.Column('status', sa.Enum(
            'PENDING', 'QUEUED', 'RUNNING', 'PAUSED', 'COMPLETED',
            'PARTIALLY_COMPLETED', 'FAILED', 'TIMEOUT', 'STOPPED',
            'CANCELLED', 'ORPHANED', 'DEGRADED',
            name='session_status'
        ), nullable=False, server_default='PENDING'),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('model_config', sa.String(length=100), nullable=True),
        sa.Column('initial_prompt', sa.Text(), nullable=False),
        sa.Column('max_duration_seconds', sa.Integer(), nullable=False, server_default='3600'),
        sa.Column('cpu_limit', sa.Float(), nullable=True),
        sa.Column('memory_limit_mb', sa.Integer(), nullable=True),
        sa.Column('metrics_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('updated_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['sessions.id'], name='fk_sessions_parent', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('title', 'created_by', name='uq_sessions_title_creator'),
        sa.CheckConstraint('max_duration_seconds >= 60 AND max_duration_seconds <= 86400', name='chk_sessions_duration'),
        sa.CheckConstraint('COALESCE(cpu_limit, 0.1) >= 0.1 AND COALESCE(cpu_limit, 8.0) <= 8.0', name='chk_sessions_cpu_limit')
    )
    
    # Create indexes for sessions
    op.create_index('idx_sessions_status_priority', 'sessions', ['status', 'priority'])
    op.create_index('idx_sessions_parent_created', 'sessions', ['parent_id', 'created_at'])
    op.create_index('idx_sessions_type_status', 'sessions', ['session_type', 'status'])
    op.create_index('idx_sessions_active', 'sessions', ['status'], 
        postgresql_where=sa.text("status IN ('pending', 'queued', 'running', 'paused')"))
    op.create_index(op.f('ix_sessions_created_at'), 'sessions', ['created_at'])
    op.create_index(op.f('ix_sessions_priority'), 'sessions', ['priority'])
    op.create_index(op.f('ix_sessions_session_type'), 'sessions', ['session_type'])
    op.create_index(op.f('ix_sessions_status'), 'sessions', ['status'])
    op.create_index(op.f('ix_sessions_status_updated_at'), 'sessions', ['status_updated_at'])
    op.create_index(op.f('ix_sessions_title'), 'sessions', ['title'])
    
    # Create session_metrics table
    op.create_table('session_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('queue_duration_seconds', sa.Float(), nullable=True),
        sa.Column('execution_duration_seconds', sa.Float(), nullable=True),
        sa.Column('total_duration_seconds', sa.Float(), nullable=True),
        sa.Column('cpu_usage_percent', sa.Float(), nullable=True),
        sa.Column('memory_usage_mb', sa.Float(), nullable=True),
        sa.Column('disk_usage_mb', sa.Float(), nullable=True),
        sa.Column('network_bytes_sent', sa.BigInteger(), nullable=True),
        sa.Column('network_bytes_received', sa.BigInteger(), nullable=True),
        sa.Column('total_tokens_used', sa.BigInteger(), nullable=True),
        sa.Column('api_calls_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('api_errors_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('code_quality_score', sa.Float(), nullable=True),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('warnings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('checkpoint_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_checkpoint_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], name='fk_metrics_session', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    
    # Create indexes for session_metrics
    op.create_index('idx_metrics_session', 'session_metrics', ['session_id'])
    op.create_index('idx_metrics_created', 'session_metrics', ['created_at'])
    op.create_index('idx_metrics_duration', 'session_metrics', ['execution_duration_seconds'])
    op.create_index('idx_metrics_success', 'session_metrics', ['success_rate'])
    op.create_index(op.f('ix_session_metrics_completed_at'), 'session_metrics', ['completed_at'])
    op.create_index(op.f('ix_session_metrics_failed_at'), 'session_metrics', ['failed_at'])
    op.create_index(op.f('ix_session_metrics_started_at'), 'session_metrics', ['started_at'])
    
    # Create session_checkpoints table
    op.create_table('session_checkpoints',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], name='fk_checkpoints_session', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'sequence', name='uq_checkpoints_session_sequence')
    )
    
    # Create indexes for session_checkpoints
    op.create_index('idx_checkpoints_session_seq', 'session_checkpoints', ['session_id', 'sequence'])
    op.create_index('idx_checkpoints_timestamp', 'session_checkpoints', ['session_id', 'created_at'])
    op.create_index(op.f('ix_session_checkpoints_created_at'), 'session_checkpoints', ['created_at'])
    
    # Create foreign key from sessions to metrics
    op.create_foreign_key('fk_sessions_metrics', 'sessions', 'session_metrics', ['metrics_id'], ['id'], ondelete='CASCADE')
    
    # Create industrial triggers
    op.execute("""
        CREATE OR REPLACE FUNCTION update_session_child_ids()
        RETURNS TRIGGER AS $$
        DECLARE
            child_ids_json JSONB;
        BEGIN
            IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND NEW.parent_id IS DISTINCT FROM OLD.parent_id) THEN
                IF NEW.parent_id IS NOT NULL THEN
                    UPDATE sessions
                    SET metadata = jsonb_set(
                        COALESCE(metadata, '{}'::jsonb),
                        '{child_ids}',
                        COALESCE(metadata->'child_ids', '[]'::jsonb) || to_jsonb(NEW.id::text)
                    )
                    WHERE id = NEW.parent_id;
                END IF;
                
                IF TG_OP = 'UPDATE' AND OLD.parent_id IS NOT NULL AND OLD.parent_id IS DISTINCT FROM NEW.parent_id THEN
                    UPDATE sessions
                    SET metadata = jsonb_set(
                        COALESCE(metadata, '{}'::jsonb),
                        '{child_ids}',
                        COALESCE(metadata->'child_ids', '[]'::jsonb) - to_jsonb(OLD.id::text)
                    )
                    WHERE id = OLD.parent_id;
                END IF;
            END IF;
            
            IF TG_OP = 'UPDATE' AND NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL THEN
                IF NEW.parent_id IS NOT NULL THEN
                    UPDATE sessions
                    SET metadata = jsonb_set(
                        COALESCE(metadata, '{}'::jsonb),
                        '{child_ids}',
                        COALESCE(metadata->'child_ids', '[]'::jsonb) - to_jsonb(NEW.id::text)
                    )
                    WHERE id = NEW.parent_id;
                END IF;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trg_update_child_ids
        AFTER INSERT OR UPDATE OF parent_id, deleted_at ON sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_session_child_ids();
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION update_session_metrics_timestamps()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status = 'running' AND OLD.status != 'running' THEN
                UPDATE session_metrics
                SET started_at = NEW.status_updated_at
                WHERE session_id = NEW.id;
            END IF;
            
            IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
                UPDATE session_metrics
                SET completed_at = NEW.status_updated_at
                WHERE session_id = NEW.id;
            END IF;
            
            IF NEW.status = 'failed' AND OLD.status != 'failed' THEN
                UPDATE session_metrics
                SET failed_at = NEW.status_updated_at
                WHERE session_id = NEW.id;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trg_update_metrics_timestamps
        AFTER UPDATE OF status ON sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_session_metrics_timestamps();
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION enforce_optimistic_lock()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                IF NEW.version != OLD.version + 1 THEN
                    RAISE EXCEPTION 'Optimistic lock violation for session %%: expected version %%, got %%',
                        OLD.id, OLD.version + 1, NEW.version
                    USING ERRCODE = '23505';
                END IF;
            END IF;
            
            IF TG_OP = 'INSERT' THEN
                NEW.version := 1;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trg_enforce_optimistic_lock
        BEFORE INSERT OR UPDATE ON sessions
        FOR EACH ROW
        EXECUTE FUNCTION enforce_optimistic_lock();
    """)
    
    # Create full-text search index
    op.execute("""
        CREATE INDEX idx_sessions_search ON sessions 
        USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
    """)


def downgrade() -> None:
    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS trg_enforce_optimistic_lock ON sessions")
    op.execute("DROP FUNCTION IF EXISTS enforce_optimistic_lock()")
    
    op.execute("DROP TRIGGER IF EXISTS trg_update_metrics_timestamps ON sessions")
    op.execute("DROP FUNCTION IF EXISTS update_session_metrics_timestamps()")
    
    op.execute("DROP TRIGGER IF EXISTS trg_update_child_ids ON sessions")
    op.execute("DROP FUNCTION IF EXISTS update_session_child_ids()")
    
    # Drop indexes
    op.drop_index('idx_sessions_search', table_name='sessions')
    op.drop_index('idx_checkpoints_timestamp', table_name='session_checkpoints')
    op.drop_index('idx_checkpoints_session_seq', table_name='session_checkpoints')
    op.drop_index('idx_metrics_success', table_name='session_metrics')
    op.drop_index('idx_metrics_duration', table_name='session_metrics')
    op.drop_index('idx_metrics_created', table_name='session_metrics')
    op.drop_index('idx_metrics_session', table_name='session_metrics')
    op.drop_index('idx_sessions_active', table_name='sessions')
    op.drop_index('idx_sessions_type_status', table_name='sessions')
    op.drop_index('idx_sessions_parent_created', table_name='sessions')
    op.drop_index('idx_sessions_status_priority', table_name='sessions')
    
    # Drop tables
    op.drop_table('session_checkpoints')
    op.drop_table('session_metrics')
    op.drop_table('sessions')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS session_priority")
    op.execute("DROP TYPE IF EXISTS session_type")
    op.execute("DROP TYPE IF EXISTS session_status")
