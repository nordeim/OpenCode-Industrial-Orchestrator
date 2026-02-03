"""
INDUSTRIAL TASK DTOs
Data Transfer Objects for Task API layer with Pydantic validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from .agent_dtos import AgentCapabilityDTO


class TaskComplexityLevelDTO(str, Enum):
    """Task complexity level for API layer."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class TaskPriorityDTO(str, Enum):
    """Task priority for API layer."""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class TaskStatusDTO(str, Enum):
    """Task status for API layer."""
    PENDING = "pending"
    READY = "ready"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TaskDependencyTypeDTO(str, Enum):
    """Task dependency types for API layer."""
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"


# =============================================================================
# REQUEST DTOs
# =============================================================================

class CreateTaskRequest(BaseModel):
    """Request to create a new task."""
    
    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Task title",
        json_schema_extra={"example": "Implement user authentication"}
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed task description"
    )
    session_id: UUID = Field(
        ...,
        description="Parent session ID"
    )
    parent_task_id: Optional[UUID] = Field(
        default=None,
        description="Parent task ID for subtasks"
    )
    priority: TaskPriorityDTO = Field(
        default=TaskPriorityDTO.NORMAL,
        description="Task priority"
    )
    required_capabilities: Optional[List[AgentCapabilityDTO]] = Field(
        default=None,
        description="Required agent capabilities"
    )
    estimated_hours: Optional[float] = Field(
        default=None,
        ge=0.1,
        le=1000.0,
        description="Estimated hours to complete"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        max_length=20,
        description="Task tags"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )


class UpdateTaskRequest(BaseModel):
    """Request to update a task."""
    
    title: Optional[str] = Field(default=None, min_length=5, max_length=200)
    description: Optional[str] = Field(default=None, min_length=10, max_length=5000)
    priority: Optional[TaskPriorityDTO] = None
    required_capabilities: Optional[List[AgentCapabilityDTO]] = None
    estimated_hours: Optional[float] = Field(default=None, ge=0.1, le=1000.0)
    tags: Optional[List[str]] = Field(default=None, max_length=20)
    metadata: Optional[Dict[str, Any]] = None


class UpdateTaskStatusRequest(BaseModel):
    """Request to update task status."""
    
    status: TaskStatusDTO = Field(
        ...,
        description="New task status"
    )
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Task result (for completed/failed)"
    )
    error_message: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Error message (for failed status)"
    )


class DecomposeTaskRequest(BaseModel):
    """Request to decompose a task into subtasks."""
    
    apply_templates: bool = Field(
        default=True,
        description="Apply decomposition templates"
    )
    apply_rules: bool = Field(
        default=True,
        description="Apply decomposition rules"
    )
    max_depth: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum decomposition depth"
    )
    auto_estimate: bool = Field(
        default=True,
        description="Automatically estimate complexity"
    )
    template_name: Optional[str] = Field(
        default=None,
        description="Specific template to apply (microservice, crud, security)"
    )


class AddDependencyRequest(BaseModel):
    """Request to add task dependency."""
    
    depends_on_task_id: UUID = Field(
        ...,
        description="Task ID that this task depends on"
    )
    dependency_type: TaskDependencyTypeDTO = Field(
        default=TaskDependencyTypeDTO.FINISH_TO_START,
        description="Type of dependency"
    )
    is_required: bool = Field(
        default=True,
        description="Whether dependency is required"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Dependency description"
    )


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class TaskEstimateResponse(BaseModel):
    """Task estimate details."""
    
    model_config = ConfigDict(from_attributes=True)
    
    optimistic_hours: float = 0.0
    likely_hours: float = 0.0
    pessimistic_hours: float = 0.0
    expected_hours: float = Field(description="PERT expected hours")
    complexity_level: TaskComplexityLevelDTO
    estimated_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Estimate confidence"
    )


class TaskDependencyResponse(BaseModel):
    """Task dependency details."""
    
    source_task_id: UUID
    target_task_id: UUID
    dependency_type: TaskDependencyTypeDTO
    is_required: bool
    is_satisfied: bool = Field(description="Whether dependency is satisfied")
    description: Optional[str] = None


class TaskResponse(BaseModel):
    """Response containing task details."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    description: str
    status: TaskStatusDTO
    priority: TaskPriorityDTO
    complexity_level: TaskComplexityLevelDTO
    session_id: UUID
    parent_task_id: Optional[UUID] = None
    assigned_agent_id: Optional[UUID] = None
    required_capabilities: Optional[List[AgentCapabilityDTO]] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    tags: Optional[List[str]] = None
    
    # Computed fields
    is_leaf_task: bool = Field(description="No subtasks")
    is_root_task: bool = Field(description="No parent")
    can_start: bool = Field(description="Dependencies satisfied")
    is_blocked: bool = Field(description="Blocked by dependencies")
    
    # Optional nested data
    estimate: Optional[TaskEstimateResponse] = None
    dependencies: Optional[List[TaskDependencyResponse]] = None
    subtasks: Optional[List["TaskResponse"]] = None
    result: Optional[Dict[str, Any]] = None


class TaskListResponse(BaseModel):
    """List of tasks."""
    
    items: List[TaskResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int
    
    # Aggregates
    by_status: Dict[str, int] = Field(default_factory=dict)
    by_priority: Dict[str, int] = Field(default_factory=dict)
    by_complexity: Dict[str, int] = Field(default_factory=dict)


class TaskTreeResponse(BaseModel):
    """Hierarchical task tree."""
    
    id: UUID
    title: str
    status: TaskStatusDTO
    complexity_level: TaskComplexityLevelDTO
    progress_percentage: float
    depth: int = 0
    children: List["TaskTreeResponse"] = Field(default_factory=list)
    dependencies: List[UUID] = Field(
        default_factory=list,
        description="IDs of tasks this depends on"
    )


class DependencyGraphResponse(BaseModel):
    """Task dependency graph for visualization."""
    
    task_id: UUID
    nodes: List[Dict[str, Any]] = Field(
        description="Graph nodes (tasks)"
    )
    edges: List[Dict[str, Any]] = Field(
        description="Graph edges (dependencies)"
    )
    critical_path: List[UUID] = Field(
        default_factory=list,
        description="Critical path task IDs"
    )
    total_estimated_hours: float
    
    # Visualization hints
    layout_type: str = Field(
        default="dagre",
        description="Suggested layout algorithm"
    )


class DecompositionResultResponse(BaseModel):
    """Result of task decomposition."""
    
    root_task: TaskResponse
    subtasks_created: int
    max_depth_reached: int
    templates_applied: List[str]
    rules_applied: List[str]
    total_estimated_hours: float
    warnings: List[str] = Field(default_factory=list)


class TaskStatsResponse(BaseModel):
    """Aggregate task statistics."""
    
    total_tasks: int
    tasks_by_status: Dict[str, int]
    tasks_by_priority: Dict[str, int]
    tasks_by_complexity: Dict[str, int]
    completion_rate: float
    average_duration_hours: Optional[float]
    overdue_tasks: int
    blocked_tasks: int


# Enable forward reference resolution for recursive types
TaskResponse.model_rebuild()
TaskTreeResponse.model_rebuild()
