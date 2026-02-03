"""
INDUSTRIAL SESSION DTOs
Data Transfer Objects for Session API layer with Pydantic validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class SessionTypeDTO(str, Enum):
    """Session type for API layer."""
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"
    DEBUG = "debug"
    INTEGRATION = "integration"


class SessionPriorityDTO(int, Enum):
    """Session priority for API layer."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    DEFERRED = 4


class SessionStatusDTO(str, Enum):
    """Session status for API layer."""
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


# =============================================================================
# REQUEST DTOs
# =============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create a new session."""
    
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r"^[A-Z][A-Za-z0-9_-]*$",
        description="Industrial session title (must start with uppercase)",
        json_schema_extra={"example": "Session-ProjectAlpha-001"}
    )
    initial_prompt: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Task description or prompt for the session",
        json_schema_extra={"example": "Implement user authentication with JWT tokens"}
    )
    session_type: SessionTypeDTO = Field(
        default=SessionTypeDTO.EXECUTION,
        description="Type of orchestration session"
    )
    priority: SessionPriorityDTO = Field(
        default=SessionPriorityDTO.MEDIUM,
        description="Execution priority level"
    )
    agent_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional agent configuration overrides"
    )
    max_duration_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Maximum session duration in seconds"
    )
    parent_session_id: Optional[UUID] = Field(
        default=None,
        description="Parent session ID for hierarchical sessions"
    )
    created_by: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Creator identifier"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        max_length=20,
        description="Tags for categorization"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )


class UpdateSessionRequest(BaseModel):
    """Request to update session (partial update)."""
    
    title: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=100,
        pattern=r"^[A-Z][A-Za-z0-9_-]*$"
    )
    priority: Optional[SessionPriorityDTO] = None
    agent_config: Optional[Dict[str, Any]] = None
    max_duration_seconds: Optional[int] = Field(default=None, ge=60, le=86400)
    tags: Optional[List[str]] = Field(default=None, max_length=20)
    metadata: Optional[Dict[str, Any]] = None


class CompleteSessionRequest(BaseModel):
    """Request to complete a session."""
    
    result: Dict[str, Any] = Field(
        ...,
        description="Execution result data"
    )
    success_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Success rate (0.0 to 1.0)"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )


class FailSessionRequest(BaseModel):
    """Request to mark session as failed."""
    
    error_message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Error message"
    )
    error_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Error code for categorization"
    )
    error_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error context"
    )
    retryable: bool = Field(
        default=True,
        description="Whether the failure is retryable"
    )


class AddCheckpointRequest(BaseModel):
    """Request to add a checkpoint."""
    
    checkpoint_data: Dict[str, Any] = Field(
        ...,
        description="Checkpoint state data"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Checkpoint metadata"
    )


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class SessionMetricsResponse(BaseModel):
    """Session execution metrics."""
    
    model_config = ConfigDict(from_attributes=True)
    
    success_rate: float = Field(description="Overall success rate")
    code_quality_score: Optional[float] = Field(default=None)
    tokens_used: int = Field(default=0)
    api_calls_count: int = Field(default=0)
    api_errors_count: int = Field(default=0)
    execution_time_seconds: Optional[float] = Field(default=None)


class SessionCheckpointResponse(BaseModel):
    """Session checkpoint data."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    sequence: int
    data: Dict[str, Any]
    created_at: datetime


class SessionResponse(BaseModel):
    """Response containing session details."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    status: SessionStatusDTO
    session_type: SessionTypeDTO
    priority: SessionPriorityDTO
    initial_prompt: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parent_session_id: Optional[UUID] = None
    created_by: Optional[str] = None
    tags: Optional[List[str]] = None
    health_score: Optional[float] = Field(
        default=None,
        description="Session health score (0.0 to 1.0)"
    )
    is_recoverable: Optional[bool] = Field(
        default=None,
        description="Whether session can be recovered from failure"
    )
    
    # Optional nested data
    metrics: Optional[SessionMetricsResponse] = None
    checkpoints: Optional[List[SessionCheckpointResponse]] = None


class SessionListResponse(BaseModel):
    """Paginated list of sessions."""
    
    items: List[SessionResponse]
    total: int = Field(description="Total number of items")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, le=100, description="Items per page")
    total_pages: int = Field(ge=0, description="Total number of pages")
    
    @classmethod
    def from_results(
        cls,
        items: List[SessionResponse],
        total: int,
        page: int,
        page_size: int
    ) -> "SessionListResponse":
        """Factory method to create response with calculated total pages."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


class SessionTreeResponse(BaseModel):
    """Hierarchical session tree."""
    
    id: UUID
    title: str
    status: SessionStatusDTO
    depth: int = Field(ge=0)
    children: List["SessionTreeResponse"] = Field(default_factory=list)


class SessionStatsResponse(BaseModel):
    """Aggregate session statistics."""
    
    total_sessions: int
    active_sessions: int
    completed_sessions: int
    failed_sessions: int
    average_duration_seconds: Optional[float]
    average_success_rate: Optional[float]
    sessions_by_status: Dict[str, int]
    sessions_by_type: Dict[str, int]
    sessions_by_priority: Dict[str, int]


# =============================================================================
# ERROR RESPONSES
# =============================================================================

class SessionErrorResponse(BaseModel):
    """Error response for session operations."""
    
    error_code: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )
    session_id: Optional[UUID] = Field(
        default=None,
        description="Related session ID if applicable"
    )
    retryable: bool = Field(
        default=False,
        description="Whether the operation can be retried"
    )
    retry_after_seconds: Optional[int] = Field(
        default=None,
        description="Suggested retry delay"
    )


# Enable forward reference resolution for recursive types
SessionTreeResponse.model_rebuild()
