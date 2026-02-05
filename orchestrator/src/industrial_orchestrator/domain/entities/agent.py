"""
INDUSTRIAL AGENT ENTITY
Advanced agent models with specialization, performance tracking, and capability routing.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, ValidationInfo

from ..value_objects.session_status import SessionStatus
from ..exceptions.agent_exceptions import (
    AgentCapabilityMismatchError,
    AgentPerformanceDegradedError,
    AgentOverloadedError,
)


class AgentType(str, Enum):
    """Industrial agent specialization types"""
    ARCHITECT = "architect"          # System design and planning
    IMPLEMENTER = "implementer"      # Code generation and implementation
    REVIEWER = "reviewer"            # Code review and quality assurance
    DEBUGGER = "debugger"            # Problem diagnosis and fixing
    INTEGRATOR = "integrator"        # System integration and deployment
    ORCHESTRATOR = "orchestrator"    # Multi-agent coordination
    ANALYST = "analyst"              # Requirements analysis
    OPTIMIZER = "optimizer"          # Performance optimization


class AgentCapability(str, Enum):
    """Specific capabilities an agent can possess"""
    # Planning & Architecture
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    SYSTEM_DESIGN = "system_design"
    ARCHITECTURE_PLANNING = "architecture_planning"
    TASK_DECOMPOSITION = "task_decomposition"
    
    # Implementation
    CODE_GENERATION = "code_generation"
    TEST_GENERATION = "test_generation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    
    # Quality Assurance
    CODE_REVIEW = "code_review"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    
    # Problem Solving
    DEBUGGING = "debugging"
    BUG_FIXING = "bug_fixing"
    TROUBLESHOOTING = "troubleshooting"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    OPTIMIZATION = "optimization"
    
    # Integration & Operations
    DEPLOYMENT = "deployment"
    CONFIGURATION = "configuration"
    MONITORING = "monitoring"
    SCALING = "scaling"
    
    # Coordination
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    RESOURCE_ALLOCATION = "resource_allocation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    PROGRESS_TRACKING = "progress_tracking"


class AgentPerformanceTier(str, Enum):
    """Performance classification based on historical success"""
    ELITE = "elite"          # > 95% success rate, exceptional quality
    ADVANCED = "advanced"    # 85-95% success rate, high quality
    PREMIUM = "premium"      # High performance tier
    STANDARD = "standard"    # Default starting tier
    COMPETENT = "competent"  # 70-85% success rate, reliable
    TRAINEE = "trainee"      # < 70% success rate, learning
    DEGRADED = "degraded"    # Performance issues detected


class AgentLoadLevel(str, Enum):
    """Current workload classification"""
    IDLE = "idle"            # 0-20% capacity utilized
    LOW = "idle"             # Alias for IDLE
    OPTIMAL = "optimal"      # 20-70% capacity utilized
    HIGH = "high"            # 70-90% capacity utilized
    CRITICAL = "critical"    # > 90% capacity utilized
    OVERLOADED = "overloaded" # Exceeding capacity


class AgentPerformanceMetrics(BaseModel):
    """Industrial-grade performance tracking for agents"""
    
    total_tasks: int = Field(default=0, ge=0)
    successful_tasks: int = Field(default=0, ge=0)
    failed_tasks: int = Field(default=0, ge=0)
    partially_successful_tasks: int = Field(default=0, ge=0)
    
    # Quality metrics
    average_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    code_coverage_impact: float = Field(default=0.0, ge=0.0, le=1.0)
    security_improvement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    performance_improvement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Efficiency metrics
    average_execution_time_seconds: float = Field(default=0.0, ge=0.0)
    tokens_per_task: float = Field(default=0.0, ge=0.0)
    cost_per_task_usd: float = Field(default=0.0, ge=0.0)
    
    # Specialization metrics
    capability_success_rates: Dict[AgentCapability, float] = Field(default_factory=dict)
    technology_success_rates: Dict[str, float] = Field(default_factory=dict)
    
    # Temporal metrics
    success_rate_trend_30d: float = Field(default=0.0)  # Percentage change
    quality_trend_30d: float = Field(default=0.0)       # Percentage change
    efficiency_trend_30d: float = Field(default=0.0)    # Percentage change
    
    @property
    def overall_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_tasks == 0:
            return 0.0
        return (self.successful_tasks + self.partially_successful_tasks * 0.5) / self.total_tasks
    
    @property
    def complete_success_rate(self) -> float:
        """Calculate complete success rate (excluding partial successes)"""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks
    
    def calculate_performance_tier(self) -> AgentPerformanceTier:
        """Determine performance tier based on metrics"""
        success_rate = self.overall_success_rate
        
        if success_rate >= 0.95 and self.average_quality_score >= 0.9:
            return AgentPerformanceTier.ELITE
        elif success_rate >= 0.85:
            return AgentPerformanceTier.ADVANCED
        elif success_rate >= 0.70:
            return AgentPerformanceTier.COMPETENT
        elif success_rate >= 0.50:
            return AgentPerformanceTier.TRAINEE
        else:
            return AgentPerformanceTier.DEGRADED
    
    def record_task_result(
        self,
        success: bool,
        partial_success: bool = False,
        quality_score: Optional[float] = None,
        execution_time_seconds: Optional[float] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        capabilities_used: Optional[List[AgentCapability]] = None,
        technologies: Optional[List[str]] = None
    ) -> None:
        """Record task execution result"""
        self.total_tasks += 1
        
        if success and not partial_success:
            self.successful_tasks += 1
        elif partial_success:
            self.partially_successful_tasks += 1
        else:
            self.failed_tasks += 1
        
        # Update quality metrics
        if quality_score is not None:
            # Moving average update
            current_total = self.total_tasks - 1  # Excluding current
            self.average_quality_score = (
                (self.average_quality_score * current_total) + quality_score
            ) / self.total_tasks
        
        # Update efficiency metrics
        if execution_time_seconds is not None:
            current_total = self.total_tasks - 1
            self.average_execution_time_seconds = (
                (self.average_execution_time_seconds * current_total) + execution_time_seconds
            ) / self.total_tasks
        
        if tokens_used is not None:
            current_total = self.total_tasks - 1
            self.tokens_per_task = (
                (self.tokens_per_task * current_total) + tokens_used
            ) / self.total_tasks
        
        if cost_usd is not None:
            current_total = self.total_tasks - 1
            self.cost_per_task_usd = (
                (self.cost_per_task_usd * current_total) + cost_usd
            ) / self.total_tasks
        
        # Update capability success rates
        if capabilities_used:
            for capability in capabilities_used:
                current_rate = self.capability_success_rates.get(capability, 0.0)
                current_count = self.total_tasks - 1
                new_rate = (
                    (current_rate * current_count) + (1.0 if success else 0.0)
                ) / self.total_tasks
                self.capability_success_rates[capability] = new_rate
        
        # Update technology success rates
        if technologies:
            for tech in technologies:
                current_rate = self.technology_success_rates.get(tech, 0.0)
                current_count = self.total_tasks - 1
                new_rate = (
                    (current_rate * current_count) + (1.0 if success else 0.0)
                ) / self.total_tasks
                self.technology_success_rates[tech] = new_rate


class AgentLoadMetrics(BaseModel):
    """Real-time load tracking for agents"""
    
    current_concurrent_tasks: int = Field(default=0, ge=0)
    max_concurrent_capacity: int = Field(default=5, ge=1)
    queue_length: int = Field(default=0, ge=0)
    
    # Resource utilization (0.0 to 1.0)
    cpu_utilization: float = Field(default=0.0, ge=0.0, le=1.0)
    memory_utilization: float = Field(default=0.0, ge=0.0, le=1.0)
    network_utilization: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Temporal load patterns
    load_trend_1h: float = Field(default=0.0)  # Percentage change
    peak_load_today: int = Field(default=0, ge=0)
    
    @property
    def utilization_percentage(self) -> float:
        """Calculate overall utilization percentage"""
        return self.current_concurrent_tasks / self.max_concurrent_capacity
    
    @property
    def load_level(self) -> AgentLoadLevel:
        """Determine current load level"""
        utilization = self.utilization_percentage
        
        if utilization <= 0.2:
            return AgentLoadLevel.IDLE
        elif utilization <= 0.7:
            return AgentLoadLevel.OPTIMAL
        elif utilization <= 0.9:
            return AgentLoadLevel.HIGH
        elif utilization <= 1.0:
            return AgentLoadLevel.CRITICAL
        else:
            return AgentLoadLevel.OVERLOADED
    
    def can_accept_task(self, estimated_complexity: float = 1.0) -> bool:
        """Check if agent can accept a new task"""
        if self.load_level == AgentLoadLevel.OVERLOADED:
            return False
        
        # Adjust for task complexity
        effective_load = self.current_concurrent_tasks + estimated_complexity
        
        # Don't exceed capacity
        if effective_load > self.max_concurrent_capacity:
            return False
        
        # Don't exceed critical threshold for complex tasks
        if estimated_complexity > 2.0 and self.load_level == AgentLoadLevel.CRITICAL:
            return False
        
        return True
    
    def increment_load(self, estimated_complexity: float = 1.0) -> None:
        """Increment load for new task"""
        self.current_concurrent_tasks += estimated_complexity
        self.queue_length = max(0, self.queue_length - 1)
        
        # Update peak load
        if self.current_concurrent_tasks > self.peak_load_today:
            self.peak_load_today = self.current_concurrent_tasks
    
    def decrement_load(self, estimated_complexity: float = 1.0) -> None:
        """Decrement load for completed task"""
        self.current_concurrent_tasks = max(0, self.current_concurrent_tasks - estimated_complexity)


class AgentEntity(BaseModel):
    """
    Industrial Agent Entity
    
    Advanced agent model with:
    1. Specialized capabilities
    2. Performance tracking
    3. Load management
    4. Dynamic routing preferences
    """
    
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID = Field(...)  # Required for isolation
    name: str = Field(..., min_length=1, max_length=100)
    agent_type: AgentType
    description: Optional[str] = Field(None, max_length=500)
    
    # Core capabilities
    primary_capabilities: List[AgentCapability] = Field(default_factory=list)
    secondary_capabilities: List[AgentCapability] = Field(default_factory=list)
    
    # Configuration
    model_identifier: str = Field(..., pattern=r"^[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-\.]+$")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1000, le=100000)
    system_prompt_template: str = Field(default="")
    
    # Performance tracking
    performance: AgentPerformanceMetrics = Field(default_factory=AgentPerformanceMetrics)
    load: AgentLoadMetrics = Field(default_factory=AgentLoadMetrics)
    
    # Specialization
    preferred_technologies: List[str] = Field(default_factory=list)
    avoided_technologies: List[str] = Field(default_factory=list)
    complexity_preference: str = Field(default="medium", pattern="^(simple|medium|complex|expert)$")
    
    # Operational state
    is_active: bool = Field(default=True)
    last_active_at: Optional[datetime] = None
    maintenance_mode: bool = Field(default=False)
    
    # Routing preferences
    preferred_session_types: List[str] = Field(default_factory=list)
    max_task_duration_hours: float = Field(default=4.0, ge=0.5, le=24.0)
    min_quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # Metadata
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @field_validator('name')
    @classmethod
    def validate_agent_name(cls, v: str) -> str:
        """Enforce industrial naming conventions"""
        if not v.strip():
            raise ValueError("Agent name cannot be empty")
        
        # Reject generic AI-generated names
        generic_patterns = [
            'ai assistant', 'bot', 'helper', 'agent',
            'coder', 'reviewer', 'debugger'  # Too generic without qualifiers
        ]
        
        if any(pattern in v.lower() for pattern in generic_patterns):
            raise ValueError(f"Agent name '{v}' is too generic. Use descriptive, unique naming.")
        
        # Require capitalization and proper formatting
        if v == v.lower() or v == v.upper():
            raise ValueError(f"Agent name '{v}' should use proper capitalization")
        
        return v.strip()
    
    @field_validator('primary_capabilities')
    @classmethod
    def validate_capabilities(cls, v: List[AgentCapability], info: ValidationInfo) -> List[AgentCapability]:
        """Ensure capabilities align with agent type"""
        agent_type = info.data.get('agent_type')
        
        if not v:
            raise ValueError("Agent must have at least one primary capability")
        
        # Type-specific capability validation
        type_capability_map = {
            AgentType.ARCHITECT: {
                AgentCapability.REQUIREMENTS_ANALYSIS,
                AgentCapability.SYSTEM_DESIGN,
                AgentCapability.ARCHITECTURE_PLANNING,
                AgentCapability.TASK_DECOMPOSITION,
            },
            AgentType.IMPLEMENTER: {
                AgentCapability.CODE_GENERATION,
                AgentCapability.TEST_GENERATION,
                AgentCapability.DOCUMENTATION,
                AgentCapability.REFACTORING,
            },
            AgentType.REVIEWER: {
                AgentCapability.CODE_REVIEW,
                AgentCapability.SECURITY_AUDIT,
                AgentCapability.PERFORMANCE_ANALYSIS,
                AgentCapability.COMPLIANCE_CHECK,
            },
            AgentType.DEBUGGER: {
                AgentCapability.DEBUGGING,
                AgentCapability.TROUBLESHOOTING,
                AgentCapability.ROOT_CAUSE_ANALYSIS,
                AgentCapability.OPTIMIZATION,
            },
            AgentType.INTEGRATOR: {
                AgentCapability.DEPLOYMENT,
                AgentCapability.CONFIGURATION,
                AgentCapability.MONITORING,
                AgentCapability.SCALING,
            },
            AgentType.ORCHESTRATOR: {
                AgentCapability.WORKFLOW_ORCHESTRATION,
                AgentCapability.RESOURCE_ALLOCATION,
                AgentCapability.CONFLICT_RESOLUTION,
                AgentCapability.PROGRESS_TRACKING,
            },
        }
        
        allowed_capabilities = type_capability_map.get(agent_type, set())
        
        for capability in v:
            if capability not in allowed_capabilities:
                raise ValueError(
                    f"Capability '{capability}' not allowed for agent type '{agent_type}'. "
                    f"Allowed: {allowed_capabilities}"
                )
        
        return v
    
    @model_validator(mode='after')
    def validate_agent_configuration(self) -> 'AgentEntity':
        """Comprehensive agent configuration validation"""
        # Ensure system prompt contains role information
        if not self.system_prompt_template or len(self.system_prompt_template.strip()) < 50:
            raise ValueError("System prompt must be at least 50 characters and define agent role")
        
        # Validate model configuration
        if '/' not in self.model_identifier:
            raise ValueError("Model identifier must be in format 'provider/model_name'")
        
        # Set default max_tokens based on agent type
        if self.max_tokens is None:
            type_token_map = {
                AgentType.ARCHITECT: 4000,
                AgentType.IMPLEMENTER: 8000,
                AgentType.REVIEWER: 2000,
                AgentType.DEBUGGER: 4000,
                AgentType.INTEGRATOR: 3000,
                AgentType.ORCHESTRATOR: 2000,
                AgentType.ANALYST: 3000,
                AgentType.OPTIMIZER: 2000,
            }
            self.max_tokens = type_token_map.get(self.agent_type, 4000)
        
        return self
    
    @property
    def all_capabilities(self) -> Set[AgentCapability]:
        """Get all capabilities (primary + secondary)"""
        return set(self.primary_capabilities) | set(self.secondary_capabilities)
    
    @property
    def performance_tier(self) -> AgentPerformanceTier:
        """Get current performance tier"""
        return self.performance.calculate_performance_tier()
    
    @property
    def load_level(self) -> AgentLoadLevel:
        """Get current load level"""
        return self.load.load_level
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has specific capability"""
        return capability in self.all_capabilities
    
    def can_handle_task(
        self,
        required_capabilities: List[AgentCapability],
        estimated_complexity: float = 1.0,
        technologies: Optional[List[str]] = None
    ) -> bool:
        """
        Determine if agent can handle a task
        
        Args:
            required_capabilities: List of capabilities needed
            estimated_complexity: Task complexity (1.0 = average)
            technologies: Technologies involved in task
        
        Returns:
            bool: True if agent can handle task
        """
        # Check maintenance mode
        if self.maintenance_mode or not self.is_active:
            return False
        
        # Check capabilities
        if not all(self.has_capability(cap) for cap in required_capabilities):
            return False
        
        # Check load capacity
        if not self.load.can_accept_task(estimated_complexity):
            return False
        
        # Check technology preferences
        if technologies:
            # Avoid technologies the agent struggles with
            for tech in technologies:
                if tech in self.avoided_technologies:
                    return False
            
            # Prefer agents with experience in these technologies
            # (This is a soft requirement, not a hard rejection)
        
        # Check quality threshold
        if self.performance.overall_success_rate < self.min_quality_threshold:
            return False
        
        # Check performance tier
        if self.performance_tier == AgentPerformanceTier.DEGRADED:
            return False
        
        return True
    
    def calculate_task_suitability_score(
        self,
        required_capabilities: List[AgentCapability],
        estimated_complexity: float = 1.0,
        technologies: Optional[List[str]] = None,
        session_type: Optional[str] = None
    ) -> float:
        """
        Calculate suitability score for a task (0.0 to 1.0)
        
        Higher score indicates better fit
        """
        if not self.can_handle_task(required_capabilities, estimated_complexity, technologies):
            return 0.0
        
        # Base score from capability match
        capability_score = 0.0
        for capability in required_capabilities:
            if capability in self.primary_capabilities:
                capability_score += 1.0
            elif capability in self.secondary_capabilities:
                capability_score += 0.7
            else:
                capability_score += 0.3  # Should not happen due to can_handle_task check
        
        capability_score /= len(required_capabilities)
        
        # Performance score (weighted heavily)
        performance_score = self.performance.overall_success_rate
        
        # Load score (prefer less loaded agents)
        load_utilization = self.load.utilization_percentage
        load_score = 1.0 - min(load_utilization, 1.0)
        
        # Technology match score
        tech_score = 1.0
        if technologies:
            matches = sum(1 for tech in technologies if tech in self.preferred_technologies)
            tech_score = matches / len(technologies) if technologies else 1.0
        
        # Session type preference
        session_score = 1.0
        if session_type and self.preferred_session_types:
            session_score = 0.3 if session_type not in self.preferred_session_types else 1.0
        
        # Complexity alignment
        complexity_map = {
            "simple": 0.3,
            "medium": 0.6,
            "complex": 0.8,
            "expert": 1.0,
        }
        complexity_pref = complexity_map.get(self.complexity_preference, 0.6)
        
        # Adjust for complexity (experts handle complex tasks better)
        if estimated_complexity > 2.0 and self.complexity_preference in ["complex", "expert"]:
            complexity_alignment = 1.0
        elif estimated_complexity > 1.5 and self.complexity_preference in ["medium", "complex", "expert"]:
            complexity_alignment = 0.8
        else:
            complexity_alignment = 0.6
        
        # Weighted combination
        weights = {
            "capability": 0.25,
            "performance": 0.30,
            "load": 0.15,
            "technology": 0.15,
            "session": 0.05,
            "complexity": 0.10,
        }
        
        total_score = (
            weights["capability"] * capability_score +
            weights["performance"] * performance_score +
            weights["load"] * load_score +
            weights["technology"] * tech_score +
            weights["session"] * session_score +
            weights["complexity"] * complexity_alignment
        )
        
        # Apply performance tier multiplier
        tier_multipliers = {
            AgentPerformanceTier.ELITE: 1.1,
            AgentPerformanceTier.ADVANCED: 1.05,
            AgentPerformanceTier.COMPETENT: 1.0,
            AgentPerformanceTier.TRAINEE: 0.9,
            AgentPerformanceTier.DEGRADED: 0.0,
        }
        
        return total_score * tier_multipliers.get(self.performance_tier, 1.0)
    
    def accept_task(
        self,
        estimated_complexity: float = 1.0,
        required_capabilities: Optional[List[AgentCapability]] = None
    ) -> None:
        """
        Mark agent as accepting a new task
        
        Args:
            estimated_complexity: Estimated complexity of task
            required_capabilities: Capabilities required for task (for validation)
        
        Raises:
            AgentOverloadedError: If agent cannot accept more work
            AgentCapabilityMismatchError: If agent lacks required capabilities
        """
        # Validate capabilities
        if required_capabilities:
            missing = [cap for cap in required_capabilities if not self.has_capability(cap)]
            if missing:
                raise AgentCapabilityMismatchError(
                    f"Agent missing required capabilities: {missing}"
                )
        
        # Check load
        if not self.load.can_accept_task(estimated_complexity):
            raise AgentOverloadedError(
                f"Agent load level {self.load_level} cannot accept task "
                f"(current: {self.load.current_concurrent_tasks}, "
                f"capacity: {self.load.max_concurrent_capacity})"
            )
        
        # Accept task
        self.load.increment_load(estimated_complexity)
        self.last_active_at = datetime.now(timezone.utc)
    
    def complete_task(
        self,
        success: bool,
        partial_success: bool = False,
        quality_score: Optional[float] = None,
        execution_time_seconds: Optional[float] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None,
        capabilities_used: Optional[List[AgentCapability]] = None,
        technologies: Optional[List[str]] = None,
        estimated_complexity: float = 1.0
    ) -> None:
        """
        Mark task as completed and update metrics
        
        Args:
            success: Whether task was successful
            partial_success: Whether task was partially successful
            quality_score: Quality score (0.0 to 1.0)
            execution_time_seconds: Time taken
            tokens_used: Tokens consumed
            cost_usd: Cost incurred
            capabilities_used: Capabilities utilized
            technologies: Technologies involved
            estimated_complexity: Original complexity estimate
        """
        # Update performance metrics
        self.performance.record_task_result(
            success=success,
            partial_success=partial_success,
            quality_score=quality_score,
            execution_time_seconds=execution_time_seconds,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            capabilities_used=capabilities_used,
            technologies=technologies
        )
        
        # Update load
        self.load.decrement_load(estimated_complexity)
        
        # Update timestamp
        self.updated_at = datetime.now(timezone.utc)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            "agent_id": str(self.id),
            "agent_name": self.name,
            "agent_type": self.agent_type.value,
            "performance_tier": self.performance_tier.value,
            "load_level": self.load_level.value,
            "overall_success_rate": self.performance.overall_success_rate,
            "complete_success_rate": self.performance.complete_success_rate,
            "average_quality_score": self.performance.average_quality_score,
            "total_tasks": self.performance.total_tasks,
            "current_load": self.load.current_concurrent_tasks,
            "max_capacity": self.load.max_concurrent_capacity,
            "utilization_percentage": self.load.utilization_percentage,
            "capability_success_rates": {
                cap.value: rate
                for cap, rate in self.performance.capability_success_rates.items()
            },
            "is_active": self.is_active,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "updated_at": self.updated_at.isoformat(),
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get agent health status for monitoring"""
        issues = []
        
        # Check performance degradation
        if self.performance_tier == AgentPerformanceTier.DEGRADED:
            issues.append({
                "type": "performance_degradation",
                "severity": "critical",
                "message": f"Performance tier: {self.performance_tier.value}"
            })
        
        # Check overload
        if self.load_level == AgentLoadLevel.OVERLOADED:
            issues.append({
                "type": "overloaded",
                "severity": "critical",
                "message": f"Load level: {self.load_level.value}"
            })
        
        # Check inactivity
        if self.last_active_at:
            hours_inactive = (datetime.now(timezone.utc) - self.last_active_at).total_seconds() / 3600
            if hours_inactive > 24:
                issues.append({
                    "type": "inactive",
                    "severity": "warning",
                    "message": f"Inactive for {hours_inactive:.1f} hours"
                })
        
        # Check low success rate
        if self.performance.overall_success_rate < 0.5:
            issues.append({
                "type": "low_success_rate",
                "severity": "warning",
                "message": f"Success rate: {self.performance.overall_success_rate:.1%}"
            })
        
        return {
            "agent_id": str(self.id),
            "agent_name": self.name,
            "is_healthy": len(issues) == 0,
            "issues": issues,
            "performance_tier": self.performance_tier.value,
            "load_level": self.load_level.value,
            "success_rate": self.performance.overall_success_rate,
            "utilization": self.load.utilization_percentage,
            "last_active_hours": (
                (datetime.now(timezone.utc) - self.last_active_at).total_seconds() / 3600
                if self.last_active_at else None
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
