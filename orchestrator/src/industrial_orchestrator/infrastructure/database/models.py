"""
INDUSTRIAL DATABASE MODELS
SQLAlchemy models with industrial-grade features:
1. Soft deletion with audit trail
2. Optimistic concurrency control
3. Full-text search indexing
4. Composite indexes for performance
5. Foreign key constraints with cascading
"""

import enum
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    Enum, JSON, Float, BigInteger, Index, UniqueConstraint, CheckConstraint,
    text, event, DDL
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, validates, deferred
from sqlalchemy.sql import func, expression

# Import Base and TimestampMixin from config to ensure single registry
from ..config.database import Base, TimestampMixin


class SessionStatusDB(enum.Enum):
    """Database representation of session status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    STOPPED = "stopped"
    CANCELLED = "cancelled"
    ORPHANED = "orphaned"
    DEGRADED = "degraded"


class SessionTypeDB(enum.Enum):
    """Database representation of session type"""
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"
    DEBUG = "debug"
    INTEGRATION = "integration"


class SessionPriorityDB(enum.IntEnum):
    """Database representation of session priority"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    DEFERRED = 4


class TenantModel(Base, TimestampMixin):
    """
    Industrial Tenant Database Model
    """
    __tablename__ = "tenants"
    
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()")
    )
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    
    max_concurrent_sessions = Column(Integer, default=10)
    max_tokens_per_month = Column(BigInteger, default=1000000)
    
    is_active = Column(Boolean, default=True)
    meta_data = Column(JSONB, nullable=False, default=text("'{}'::jsonb"))

    sessions = relationship("SessionModel", back_populates="tenant")
    fine_tuning_jobs = relationship("FineTuningJobModel", back_populates="tenant")


