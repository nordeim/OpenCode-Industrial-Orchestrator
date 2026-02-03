"""
INDUSTRIAL-GRADE SESSION ENTITY
Core business entity representing an OpenCode execution session.
Designed for resilience, auditability, and precise state management.
"""

from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from ..value_objects.session_status import SessionStatus
from ..value_objects.execution_metrics import ExecutionMetrics
from ..events.session_events import SessionCreated, SessionStatusChanged
from ..exceptions.session_exceptions import InvalidSessionTransition


class SessionType(str, Enum):
    """Type of orchestration session"""
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"
    DEBUG = "debug"
    INTEGRATION = "integration"


class SessionPriority(int, Enum):
    """Execution priority level"""
    CRITICAL = 0    # Blocking failures, immediate attention
    HIGH = 1        # Core path, user-blocking
    MEDIUM = 2      # Important but can wait
    LOW = 3         # Background, non-urgent
    DEFERRED = 4    # Can be scheduled later


class SessionEntity(BaseModel):
    """
    Industrial Session Entity
    
    Key Design Principles:
    1. Immutable core fields (id, created_at)
    2. State machine enforcement via status transitions
    3. Audit trail through events
    4. Metrics-driven performance tracking
    5. Resource isolation via execution_context
    """
    
    # Immutable identifiers
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Business identity
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    session_type: SessionType = Field(default=SessionType.EXECUTION)
    priority: SessionPriority = Field(default=SessionPriority.MEDIUM)
    
    # State management
    status: SessionStatus = Field(default=SessionStatus.PENDING)
    status_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    parent_id: Optional[UUID] = None
    child_ids: List[UUID] = Field(default_factory=list)
    
    # Execution context
    agent_config: Dict[str, Any] = Field(default_factory=dict)
    model_identifier: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+$")
    initial_prompt: str = Field(..., min_length=1, max_length=10000)
    
    # Resource allocation
    max_duration_seconds: int = Field(default=3600, ge=60, le=86400)
    cpu_limit: Optional[float] = Field(None, ge=0.1, le=8.0)
    memory_limit_mb: Optional[int] = Field(None, ge=100, le=8192)
    
    # Metrics & telemetry
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    checkpoints: List[Dict[str, Any]] = Field(default_factory=list)
    
    # System metadata
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Domain events (not persisted, for CQRS)
    _events: List[Any] = []
    
    model_config = {
        "arbitrary_types_allowed": True,
        "validate_assignment": True,
    }
    
    @validator('title')
    def validate_title_format(cls, v: str) -> str:
        """Enforce industrial naming convention"""
        if not v.strip():
            raise ValueError("Session title cannot be empty")
        
        # Reject generic AI-generated titles
        generic_patterns = [
            'test session', 'new session', 'untitled',
            'coding task', 'development session'
        ]
        
        if v.lower() in generic_patterns:
            raise ValueError(f"Title '{v}' is too generic. Use descriptive, industrial naming")
        
        return v.strip()
    
    @validator('agent_config')
    def validate_agent_config(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure agent configuration follows industrial standards"""
        if not v:
            return {'default_agent': 'industrial-coder'}
        
        # Validate agent name format
        for agent_name in v.keys():
            if not agent_name.replace('_', '').replace('-', '').isalnum():
                raise ValueError(f"Invalid agent name: {agent_name}. Use alphanumeric with underscores/hyphens")
        
        return v
    
    def transition_to(self, new_status: SessionStatus) -> None:
        """
        Industrial-grade state transition with validation
        
        Design Principle: State changes are explicit, validated events
        """
        if not self.status.can_transition_to(new_status):
            raise InvalidSessionTransition(
                current_status=self.status,
                target_status=new_status,
                session_id=self.id
            )
        
        old_status = self.status
        self.status = new_status
        self.status_updated_at = datetime.now(timezone.utc)
        
        # Record state transition event
        event = SessionStatusChanged(
            session_id=self.id,
            old_status=old_status,
            new_status=new_status,
            timestamp=self.status_updated_at
        )
        self._events.append(event)
    
    def start_execution(self) -> None:
        """Begin session execution with validation"""
        if self.status != SessionStatus.PENDING:
            raise InvalidSessionTransition(
                current_status=self.status,
                target_status=SessionStatus.RUNNING,
                session_id=self.id,
                reason="Can only start from PENDING state"
            )
        
        self.transition_to(SessionStatus.RUNNING)
        self.metrics.started_at = datetime.now(timezone.utc)
    
    def complete_with_result(self, result: Dict[str, Any]) -> None:
        """Mark session as completed with execution results"""
        self.transition_to(SessionStatus.COMPLETED)
        self.metrics.completed_at = datetime.now(timezone.utc)
        self.metrics.result = result
        
        # Calculate duration
        if self.metrics.started_at:
            duration = (self.metrics.completed_at - self.metrics.started_at).total_seconds()
            self.metrics.execution_duration_seconds = duration
    
    def fail_with_error(self, error: Exception, error_context: Dict[str, Any] = None) -> None:
        """Handle session failure with detailed error context"""
        self.transition_to(SessionStatus.FAILED)
        self.metrics.failed_at = datetime.now(timezone.utc)
        self.metrics.error = {
            'type': error.__class__.__name__,
            'message': str(error),
            'context': error_context or {}
        }
    
    def add_checkpoint(self, data: Dict[str, Any]) -> None:
        """Add execution checkpoint for recovery"""
        checkpoint = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': data,
            'sequence': len(self.checkpoints) + 1
        }
        self.checkpoints.append(checkpoint)
        
        # Limit checkpoint history
        if len(self.checkpoints) > 100:
            self.checkpoints = self.checkpoints[-100:]
    
    def get_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Retrieve most recent checkpoint for recovery"""
        if not self.checkpoints:
            return None
        return self.checkpoints[-1]
    
    def collect_events(self) -> List[Any]:
        """Collect and clear domain events for publishing"""
        events = self._events.copy()
        self._events.clear()
        return events
    
    def calculate_health_score(self) -> float:
        """Calculate session health score (0.0 to 1.0)"""
        if self.status == SessionStatus.COMPLETED:
            return 1.0
        
        if self.status == SessionStatus.FAILED:
            return 0.0
        
        # Calculate based on duration vs limit
        if self.status == SessionStatus.RUNNING and self.metrics.started_at:
            elapsed = (datetime.now(timezone.utc) - self.metrics.started_at).total_seconds()
            progress_ratio = min(elapsed / self.max_duration_seconds, 1.0)
            
            # Penalize long-running sessions
            if progress_ratio > 0.9:
                return 0.3  # At risk
            elif progress_ratio > 0.7:
                return 0.7  # Warning
            else:
                return 0.9  # Healthy
        
        return 0.8  # Default for other states
    
    def is_recoverable(self) -> bool:
        """Determine if session can be recovered from failure"""
        recoverable_statuses = {
            SessionStatus.FAILED,
            SessionStatus.TIMEOUT,
            SessionStatus.STOPPED
        }
        
        return (
            self.status in recoverable_statuses and
            len(self.checkpoints) > 0 and
            self.metrics.retry_count < 3
        )
