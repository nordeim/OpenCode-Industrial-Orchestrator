"""
INDUSTRIAL AGENT DTOs
Data Transfer Objects for Agent API layer with Pydantic validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class AgentTypeDTO(str, Enum):
    """Agent specialization types for API layer."""
    ARCHITECT = "architect"
    IMPLEMENTER = "implementer"
    REVIEWER = "reviewer"
    DEBUGGER = "debugger"
    INTEGRATOR = "integrator"
    ORCHESTRATOR = "orchestrator"
    ANALYST = "analyst"
    OPTIMIZER = "optimizer"


class AgentCapabilityDTO(str, Enum):
    """Agent capabilities for API layer."""
    # Analysis
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    SYSTEM_DESIGN = "system_design"
    ARCHITECTURE_PLANNING = "architecture_planning"
    # Implementation
    BACKEND_DEVELOPMENT = "backend_development"
    FRONTEND_DEVELOPMENT = "frontend_development"
    DATABASE_DESIGN = "database_design"
    API_DEVELOPMENT = "api_development"
    # Quality
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    # Debugging
    BUG_FIXING = "bug_fixing"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    ERROR_HANDLING = "error_handling"
    # DevOps
    CI_CD = "ci_cd"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    SCALING = "scaling"
    # Orchestration
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    RESOURCE_ALLOCATION = "resource_allocation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    PROGRESS_TRACKING = "progress_tracking"


class AgentPerformanceTierDTO(str, Enum):
    """Agent performance tier for API layer."""
    ELITE = "elite"
    ADVANCED = "advanced"
    COMPETENT = "competent"
    TRAINEE = "trainee"
    DEGRADED = "degraded"


class AgentLoadLevelDTO(str, Enum):
    """Agent load level for API layer."""
    IDLE = "idle"
    OPTIMAL = "optimal"
    HIGH = "high"
    CRITICAL = "critical"
    OVERLOADED = "overloaded"


# =============================================================================
# REQUEST DTOs
# =============================================================================

class RegisterAgentRequest(BaseModel):
    """Request to register a new agent."""
    
    name: str = Field(
        ...,
        min_length=5,
        max_length=50,
        pattern=r"^AGENT-[A-Z0-9-]+$",
        description="Agent name (must follow AGENT-XXX pattern)",
        json_schema_extra={"example": "AGENT-BACKEND-001"}
    )
    agent_type: AgentTypeDTO = Field(
        ...,
        description="Agent specialization type"
    )
    capabilities: List[AgentCapabilityDTO] = Field(
        ...,
        min_length=1,
        description="Agent capabilities"
    )
    max_concurrent_capacity: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum concurrent tasks"
    )
    preferred_technologies: Optional[List[str]] = Field(
        default=None,
        max_length=20,
        description="Preferred technology stack"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional agent metadata"
    )
    
    @field_validator('capabilities')
    @classmethod
    def validate_capabilities_for_type(cls, v: List[AgentCapabilityDTO], info) -> List[AgentCapabilityDTO]:
        """Validate capabilities align with agent type (basic validation)."""
        # Allow all capabilities for now, more strict validation in domain layer
        return v


class DeregisterAgentRequest(BaseModel):
    """Request to deregister an agent."""
    
    reason: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Reason for deregistration"
    )
    graceful: bool = Field(
        default=True,
        description="Wait for current tasks to complete"
    )


class RouteTaskRequest(BaseModel):
    """Request to route a task to an agent."""
    
    task_description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Task description for capability matching"
    )
    required_capabilities: List[AgentCapabilityDTO] = Field(
        ...,
        min_length=1,
        description="Required agent capabilities"
    )
    preferred_agent_type: Optional[AgentTypeDTO] = Field(
        default=None,
        description="Preferred agent type"
    )
    preferred_agent_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Preferred specific agents"
    )
    min_performance_tier: Optional[AgentPerformanceTierDTO] = Field(
        default=None,
        description="Minimum required performance tier"
    )
    estimated_complexity: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Estimated task complexity (1.0 = normal)"
    )


class UpdateAgentPerformanceRequest(BaseModel):
    """Request to update agent performance metrics."""
    
    task_success: bool = Field(
        ...,
        description="Whether the task was successful"
    )
    partial_success: bool = Field(
        default=False,
        description="Partial success flag"
    )
    quality_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Quality score (0.0 to 1.0)"
    )
    execution_time_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Task execution time"
    )
    tokens_used: Optional[int] = Field(
        default=None,
        ge=0,
        description="Tokens consumed"
    )
    cost_usd: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Task cost in USD"
    )


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class AgentPerformanceMetricsResponse(BaseModel):
    """Agent performance metrics response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    partial_successes: int = 0
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    average_quality_score: Optional[float] = None
    average_execution_time_seconds: Optional[float] = None
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    performance_tier: AgentPerformanceTierDTO


class AgentLoadMetricsResponse(BaseModel):
    """Agent load metrics response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    current_concurrent_tasks: int = 0
    max_concurrent_capacity: int = 5
    queue_length: int = 0
    utilization_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    load_level: AgentLoadLevelDTO
    can_accept_task: bool = True


class AgentResponse(BaseModel):
    """Response containing agent details."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    agent_type: AgentTypeDTO
    capabilities: List[AgentCapabilityDTO]
    performance_tier: AgentPerformanceTierDTO
    load_level: AgentLoadLevelDTO
    is_available: bool = Field(description="Whether agent can accept new tasks")
    created_at: datetime
    last_heartbeat_at: Optional[datetime] = None
    preferred_technologies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Optional nested data
    performance_metrics: Optional[AgentPerformanceMetricsResponse] = None
    load_metrics: Optional[AgentLoadMetricsResponse] = None


class AgentListResponse(BaseModel):
    """List of agents."""
    
    items: List[AgentResponse]
    total: int
    available_count: int = Field(description="Number of available agents")
    by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by agent type"
    )
    by_capability: Dict[str, int] = Field(
        default_factory=dict,
        description="Count by capability"
    )


class AgentPerformanceSummaryResponse(BaseModel):
    """Comprehensive agent performance summary."""
    
    agent_id: UUID
    agent_name: str
    agent_type: AgentTypeDTO
    
    # Performance
    performance_tier: AgentPerformanceTierDTO
    success_rate: float
    average_quality_score: Optional[float]
    
    # Workload
    load_level: AgentLoadLevelDTO
    utilization_percentage: float
    tasks_completed_today: int
    tasks_in_progress: int
    
    # Cost efficiency
    average_cost_per_task: Optional[float]
    average_tokens_per_task: Optional[int]
    
    # Trends
    success_rate_trend: str = Field(
        description="IMPROVING, STABLE, or DECLINING"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Performance recommendations"
    )


class RouteTaskResponse(BaseModel):
    """Response from task routing."""
    
    selected_agent: AgentResponse
    routing_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for routing decision"
    )
    alternatives: List[AgentResponse] = Field(
        default_factory=list,
        description="Alternative agents considered"
    )
    routing_reason: str = Field(
        description="Explanation for routing decision"
    )


class AgentStatsResponse(BaseModel):
    """Aggregate agent statistics."""
    
    total_agents: int
    available_agents: int
    agents_by_type: Dict[str, int]
    agents_by_tier: Dict[str, int]
    agents_by_load_level: Dict[str, int]
    overall_utilization: float
    average_success_rate: float