class SessionModel(Base, TimestampMixin):
    """
    Industrial Session Database Model
    
    Design Principles:
    1. Normalized schema for data integrity
    2. Indexed columns for performance
    3. JSONB for flexible metadata
    4. Soft deletion with audit trail
    5. Optimistic locking with versioning
    """
    
    __tablename__ = "sessions"
    __table_args__ = (
        # Composite indexes for common query patterns
        Index("idx_sessions_status_priority", "status", "priority"),
        Index("idx_sessions_parent_created", "parent_id", "created_at"),
        Index("idx_sessions_type_status", "session_type", "status"),
        Index("idx_sessions_tenant", "tenant_id"),
        
        # Partial indexes for active sessions
        Index(
            "idx_sessions_active",
            "status",
            postgresql_where=text("status IN ('pending', 'queued', 'running', 'paused')")
        ),
        
        # Full-text search index on title and description
        Index(
            "idx_sessions_search",
            text("to_tsvector('english', title || ' ' || COALESCE(description, ''))"),
            postgresql_using="gin"
        ),
        
        # Unique constraint for business rules
        UniqueConstraint("title", "created_by", name="uq_sessions_title_creator"),
        
        # Check constraints
        CheckConstraint(
            "max_duration_seconds >= 60 AND max_duration_seconds <= 86400",
            name="chk_sessions_duration"
        ),
        CheckConstraint(
            "COALESCE(cpu_limit, 0.1) >= 0.1 AND COALESCE(cpu_limit, 8.0) <= 8.0",
            name="chk_sessions_cpu_limit"
        ),
        
        # Table partitioning hint (would require PostgreSQL partitioning setup)
        {"postgresql_partition_by": "RANGE (created_at)"}
    )
    
    # Primary key with UUID for distributed systems
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        comment="Globally unique session identifier"
    )
    
    tenant_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE", name="fk_sessions_tenant"),
        nullable=False,
        index=True
    )
    
    # Business identity
    title = Column(
        String(200),
        nullable=False,
        index=True,
        comment="Industrial session title (descriptive, non-generic)"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Detailed session description and context"
    )
    
    session_type = Column(
        Enum(SessionTypeDB),
        nullable=False,
        default=SessionTypeDB.EXECUTION,
        index=True,
        comment="Type of orchestration session"
    )
    
    priority = Column(
        Enum(SessionPriorityDB),
        nullable=False,
        default=SessionPriorityDB.MEDIUM,
        index=True,
        comment="Execution priority level"
    )
    
    # State management
    status = Column(
        Enum(SessionStatusDB),
        nullable=False,
        default=SessionStatusDB.PENDING,
        index=True,
        comment="Current session status"
    )
    
    status_updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
        comment="Timestamp of last status change"
    )
    
    # Relationships (self-referential)
    parent_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "sessions.id",
            ondelete="SET NULL",
            name="fk_sessions_parent"
        ),
        nullable=True,
        index=True,
        comment="Parent session ID for hierarchical relationships"
    )
    
    # Execution context (JSONB for flexibility and queryability)
    agent_config = Column(
        JSONB,
        nullable=False,
        default=text("'{}'::jsonb"),
        server_default=text("'{}'::jsonb"),
        comment="Agent configuration with model parameters"
    )
    
    model_config = Column(
        String(100),
        nullable=True,
        comment="Primary model configuration (provider/model)"
    )
    
    initial_prompt = Column(
        Text,
        nullable=False,
        comment="Initial prompt or task description"
    )
    
    # Resource allocation
    max_duration_seconds = Column(
        Integer,
        nullable=False,
        default=3600,
        comment="Maximum execution duration in seconds"
    )
    
    cpu_limit = Column(
        Float,
        nullable=True,
        comment="CPU limit in cores (null = unlimited)"
    )
    
    memory_limit_mb = Column(
        Integer,
        nullable=True,
        comment="Memory limit in MB (null = unlimited)"
    )
    
    # Metrics (stored separately for performance)
    metrics_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "session_metrics.id",
            ondelete="CASCADE",
            name="fk_sessions_metrics"
        ),
        nullable=True,
        unique=True,
        comment="Reference to session metrics"
    )
    
    # System metadata
    created_by = Column(
        String(100),
        nullable=True,
        index=True,
        comment="User or system that created the session"
    )
    
    tags = Column(
        JSONB,
        nullable=False,
        default=text("'[]'::jsonb"),
        server_default=text("'[]'::jsonb"),
        comment="Session tags for categorization"
    )
    
    meta_data = Column(
        JSONB,
        nullable=False,
        default=text("'{}'::jsonb"),
        server_default=text("'{}'::jsonb"),
        comment="Arbitrary metadata for extensibility"
    )
    
    # Optimistic concurrency control
    version = Column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="Optimistic lock version for concurrent updates"
    )
    
    # Audit trail for data changes
    updated_by = Column(
        String(100),
        nullable=True,
        comment="User or system that last updated the session"
    )
    
    # Relationships
    tenant = relationship("TenantModel", back_populates="sessions")
    
    parent = relationship(
        "SessionModel",
        remote_side=[id],
        backref="children",
        foreign_keys=[parent_id]
    )
    
    metrics = relationship(
        "SessionMetricsModel",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    checkpoints = relationship(
        "SessionCheckpointModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionCheckpointModel.sequence"
    )
    
    @validates('title')
    def validate_title(self, key: str, value: str) -> str:
        """Enforce industrial naming conventions in database layer"""
        if not value or not value.strip():
            raise ValueError("Session title cannot be empty")
        
        # Reject generic titles
        generic_patterns = [
            'test session', 'new session', 'untitled',
            'coding task', 'development session'
        ]
        
        if value.lower() in generic_patterns:
            raise ValueError(f"Title '{value}' is too generic")
        
        return value.strip()
    
    @validates('agent_config')
    def validate_agent_config(self, key: str, value: dict) -> dict:
        """Validate agent configuration structure"""
        if not value:
            return {'default_agent': 'industrial-coder'}
        
        # Ensure it's a valid JSON object
        if not isinstance(value, dict):
            raise ValueError("Agent config must be a dictionary")
        
        return value
    
    @hybrid_property
    def is_active(self) -> bool:
        """Check if session is in active state"""
        active_statuses = {
            SessionStatusDB.PENDING,
            SessionStatusDB.QUEUED,
            SessionStatusDB.RUNNING,
            SessionStatusDB.PAUSED,
            SessionStatusDB.DEGRADED,
        }
        return self.status in active_statuses
    
    @is_active.expression
    def is_active(cls):
        """SQL expression for active status check"""
        return cls.status.in_([
            SessionStatusDB.PENDING,
            SessionStatusDB.QUEUED,
            SessionStatusDB.RUNNING,
            SessionStatusDB.PAUSED,
            SessionStatusDB.DEGRADED,
        ])
    
    @hybrid_property
    def is_terminal(self) -> bool:
        """Check if session is in terminal state"""
        terminal_statuses = {
            SessionStatusDB.COMPLETED,
            SessionStatusDB.PARTIALLY_COMPLETED,
            SessionStatusDB.FAILED,
            SessionStatusDB.TIMEOUT,
            SessionStatusDB.STOPPED,
            SessionStatusDB.CANCELLED,
            SessionStatusDB.ORPHANED,
        }
        return self.status in terminal_statuses
    
    @hybrid_property
    def duration_seconds(self) -> Optional[float]:
        """Calculate session duration based on timestamps"""
        if not self.metrics:
            return None
        
        if self.metrics.completed_at:
            return (self.metrics.completed_at - self.metrics.created_at).total_seconds()
        elif self.metrics.failed_at:
            return (self.metrics.failed_at - self.metrics.created_at).total_seconds()
        elif self.metrics.started_at:
            return (datetime.now(timezone.utc) - self.metrics.started_at).total_seconds()
        
        return None
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert model to dictionary (for serialization)"""
        data = {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "session_type": self.session_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "status_updated_at": self.status_updated_at.isoformat() if self.status_updated_at else None,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "agent_config": self.agent_config,
            "model_config": self.model_config,
            "initial_prompt": self.initial_prompt,
            "max_duration_seconds": self.max_duration_seconds,
            "cpu_limit": self.cpu_limit,
            "memory_limit_mb": self.memory_limit_mb,
            "created_by": self.created_by,
            "tags": self.tags,
            "metadata": self.meta_data,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
        
        if include_relationships:
            if self.metrics:
                data["metrics"] = self.metrics.to_dict()
            if self.checkpoints:
                data["checkpoints"] = [cp.to_dict() for cp in self.checkpoints]
            if self.children:
                data["child_ids"] = [str(child.id) for child in self.children]
        
        return data


class SessionMetricsModel(Base, TimestampMixin):
    """
    Industrial Session Metrics Database Model
    
    Separated from session for:
    1. Performance optimization (frequent updates)
    2. Historical data retention
    3. Efficient aggregation queries
    """
    
    __tablename__ = "session_metrics"
    __table_args__ = (
        Index("idx_metrics_session", "session_id"),
        Index("idx_metrics_created", "created_at"),
        Index("idx_metrics_duration", "execution_duration_seconds"),
        Index("idx_metrics_success", "success_rate"),
    )
    
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        comment="Unique metrics identifier"
    )
    
    session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "sessions.id",
            ondelete="CASCADE",
            name="fk_metrics_session"
        ),
        nullable=False,
        unique=True,
        index=True,
        comment="Reference to session"
    )
    
    # Timestamps
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When execution started"
    )
    
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When execution completed successfully"
    )
    
    failed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When execution failed"
    )
    
    # Duration metrics
    queue_duration_seconds = Column(
        Float,
        nullable=True,
        comment="Time spent in queue before execution"
    )
    
    execution_duration_seconds = Column(
        Float,
        nullable=True,
        comment="Actual execution time"
    )
    
    total_duration_seconds = Column(
        Float,
        nullable=True,
        comment="Total time from creation to completion"
    )
    
    # Resource utilization
    cpu_usage_percent = Column(
        Float,
        nullable=True,
        comment="Average CPU usage percentage"
    )
    
    memory_usage_mb = Column(
        Float,
        nullable=True,
        comment="Peak memory usage in MB"
    )
    
    disk_usage_mb = Column(
        Float,
        nullable=True,
        comment="Disk space used in MB"
    )
    
    network_bytes_sent = Column(
        BigInteger,
        nullable=True,
        comment="Total bytes sent over network"
    )
    
    network_bytes_received = Column(
        BigInteger,
        nullable=True,
        comment="Total bytes received over network"
    )
    
    # Performance counters
    total_tokens_used = Column(
        BigInteger,
        nullable=True,
        comment="Total tokens consumed by AI models"
    )
    
    api_calls_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of API calls made"
    )
    
    api_errors_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of API errors encountered"
    )
    
    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of retry attempts"
    )
    
    # Quality metrics
    success_rate = Column(
        Float,
        nullable=True,
        comment="Success rate (0.0 to 1.0)"
    )
    
    confidence_score = Column(
        Float,
        nullable=True,
        comment="Confidence score (0.0 to 1.0)"
    )
    
    code_quality_score = Column(
        Float,
        nullable=True,
        comment="Code quality score (0.0 to 1.0)"
    )
    
    # Results (JSONB for flexibility)
    result = Column(
        JSONB,
        nullable=True,
        comment="Execution results"
    )
    
    error = Column(
        JSONB,
        nullable=True,
        comment="Error details if execution failed"
    )
    
    warnings = Column(
        JSONB,
        nullable=False,
        default=text("'[]'::jsonb"),
        server_default=text("'[]'::jsonb"),
        comment="Warning messages encountered"
    )
    
    # Checkpointing
    checkpoint_count = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of checkpoints taken"
    )
    
    last_checkpoint_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last checkpoint"
    )
    
    # Cost tracking
    estimated_cost_usd = Column(
        Float,
        nullable=True,
        comment="Estimated cost in USD"
    )
    
    # Relationships
    session = relationship(
        "SessionModel",
        back_populates="metrics",
        uselist=False
    )
    
    @hybrid_property
    def api_error_rate(self) -> Optional[float]:
        """Calculate API error rate"""
        if self.api_calls_count == 0:
            return 0.0
        return self.api_errors_count / self.api_calls_count
    
    @hybrid_property
    def is_healthy(self) -> bool:
        """Determine if metrics indicate healthy execution"""
        if self.api_error_rate and self.api_error_rate > 0.1:
            return False  # More than 10% API errors
        
        if self.retry_count > 5:
            return False  # Excessive retries
        
        if self.warnings and len(self.warnings) > 10:
            return False  # Too many warnings
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "queue_duration_seconds": self.queue_duration_seconds,
            "execution_duration_seconds": self.execution_duration_seconds,
            "total_duration_seconds": self.total_duration_seconds,
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_mb": self.memory_usage_mb,
            "disk_usage_mb": self.disk_usage_mb,
            "network_bytes_sent": self.network_bytes_sent,
            "network_bytes_received": self.network_bytes_received,
            "total_tokens_used": self.total_tokens_used,
            "api_calls_count": self.api_calls_count,
            "api_errors_count": self.api_errors_count,
            "retry_count": self.retry_count,
            "success_rate": self.success_rate,
            "confidence_score": self.confidence_score,
            "code_quality_score": self.code_quality_score,
            "result": self.result,
            "error": self.error,
            "warnings": self.warnings,
            "checkpoint_count": self.checkpoint_count,
            "last_checkpoint_at": self.last_checkpoint_at.isoformat() if self.last_checkpoint_at else None,
            "estimated_cost_usd": self.estimated_cost_usd,
            "api_error_rate": self.api_error_rate,
            "is_healthy": self.is_healthy,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SessionCheckpointModel(Base):
    """
    Industrial Session Checkpoint Database Model
    
    Design Principles:
    1. Append-only log for audit trail
    2. Efficient querying by sequence
    3. Compressed storage for large data
    """
    
    __tablename__ = "session_checkpoints"
    __table_args__ = (
        Index("idx_checkpoints_session_seq", "session_id", "sequence"),
        Index("idx_checkpoints_timestamp", "session_id", "created_at"),
        UniqueConstraint("session_id", "sequence", name="uq_checkpoints_session_sequence"),
    )
    
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        comment="Unique checkpoint identifier"
    )
    
    session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "sessions.id",
            ondelete="CASCADE",
            name="fk_checkpoints_session"
        ),
        nullable=False,
        index=True,
        comment="Reference to session"
    )
    
    sequence = Column(
        Integer,
        nullable=False,
        comment="Checkpoint sequence number (1-based)"
    )
    
    data = Column(
        JSONB,
        nullable=False,
        comment="Checkpoint data snapshot"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Checkpoint creation timestamp"
    )
    
    meta_data = Column(
        JSONB,
        nullable=False,
        default=text("'{}'::jsonb"),
        server_default=text("'{}'::jsonb"),
        comment="Checkpoint metadata"
    )
    
    # Relationships
    session = relationship(
        "SessionModel",
        back_populates="checkpoints"
    )
    
    @validates('sequence')
    def validate_sequence(self, key: str, value: int) -> int:
        """Validate sequence is positive"""
        if value < 1:
            raise ValueError("Sequence must be positive")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary"""
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "sequence": self.sequence,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.meta_data,
        }


class FineTuningJobModel(Base, TimestampMixin):
    """
    Database model for fine-tuning jobs.
    """
    __tablename__ = "fine_tuning_jobs"
    
    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()")
    )
    
    tenant_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE", name="fk_fine_tuning_tenant"),
        nullable=False,
        index=True
    )
    
    base_model = Column(String(100), nullable=False)
    target_model_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    
    version = Column(JSONB, nullable=False)
    parameters = Column(JSONB, nullable=False)
    metrics = Column(JSONB, nullable=False)
    
    dataset_path = Column(String(500), nullable=True)
    sample_count = Column(Integer, default=0)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    tenant = relationship("TenantModel", back_populates="fine_tuning_jobs")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "base_model": self.base_model,
            "target_model_name": self.target_model_name,
            "status": self.status,
            "version": self.version,
            "parameters": self.parameters,
            "metrics": self.metrics,
            "dataset_path": self.dataset_path,
            "sample_count": self.sample_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Database-level functions and triggers
def create_industrial_triggers():
    """Create industrial-grade database triggers"""
    
    # Trigger to update parent's child_ids (denormalized for performance)
    update_child_ids_trigger = DDL("""
        CREATE OR REPLACE FUNCTION update_session_child_ids()
        RETURNS TRIGGER AS $$
        DECLARE
            child_ids_json JSONB;
        BEGIN
            -- When a session is created or parent_id changes
            IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND NEW.parent_id IS DISTINCT FROM OLD.parent_id) THEN
                -- Add child to parent's child_ids array
                IF NEW.parent_id IS NOT NULL THEN
                    UPDATE sessions
                    SET metadata = jsonb_set(
                        COALESCE(metadata, '{}'::jsonb),
                        '{child_ids}',
                        COALESCE(metadata->'child_ids', '[]'::jsonb) || to_jsonb(NEW.id::text)
                    )
                    WHERE id = NEW.parent_id;
                END IF;
                
                -- Remove child from old parent's child_ids array
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
            
            -- When a session is deleted (soft delete)
            IF TG_OP = 'UPDATE' AND NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL THEN
                -- Remove from parent's child_ids
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
        
        CREATE TRIGGER trg_update_child_ids
        AFTER INSERT OR UPDATE OF parent_id, deleted_at ON sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_session_child_ids();
    """)
    
    # Trigger to auto-update metrics timestamps
    update_metrics_timestamps_trigger = DDL("""
        CREATE OR REPLACE FUNCTION update_session_metrics_timestamps()
        RETURNS TRIGGER AS $$
        BEGIN
            -- When session status changes to RUNNING, update metrics.started_at
            IF NEW.status = 'running' AND OLD.status != 'running' THEN
                UPDATE session_metrics
                SET started_at = NEW.status_updated_at
                WHERE session_id = NEW.id;
            END IF;
            
            -- When session status changes to COMPLETED, update metrics.completed_at
            IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
                UPDATE session_metrics
                SET completed_at = NEW.status_updated_at
                WHERE session_id = NEW.id;
            END IF;
            
            -- When session status changes to FAILED, update metrics.failed_at
            IF NEW.status = 'failed' AND OLD.status != 'failed' THEN
                UPDATE session_metrics
                SET failed_at = NEW.status_updated_at
                WHERE session_id = NEW.id;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trg_update_metrics_timestamps
        AFTER UPDATE OF status ON sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_session_metrics_timestamps();
    """)
    
    # Trigger for optimistic concurrency control
    optimistic_lock_trigger = DDL("""
        CREATE OR REPLACE FUNCTION enforce_optimistic_lock()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Only check version on UPDATE
            IF TG_OP = 'UPDATE' THEN
                -- If version doesn't match, someone else modified the record
                IF NEW.version != OLD.version + 1 THEN
                    RAISE EXCEPTION 'Optimistic lock violation for session %: expected version %, got %',
                        OLD.id, OLD.version + 1, NEW.version
                    USING ERRCODE = '23505';
                END IF;
            END IF;
            
            -- For INSERT, set initial version
            IF TG_OP = 'INSERT' THEN
                NEW.version := 1;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trg_enforce_optimistic_lock
        BEFORE INSERT OR UPDATE ON sessions
        FOR EACH ROW
        EXECUTE FUNCTION enforce_optimistic_lock();
    """)
    
    return [
        update_child_ids_trigger,
        update_metrics_timestamps_trigger,
        optimistic_lock_trigger,
    ]


# Register event listeners for industrial features
@event.listens_for(SessionModel, 'before_insert')
def before_session_insert(mapper, connection, target):
    """Set default values and validate before insert"""
    if not target.status_updated_at:
        target.status_updated_at = datetime.now(timezone.utc)
    
    # Ensure metrics record exists
    if not target.metrics:
        target.metrics = SessionMetricsModel(session_id=target.id)


@event.listens_for(SessionModel, 'before_update')
def before_session_update(mapper, connection, target):
    """Update version and track changes before update"""
    # Increment version for optimistic locking
    target.version = target.version + 1
    
    # Update status timestamp if status changed
    if target.status != target.__dict__.get('status'):
        target.status_updated_at = datetime.now(timezone.utc)
