# **WEEK 2: MULTI-AGENT INTELLIGENCE LAYER - DAY 5-7**

## **EXECUTIVE PROGRESS UPDATE**

✅ **Week 1 Foundation Complete** - Core orchestrator with industrial resilience  
✅ **Phase 2.1 Validated** - Architecture, persistence, distributed locking approved  

**Proceeding with meticulous implementation of Multi-Agent Intelligence Layer.**

---

## **DAY 5: AGENT SPECIALIZATION SYSTEM & TASK DECOMPOSITION**

### **1.1 Deep Reasoning: Multi-Agent Architecture**

**Architectural Decision Record #003**: We're implementing a **Hybrid Orchestration Pattern** combining:
1. **Hierarchical Task Decomposition**: Planner agents break down complex tasks
2. **Specialized Agent Roles**: Domain-specific agents with unique capabilities
3. **Dynamic Load Balancing**: Agents allocated based on capability and availability
4. **Context-Aware Execution**: Shared knowledge across agent handoffs

**Anti-Generic Principle Applied**: Rejecting simple round-robin agent assignment. Instead, we're using **Capability-Based Routing** with **Performance-Aware Load Balancing** and **Context-Preserving Handoffs**.

#### **1.2 Enhanced Domain Models for Multi-Agent Orchestration**

```bash
# Create advanced agent specialization models
cat > orchestrator/src/industrial_orchestrator/domain/entities/agent.py << 'EOF'
"""
INDUSTRIAL AGENT ENTITY
Advanced agent models with specialization, performance tracking, and capability routing.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field, validator, root_validator

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
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    
    # Quality Assurance
    CODE_REVIEW = "code_review"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    
    # Problem Solving
    DEBUGGING = "debugging"
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
    COMPETENT = "competent"  # 70-85% success rate, reliable
    TRAINEE = "trainee"      # < 70% success rate, learning
    DEGRADED = "degraded"    # Performance issues detected


class AgentLoadLevel(str, Enum):
    """Current workload classification"""
    IDLE = "idle"            # 0-20% capacity utilized
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
    name: str = Field(..., min_length=1, max_length=100)
    agent_type: AgentType
    description: Optional[str] = Field(None, max_length=500)
    
    # Core capabilities
    primary_capabilities: List[AgentCapability] = Field(default_factory=list)
    secondary_capabilities: List[AgentCapability] = Field(default_factory=list)
    
    # Configuration
    model_config: str = Field(..., pattern=r"^[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+$")
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
    
    class Config:
        arbitrary_types_allowed = True
    
    @validator('name')
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
    
    @validator('primary_capabilities')
    def validate_capabilities(cls, v: List[AgentCapability], values: Dict[str, Any]) -> List[AgentCapability]:
        """Ensure capabilities align with agent type"""
        agent_type = values.get('agent_type')
        
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
    
    @root_validator
    def validate_agent_configuration(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive agent configuration validation"""
        agent_type = values.get('agent_type')
        system_prompt = values.get('system_prompt_template', '')
        
        # Ensure system prompt contains role information
        if not system_prompt or len(system_prompt.strip()) < 50:
            raise ValueError("System prompt must be at least 50 characters and define agent role")
        
        # Validate model configuration
        model_config = values.get('model_config', '')
        if '/' not in model_config:
            raise ValueError("Model configuration must be in format 'provider/model_name'")
        
        # Set default max_tokens based on agent type
        if values.get('max_tokens') is None:
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
            values['max_tokens'] = type_token_map.get(agent_type, 4000)
        
        return values
    
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
EOF

# Create task decomposition models
cat > orchestrator/src/industrial_orchestrator/domain/entities/task.py << 'EOF'
"""
INDUSTRIAL TASK ENTITY
Advanced task models with decomposition, dependencies, and complexity analysis.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field, validator, root_validator
import networkx as nx

from .agent import AgentCapability
from ..value_objects.session_status import SessionStatus
from ..exceptions.task_exceptions import (
    TaskDependencyCycleError,
    TaskComplexityOverflowError,
    TaskDecompositionError,
)


class TaskComplexityLevel(str, Enum):
    """Task complexity classification"""
    TRIVIAL = "trivial"      # < 15 minutes, simple implementation
    SIMPLE = "simple"        # 15-60 minutes, straightforward
    MODERATE = "moderate"    # 1-4 hours, some complexity
    COMPLEX = "complex"      # 4-8 hours, significant complexity
    EXPERT = "expert"        # 8+ hours, very complex, multiple components


class TaskPriority(str, Enum):
    """Task execution priority"""
    BLOCKER = "blocker"      # Blocks all other work
    CRITICAL = "critical"    # Must be completed soon
    HIGH = "high"            # Important, but not blocking
    NORMAL = "normal"        # Standard priority
    LOW = "low"              # Can be deferred
    BACKGROUND = "background" # Non-urgent background work


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"          # Created, not started
    READY = "ready"              # Dependencies satisfied, ready to start
    ASSIGNED = "assigned"        # Assigned to agent, not started
    IN_PROGRESS = "in_progress"  # Currently being worked on
    BLOCKED = "blocked"          # Blocked by external factor
    PAUSED = "paused"            # Manually paused
    COMPLETED = "completed"      # Successfully completed
    FAILED = "failed"            # Failed execution
    CANCELLED = "cancelled"      # Cancelled before completion
    SKIPPED = "skipped"          # Skipped (dependency failed)


class TaskDependencyType(str, Enum):
    """Types of task dependencies"""
    FINISH_TO_START = "finish_to_start"  # B can't start until A finishes
    START_TO_START = "start_to_start"    # B can't start until A starts
    FINISH_TO_FINISH = "finish_to_finish" # B can't finish until A finishes
    START_TO_FINISH = "start_to_finish"   # B can't finish until A starts


class TaskDependency(BaseModel):
    """Task dependency relationship"""
    
    source_task_id: UUID
    target_task_id: UUID
    dependency_type: TaskDependencyType = Field(default=TaskDependencyType.FINISH_TO_START)
    is_required: bool = Field(default=True)
    description: Optional[str] = Field(None, max_length=200)
    
    class Config:
        arbitrary_types_allowed = True


class TaskEstimate(BaseModel):
    """Task time and resource estimates"""
    
    # Time estimates (in hours)
    optimistic_hours: float = Field(default=0.0, ge=0.0)
    likely_hours: float = Field(default=0.0, ge=0.0)
    pessimistic_hours: float = Field(default=0.0, ge=0.0)
    
    # Resource estimates
    estimated_tokens: Optional[int] = Field(None, ge=0)
    estimated_cost_usd: Optional[float] = Field(None, ge=0.0)
    required_capabilities: List[AgentCapability] = Field(default_factory=list)
    
    # Confidence metrics
    estimate_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    last_estimated_at: Optional[datetime] = None
    estimation_source: str = Field(default="manual")  # manual, ai, historical
    
    @property
    def expected_hours(self) -> float:
        """Calculate expected hours using PERT formula"""
        if self.optimistic_hours == 0 and self.likely_hours == 0 and self.pessimistic_hours == 0:
            return 0.0
        
        return (self.optimistic_hours + 4 * self.likely_hours + self.pessimistic_hours) / 6
    
    @property
    def standard_deviation_hours(self) -> float:
        """Calculate standard deviation"""
        if self.pessimistic_hours <= self.optimistic_hours:
            return 0.0
        return (self.pessimistic_hours - self.optimistic_hours) / 6
    
    @property
    def complexity_level(self) -> TaskComplexityLevel:
        """Determine complexity level based on expected hours"""
        hours = self.expected_hours
        
        if hours < 0.25:  # < 15 minutes
            return TaskComplexityLevel.TRIVIAL
        elif hours < 1.0:  # < 1 hour
            return TaskComplexityLevel.SIMPLE
        elif hours < 4.0:  # < 4 hours
            return TaskComplexityLevel.MODERATE
        elif hours < 8.0:  # < 8 hours
            return TaskComplexityLevel.COMPLEX
        else:  # 8+ hours
            return TaskComplexityLevel.EXPERT
    
    def update_from_execution(
        self,
        actual_hours: float,
        actual_tokens: Optional[int] = None,
        actual_cost_usd: Optional[float] = None
    ) -> None:
        """Update estimates based on actual execution"""
        # Simple learning algorithm - could be more sophisticated
        self.likely_hours = (self.likely_hours + actual_hours) / 2
        
        # Adjust optimistic/pessimistic based on variance
        variance = abs(actual_hours - self.expected_hours)
        if actual_hours < self.optimistic_hours:
            self.optimistic_hours = actual_hours
        elif actual_hours > self.pessimistic_hours:
            self.pessimistic_hours = actual_hours
        
        # Update confidence (increases with more data)
        self.estimate_confidence = min(0.95, self.estimate_confidence + 0.05)
        
        # Update resource estimates
        if actual_tokens is not None:
            self.estimated_tokens = actual_tokens
        
        if actual_cost_usd is not None:
            self.estimated_cost_usd = actual_cost_usd
        
        self.last_estimated_at = datetime.now(timezone.utc)
        self.estimation_source = "historical"


class TaskEntity(BaseModel):
    """
    Industrial Task Entity
    
    Represents a unit of work within a session with:
    1. Decomposition hierarchy
    2. Dependency management
    3. Complexity analysis
    4. Progress tracking
    """
    
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    parent_task_id: Optional[UUID] = None
    
    # Task identity
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    task_type: str = Field(default="implementation")
    
    # Execution state
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    status_updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assigned_agent_id: Optional[UUID] = None
    assigned_at: Optional[datetime] = None
    
    # Planning
    priority: TaskPriority = Field(default=TaskPriority.NORMAL)
    estimate: TaskEstimate = Field(default_factory=TaskEstimate)
    
    # Dependencies
    dependencies: List[TaskDependency] = Field(default_factory=list)
    dependents: List[UUID] = Field(default_factory=list)  # Reverse references
    
    # Execution tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Child tasks (for decomposition)
    child_tasks: List["TaskEntity"] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True
    
    @validator('title')
    def validate_task_title(cls, v: str) -> str:
        """Ensure task titles are descriptive and actionable"""
        if not v.strip():
            raise ValueError("Task title cannot be empty")
        
        # Should be actionable (start with verb)
        action_verbs = [
            'implement', 'create', 'add', 'update', 'fix', 'refactor',
            'optimize', 'test', 'review', 'deploy', 'configure', 'document'
        ]
        
        first_word = v.split()[0].lower() if v.split() else ""
        if first_word not in action_verbs:
            raise ValueError(
                f"Task title should start with an action verb. "
                f"Examples: {', '.join(action_verbs[:5])}..."
            )
        
        return v.strip()
    
    @property
    def is_leaf_task(self) -> bool:
        """Check if task is a leaf (no children)"""
        return len(self.child_tasks) == 0
    
    @property
    def is_root_task(self) -> bool:
        """Check if task is a root (no parent)"""
        return self.parent_task_id is None
    
    @property
    def elapsed_hours(self) -> Optional[float]:
        """Calculate elapsed hours if in progress"""
        if self.started_at and not self.completed_at and not self.failed_at:
            return (datetime.now(timezone.utc) - self.started_at).total_seconds() / 3600
        return None
    
    @property
    def duration_hours(self) -> Optional[float]:
        """Calculate total duration if completed"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() / 3600
        elif self.started_at and self.failed_at:
            return (self.failed_at - self.started_at).total_seconds() / 3600
        return None
    
    @property
    def can_start(self) -> bool:
        """Check if task can start (dependencies satisfied)"""
        if self.status != TaskStatus.PENDING and self.status != TaskStatus.READY:
            return False
        
        # Check required dependencies
        for dep in self.dependencies:
            if dep.is_required:
                # For now, assume dependency satisfaction check
                # In practice, would check actual dependency status
                return False
        
        return True
    
    @property
    def is_blocked(self) -> bool:
        """Check if task is blocked by dependencies"""
        return self.status == TaskStatus.BLOCKED or (self.status == TaskStatus.PENDING and not self.can_start)
    
    def add_dependency(
        self,
        task_id: UUID,
        dependency_type: TaskDependencyType = TaskDependencyType.FINISH_TO_START,
        is_required: bool = True,
        description: Optional[str] = None
    ) -> None:
        """Add dependency to another task"""
        # Check for self-dependency
        if task_id == self.id:
            raise ValueError("Task cannot depend on itself")
        
        # Check for duplicate
        existing = any(dep.target_task_id == task_id for dep in self.dependencies)
        if existing:
            raise ValueError(f"Dependency on task {task_id} already exists")
        
        dependency = TaskDependency(
            source_task_id=self.id,
            target_task_id=task_id,
            dependency_type=dependency_type,
            is_required=is_required,
            description=description
        )
        
        self.dependencies.append(dependency)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_child_task(self, child_task: "TaskEntity") -> None:
        """Add child task (decomposition)"""
        # Set parent reference
        child_task.parent_task_id = self.id
        
        # Add to children
        self.child_tasks.append(child_task)
        self.updated_at = datetime.now(timezone.utc)
    
    def decompose(
        self,
        decomposition_strategy: str = "functional",
        max_depth: int = 3,
        target_complexity: TaskComplexityLevel = TaskComplexityLevel.MODERATE
    ) -> List["TaskEntity"]:
        """
        Decompose task into subtasks based on strategy
        
        Args:
            decomposition_strategy: Strategy for decomposition
                - "functional": By functional components
                - "temporal": By time/phase
                - "capability": By required capabilities
            max_depth: Maximum decomposition depth
            target_complexity: Target complexity for leaf tasks
        
        Returns:
            List of generated subtasks
        """
        if max_depth <= 0:
            return []
        
        current_complexity = self.estimate.complexity_level
        complexity_value = {
            TaskComplexityLevel.TRIVIAL: 1,
            TaskComplexityLevel.SIMPLE: 2,
            TaskComplexityLevel.MODERATE: 3,
            TaskComplexityLevel.COMPLEX: 4,
            TaskComplexityLevel.EXPERT: 5,
        }
        
        target_value = complexity_value.get(target_complexity, 3)
        current_value = complexity_value.get(current_complexity, 3)
        
        # Don't decompose if already at or below target complexity
        if current_value <= target_value:
            return []
        
        # Determine decomposition factor
        decomposition_factor = current_value - target_value + 1
        
        # Generate subtasks based on strategy
        subtasks = []
        
        if decomposition_strategy == "functional":
            # Decompose by functional components
            components = [
                f"{self.title} - Component {i+1}"
                for i in range(decomposition_factor)
            ]
            
            for i, component in enumerate(components):
                subtask = TaskEntity(
                    session_id=self.session_id,
                    parent_task_id=self.id,
                    title=component,
                    description=f"Functional component {i+1} of {self.title}",
                    task_type=self.task_type,
                    priority=self.priority,
                    estimate=TaskEstimate(
                        likely_hours=self.estimate.likely_hours / decomposition_factor,
                        estimate_confidence=self.estimate.estimate_confidence * 0.8,
                        required_capabilities=self.estimate.required_capabilities.copy(),
                        estimation_source="decomposition"
                    )
                )
                
                # Further decompose if needed
                if max_depth > 1:
                    child_subtasks = subtask.decompose(
                        decomposition_strategy,
                        max_depth - 1,
                        target_complexity
                    )
                    for child in child_subtasks:
                        subtask.add_child_task(child)
                
                subtasks.append(subtask)
        
        elif decomposition_strategy == "temporal":
            # Decompose by phases/stages
            phases = ["Analysis", "Design", "Implementation", "Testing", "Review"]
            phases = phases[:decomposition_factor]
            
            for i, phase in enumerate(phases):
                subtask = TaskEntity(
                    session_id=self.session_id,
                    parent_task_id=self.id,
                    title=f"{self.title} - {phase}",
                    description=f"{phase} phase of {self.title}",
                    task_type=f"{self.task_type}_{phase.lower()}",
                    priority=self.priority,
                    estimate=TaskEstimate(
                        likely_hours=self.estimate.likely_hours / len(phases),
                        estimate_confidence=self.estimate.estimate_confidence * 0.7,
                        required_capabilities=self.estimate.required_capabilities.copy(),
                        estimation_source="decomposition"
                    )
                )
                
                # Add dependencies between phases
                if i > 0:
                    subtask.add_dependency(
                        subtasks[-1].id,
                        dependency_type=TaskDependencyType.FINISH_TO_START,
                        description=f"Depends on {phases[i-1]} phase"
                    )
                
                subtasks.append(subtask)
        
        elif decomposition_strategy == "capability":
            # Decompose by required capabilities
            capabilities = self.estimate.required_capabilities
            if not capabilities:
                capabilities = [AgentCapability.CODE_GENERATION]
            
            for i, capability in enumerate(capabilities[:decomposition_factor]):
                subtask = TaskEntity(
                    session_id=self.session_id,
                    parent_task_id=self.id,
                    title=f"{self.title} - {capability.value.replace('_', ' ').title()}",
                    description=f"{capability.value.replace('_', ' ')} aspect of {self.title}",
                    task_type=f"{self.task_type}_{capability.value}",
                    priority=self.priority,
                    estimate=TaskEstimate(
                        likely_hours=self.estimate.likely_hours / len(capabilities),
                        estimate_confidence=self.estimate.estimate_confidence * 0.6,
                        required_capabilities=[capability],
                        estimation_source="decomposition"
                    )
                )
                
                subtasks.append(subtask)
        
        # Add subtasks as children
        for subtask in subtasks:
            self.add_child_task(subtask)
        
        return subtasks
    
    def get_dependency_graph(self) -> nx.DiGraph:
        """Get NetworkX graph of task dependencies"""
        graph = nx.DiGraph()
        
        # Add this task
        graph.add_node(self.id, task=self)
        
        # Add dependencies
        for dep in self.dependencies:
            graph.add_edge(dep.target_task_id, dep.source_task_id, dependency=dep)
        
        # Add child task dependencies recursively
        for child in self.child_tasks:
            child_graph = child.get_dependency_graph()
            graph = nx.compose(graph, child_graph)
            
            # Add parent-child relationship
            graph.add_edge(self.id, child.id, relationship="parent_child")
        
        return graph
    
    def validate_dependencies(self) -> bool:
        """Validate that dependency graph has no cycles"""
        try:
            graph = self.get_dependency_graph()
            cycles = list(nx.simple_cycles(graph))
            
            if cycles:
                raise TaskDependencyCycleError(
                    f"Task dependency cycle detected: {cycles}"
                )
            
            return True
            
        except nx.NetworkXNoCycle:
            return True
    
    def get_execution_order(self) -> List[UUID]:
        """Get topological order for task execution"""
        graph = self.get_dependency_graph()
        
        try:
            return list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            raise TaskDependencyCycleError("Cannot determine execution order due to cycles")
    
    def calculate_critical_path(self) -> List[UUID]:
        """Calculate critical path for task execution"""
        graph = self.get_dependency_graph()
        
        # Add duration estimates to graph
        for node_id in graph.nodes():
            task = graph.nodes[node_id].get('task')
            if task and task.estimate:
                graph.nodes[node_id]['duration'] = task.estimate.expected_hours
            else:
                graph.nodes[node_id]['duration'] = 0
        
        # Calculate critical path (simplified)
        try:
            # For DAGs, longest path = critical path
            longest_paths = nx.dag_longest_path(graph, weight='duration')
            return longest_paths
        except nx.NetworkXUnfeasible:
            raise TaskDependencyCycleError("Cannot calculate critical path due to cycles")
    
    def update_status(self, new_status: TaskStatus) -> None:
        """Update task status with validation"""
        valid_transitions = {
            TaskStatus.PENDING: {TaskStatus.READY, TaskStatus.ASSIGNED, TaskStatus.CANCELLED},
            TaskStatus.READY: {TaskStatus.ASSIGNED, TaskStatus.CANCELLED},
            TaskStatus.ASSIGNED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.PAUSED},
            TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.PAUSED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.COMPLETED: set(),
            TaskStatus.FAILED: set(),
            TaskStatus.CANCELLED: set(),
            TaskStatus.SKIPPED: set(),
        }
        
        if new_status not in valid_transitions.get(self.status, set()):
            raise ValueError(
                f"Invalid status transition from {self.status} to {new_status}"
            )
        
        old_status = self.status
        self.status = new_status
        self.status_updated_at = datetime.now(timezone.utc)
        
        # Update timestamps based on status
        if new_status == TaskStatus.IN_PROGRESS and not self.started_at:
            self.started_at = datetime.now(timezone.utc)
        elif new_status == TaskStatus.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now(timezone.utc)
        elif new_status == TaskStatus.FAILED and not self.failed_at:
            self.failed_at = datetime.now(timezone.utc)
        
        self.updated_at = datetime.now(timezone.utc)
        
        return old_status
    
    def assign_to_agent(self, agent_id: UUID) -> None:
        """Assign task to agent"""
        if self.status not in [TaskStatus.PENDING, TaskStatus.READY]:
            raise ValueError(f"Cannot assign task in status {self.status}")
        
        self.assigned_agent_id = agent_id
        self.assigned_at = datetime.now(timezone.utc)
        self.update_status(TaskStatus.ASSIGNED)
    
    def complete_with_result(
        self,
        result: Dict[str, Any],
        quality_score: Optional[float] = None,
        actual_hours: Optional[float] = None,
        actual_tokens: Optional[int] = None,
        actual_cost_usd: Optional[float] = None
    ) -> None:
        """Mark task as completed with results"""
        self.result = result
        
        # Update estimates with actuals
        if actual_hours is not None:
            self.estimate.update_from_execution(
                actual_hours=actual_hours,
                actual_tokens=actual_tokens,
                actual_cost_usd=actual_cost_usd
            )
        
        self.update_status(TaskStatus.COMPLETED)
    
    def fail_with_error(
        self,
        error: Exception,
        error_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark task as failed with error"""
        self.error = {
            "type": error.__class__.__name__,
            "message": str(error),
            "context": error_context or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        self.update_status(TaskStatus.FAILED)
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get task progress summary"""
        total_tasks = self.count_subtasks()
        completed_tasks = self.count_subtasks(status_filter=TaskStatus.COMPLETED)
        in_progress_tasks = self.count_subtasks(status_filter=TaskStatus.IN_PROGRESS)
        failed_tasks = self.count_subtasks(status_filter=TaskStatus.FAILED)
        
        return {
            "task_id": str(self.id),
            "title": self.title,
            "status": self.status.value,
            "progress_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "failed_tasks": failed_tasks,
            "blocked_tasks": self.count_subtasks(status_filter=TaskStatus.BLOCKED),
            "elapsed_hours": self.elapsed_hours,
            "duration_hours": self.duration_hours,
            "estimated_remaining_hours": self.estimate.expected_hours - (self.elapsed_hours or 0),
            "assigned_agent": str(self.assigned_agent_id) if self.assigned_agent_id else None,
            "complexity": self.estimate.complexity_level.value,
            "priority": self.priority.value,
        }
    
    def count_subtasks(self, status_filter: Optional[TaskStatus] = None) -> int:
        """Count subtasks (recursive) optionally filtered by status"""
        count = 0
        
        # Count children
        for child in self.child_tasks:
            if status_filter is None or child.status == status_filter:
                count += 1
            
            # Recurse
            count += child.count_subtasks(status_filter)
        
        return count
    
    def find_subtask(self, task_id: UUID) -> Optional["TaskEntity"]:
        """Find subtask by ID (recursive)"""
        if self.id == task_id:
            return self
        
        for child in self.child_tasks:
            found = child.find_subtask(task_id)
            if found:
                return found
        
        return None
    
    def flatten_hierarchy(self) -> List["TaskEntity"]:
        """Flatten task hierarchy into list"""
        tasks = [self]
        
        for child in self.child_tasks:
            tasks.extend(child.flatten_hierarchy())
        
        return tasks


class TaskDecompositionTemplate(BaseModel):
    """Template for task decomposition strategies"""
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    # Decomposition rules
    complexity_threshold: TaskComplexityLevel = Field(default=TaskComplexityLevel.COMPLEX)
    decomposition_strategy: str = Field(default="functional")
    max_depth: int = Field(default=3, ge=1, le=5)
    target_leaf_complexity: TaskComplexityLevel = Field(default=TaskComplexityLevel.MODERATE)
    
    # Task type applicability
    applicable_task_types: List[str] = Field(default_factory=lambda: ["implementation"])
    excluded_task_types: List[str] = Field(default_factory=list)
    
    # Generation rules
    subtask_templates: List[Dict[str, Any]] = Field(default_factory=list)
    dependency_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def apply_to_task(self, task: TaskEntity) -> List[TaskEntity]:
        """Apply decomposition template to task"""
        # Check applicability
        if task.task_type in self.excluded_task_types:
            return []
        
        if self.applicable_task_types and task.task_type not in self.applicable_task_types:
            return []
        
        # Check complexity threshold
        task_complexity_value = {
            TaskComplexityLevel.TRIVIAL: 1,
            TaskComplexityLevel.SIMPLE: 2,
            TaskComplexityLevel.MODERATE: 3,
            TaskComplexityLevel.COMPLEX: 4,
            TaskComplexityLevel.EXPERT: 5,
        }
        
        threshold_value = task_complexity_value.get(self.complexity_threshold, 3)
        actual_value = task_complexity_value.get(task.estimate.complexity_level, 3)
        
        if actual_value < threshold_value:
            return []  # Task not complex enough for decomposition
        
        # Apply decomposition
        return task.decompose(
            decomposition_strategy=self.decomposition_strategy,
            max_depth=self.max_depth,
            target_complexity=self.target_leaf_complexity
        )
EOF

#### **1.3 Advanced Task Decomposition Algorithms**

```bash
# Create intelligent task decomposition service
cat > orchestrator/src/industrial_orchestrator/application/services/task_decomposition_service.py << 'EOF'
"""
INDUSTRIAL TASK DECOMPOSITION SERVICE
Advanced algorithms for breaking down complex tasks into manageable subtasks.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID, uuid4
from datetime import datetime, timezone

import networkx as nx
from pydantic import BaseModel, Field

from ...domain.entities.task import (
    TaskEntity, TaskDecompositionTemplate, TaskComplexityLevel,
    TaskPriority, TaskDependencyType, TaskEstimate, AgentCapability
)
from ...domain.entities.agent import AgentType
from ...domain.exceptions.task_exceptions import (
    TaskDecompositionError,
    TaskComplexityOverflowError,
    TaskDependencyCycleError,
)


class DecompositionRule(BaseModel):
    """Rule for task decomposition"""
    
    pattern: str  # Regex pattern to match task title/description
    strategy: str  # Decomposition strategy
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=10)
    
    class Config:
        arbitrary_types_allowed = True


class ComplexityAnalyzer(BaseModel):
    """Analyze task complexity using multiple heuristics"""
    
    @staticmethod
    def analyze_requirements_text(text: str) -> Dict[str, Any]:
        """Analyze requirements text for complexity indicators"""
        if not text:
            return {"word_count": 0, "estimated_hours": 1.0}
        
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        
        # Complexity heuristics
        complexity_indicators = {
            "must": 1,
            "should": 2,
            "could": 3,
            "would": 4,
            "implement": 2,
            "create": 2,
            "build": 3,
            "develop": 3,
            "design": 4,
            "architect": 5,
            "integrate": 4,
            "deploy": 3,
            "test": 2,
            "document": 1,
        }
        
        # Count technical terms
        technical_terms = re.findall(
            r'\b(API|database|authentication|encryption|scalability|performance|'
            r'security|deployment|integration|microservice|container|kubernetes|'
            r'docker|aws|azure|gcp|cloud|serverless)\b',
            text,
            re.IGNORECASE
        )
        
        # Estimate hours based on heuristics
        base_hours = word_count / 100  # 100 words ≈ 1 hour
        
        # Adjust for complexity indicators
        complexity_score = 1.0
        for indicator, weight in complexity_indicators.items():
            if indicator in text.lower():
                complexity_score += weight * 0.1
        
        # Adjust for technical terms
        complexity_score += len(technical_terms) * 0.2
        
        estimated_hours = base_hours * complexity_score
        
        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "technical_terms": len(technical_terms),
            "complexity_score": complexity_score,
            "estimated_hours": max(1.0, min(estimated_hours, 24.0)),
        }
    
    @staticmethod
    def estimate_from_task_description(task: TaskEntity) -> TaskEstimate:
        """Estimate task complexity from description"""
        if not task.description:
            return TaskEstimate(
                likely_hours=2.0,
                estimate_confidence=0.3,
                required_capabilities=[AgentCapability.CODE_GENERATION],
                estimation_source="default"
            )
        
        analysis = ComplexityAnalyzer.analyze_requirements_text(task.description)
        
        # Map to complexity levels
        hours = analysis["estimated_hours"]
        if hours < 0.25:
            likely_hours = 0.25
            optimistic = 0.1
            pessimistic = 0.5
        elif hours < 1.0:
            likely_hours = hours
            optimistic = hours * 0.5
            pessimistic = hours * 2.0
        elif hours < 4.0:
            likely_hours = hours
            optimistic = hours * 0.7
            pessimistic = hours * 1.5
        elif hours < 8.0:
            likely_hours = hours
            optimistic = hours * 0.8
            pessimistic = hours * 1.3
        else:
            likely_hours = 8.0
            optimistic = 6.0
            pessimistic = 12.0
        
        # Infer capabilities from description
        capabilities = ComplexityAnalyzer.infer_capabilities(task.description)
        
        # Calculate confidence based on analysis quality
        confidence = min(0.8, 0.3 + (analysis["word_count"] / 500))
        
        return TaskEstimate(
            optimistic_hours=optimistic,
            likely_hours=likely_hours,
            pessimistic_hours=pessimistic,
            estimated_tokens=analysis["word_count"] * 2,  # Rough estimate
            required_capabilities=capabilities,
            estimate_confidence=confidence,
            estimation_source="ai_analysis"
        )
    
    @staticmethod
    def infer_capabilities(text: str) -> List[AgentCapability]:
        """Infer required capabilities from text"""
        if not text:
            return [AgentCapability.CODE_GENERATION]
        
        text_lower = text.lower()
        capabilities = set()
        
        # Map keywords to capabilities
        keyword_map = {
            # Planning & Architecture
            "design": AgentCapability.SYSTEM_DESIGN,
            "architecture": AgentCapability.ARCHITECTURE_PLANNING,
            "plan": AgentCapability.ARCHITECTURE_PLANNING,
            "requirement": AgentCapability.REQUIREMENTS_ANALYSIS,
            "analyze": AgentCapability.REQUIREMENTS_ANALYSIS,
            "break down": AgentCapability.TASK_DECOMPOSITION,
            "decompose": AgentCapability.TASK_DECOMPOSITION,
            
            # Implementation
            "implement": AgentCapability.CODE_GENERATION,
            "create": AgentCapability.CODE_GENERATION,
            "build": AgentCapability.CODE_GENERATION,
            "develop": AgentCapability.CODE_GENERATION,
            "write": AgentCapability.CODE_GENERATION,
            "code": AgentCapability.CODE_GENERATION,
            "test": AgentCapability.TEST_GENERATION,
            "document": AgentCapability.DOCUMENTATION,
            "refactor": AgentCapability.REFACTORING,
            
            # Quality Assurance
            "review": AgentCapability.CODE_REVIEW,
            "audit": AgentCapability.SECURITY_AUDIT,
            "security": AgentCapability.SECURITY_AUDIT,
            "performance": AgentCapability.PERFORMANCE_ANALYSIS,
            "compliance": AgentCapability.COMPLIANCE_CHECK,
            
            # Problem Solving
            "debug": AgentCapability.DEBUGGING,
            "fix": AgentCapability.DEBUGGING,
            "troubleshoot": AgentCapability.TROUBLESHOOTING,
            "diagnose": AgentCapability.ROOT_CAUSE_ANALYSIS,
            "optimize": AgentCapability.OPTIMIZATION,
            "improve": AgentCapability.OPTIMIZATION,
            
            # Integration & Operations
            "deploy": AgentCapability.DEPLOYMENT,
            "configure": AgentCapability.CONFIGURATION,
            "monitor": AgentCapability.MONITORING,
            "scale": AgentCapability.SCALING,
            "integrate": AgentCapability.DEPLOYMENT,
        }
        
        for keyword, capability in keyword_map.items():
            if keyword in text_lower:
                capabilities.add(capability)
        
        # If no capabilities detected, default to code generation
        if not capabilities:
            capabilities.add(AgentCapability.CODE_GENERATION)
        
        return list(capabilities)


class TaskDecompositionService:
    """
    Industrial Task Decomposition Service
    
    Advanced algorithms for:
    1. Intelligent task breakdown
    2. Dependency graph generation
    3. Complexity analysis
    4. Parallel execution optimization
    """
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        
        # Predefined decomposition templates
        self._templates = self._load_default_templates()
        
        # Decomposition rules
        self._rules = self._load_default_rules()
        
        # Complexity analyzer
        self._analyzer = ComplexityAnalyzer()
    
    def _load_default_templates(self) -> Dict[str, TaskDecompositionTemplate]:
        """Load default decomposition templates"""
        return {
            "web_service_implementation": TaskDecompositionTemplate(
                name="Web Service Implementation",
                description="Template for implementing web services with full stack",
                complexity_threshold=TaskComplexityLevel.COMPLEX,
                decomposition_strategy="temporal",
                max_depth=4,
                target_leaf_complexity=TaskComplexityLevel.MODERATE,
                applicable_task_types=["web_service", "api", "backend"],
                subtask_templates=[
                    {
                        "phase": "requirements",
                        "title_template": "{parent_title} - Requirements Analysis",
                        "description": "Analyze and document requirements",
                        "capabilities": [AgentCapability.REQUIREMENTS_ANALYSIS],
                        "estimated_hours": 2.0,
                    },
                    {
                        "phase": "design",
                        "title_template": "{parent_title} - System Design",
                        "description": "Design system architecture and API",
                        "capabilities": [AgentCapability.SYSTEM_DESIGN],
                        "estimated_hours": 4.0,
                    },
                    {
                        "phase": "implementation",
                        "title_template": "{parent_title} - Implementation",
                        "description": "Implement core functionality",
                        "capabilities": [AgentCapability.CODE_GENERATION],
                        "estimated_hours": 8.0,
                    },
                    {
                        "phase": "testing",
                        "title_template": "{parent_title} - Testing",
                        "description": "Write and execute tests",
                        "capabilities": [AgentCapability.TEST_GENERATION],
                        "estimated_hours": 4.0,
                    },
                    {
                        "phase": "deployment",
                        "title_template": "{parent_title} - Deployment",
                        "description": "Deploy and configure service",
                        "capabilities": [AgentCapability.DEPLOYMENT],
                        "estimated_hours": 2.0,
                    },
                ],
            ),
            "refactoring_task": TaskDecompositionTemplate(
                name="Code Refactoring",
                description="Template for code refactoring tasks",
                complexity_threshold=TaskComplexityLevel.MODERATE,
                decomposition_strategy="functional",
                max_depth=3,
                target_leaf_complexity=TaskComplexityLevel.SIMPLE,
                applicable_task_types=["refactoring", "optimization"],
                subtask_templates=[
                    {
                        "component": "analysis",
                        "title_template": "{parent_title} - Code Analysis",
                        "description": "Analyze current code structure",
                        "capabilities": [AgentCapability.CODE_REVIEW],
                        "estimated_hours": 1.0,
                    },
                    {
                        "component": "planning",
                        "title_template": "{parent_title} - Refactoring Plan",
                        "description": "Plan refactoring approach",
                        "capabilities": [AgentCapability.SYSTEM_DESIGN],
                        "estimated_hours": 2.0,
                    },
                    {
                        "component": "execution",
                        "title_template": "{parent_title} - Refactoring Execution",
                        "description": "Execute refactoring changes",
                        "capabilities": [AgentCapability.REFACTORING],
                        "estimated_hours": 4.0,
                    },
                    {
                        "component": "verification",
                        "title_template": "{parent_title} - Verification",
                        "description": "Verify refactoring didn't break functionality",
                        "capabilities": [AgentCapability.TEST_GENERATION],
                        "estimated_hours": 2.0,
                    },
                ],
            ),
        }
    
    def _load_default_rules(self) -> List[DecompositionRule]:
        """Load default decomposition rules"""
        return [
            DecompositionRule(
                pattern=r".*(microservice|distributed).*",
                strategy="microservice_pattern",
                parameters={
                    "decomposition_strategy": "functional",
                    "service_count": 3,
                    "shared_components": ["auth", "database", "api_gateway"],
                },
                priority=5,
            ),
            DecompositionRule(
                pattern=r".*(CRUD|database|model).*",
                strategy="crud_pattern",
                parameters={
                    "decomposition_strategy": "capability",
                    "entities": ["create", "read", "update", "delete"],
                    "include_tests": True,
                },
                priority=4,
            ),
            DecompositionRule(
                pattern=r".*(UI|frontend|interface).*",
                strategy="ui_components",
                parameters={
                    "decomposition_strategy": "functional",
                    "components": ["layout", "navigation", "forms", "tables", "charts"],
                },
                priority=4,
            ),
            DecompositionRule(
                pattern=r".*(auth|authentication|security).*",
                strategy="security_pattern",
                parameters={
                    "decomposition_strategy": "temporal",
                    "phases": ["design", "implementation", "testing", "audit"],
                    "security_level": "high",
                },
                priority=6,  # High priority for security
            ),
        ]
    
    def analyze_and_decompose(
        self,
        task: TaskEntity,
        auto_estimate: bool = True,
        apply_templates: bool = True,
        apply_rules: bool = True,
        max_depth: int = 3
    ) -> TaskEntity:
        """
        Comprehensive task analysis and decomposition
        
        Args:
            task: Task to decompose
            auto_estimate: Automatically estimate complexity
            apply_templates: Apply matching templates
            apply_rules: Apply decomposition rules
            max_depth: Maximum decomposition depth
        
        Returns:
            Decomposed task with subtasks
        """
        self._logger.info(f"Analyzing task: {task.title} (ID: {task.id})")
        
        # Step 1: Auto-estimate if needed
        if auto_estimate and (not task.estimate or task.estimate.estimate_confidence < 0.5):
            new_estimate = self._analyzer.estimate_from_task_description(task)
            task.estimate = new_estimate
            self._logger.debug(f"Auto-estimated task: {task.estimate.expected_hours:.1f} hours")
        
        # Step 2: Apply matching templates
        if apply_templates:
            applied_templates = self._apply_matching_templates(task)
            if applied_templates:
                self._logger.info(f"Applied {len(applied_templates)} templates to task")
        
        # Step 3: Apply decomposition rules
        if apply_rules:
            applied_rules = self._apply_decomposition_rules(task)
            if applied_rules:
                self._logger.info(f"Applied {len(applied_rules)} rules to task")
        
        # Step 4: Recursively decompose child tasks
        if max_depth > 0:
            for child in task.child_tasks.copy():  # Copy to avoid modification issues
                if child.estimate.complexity_level.value >= TaskComplexityLevel.MODERATE.value:
                    self.analyze_and_decompose(
                        child,
                        auto_estimate=auto_estimate,
                        apply_templates=apply_templates,
                        apply_rules=apply_rules,
                        max_depth=max_depth - 1
                    )
        
        # Step 5: Validate decomposition
        self._validate_decomposition(task)
        
        self._logger.info(
            f"Decomposition complete: {task.count_subtasks()} total subtasks, "
            f"max depth: {self._calculate_max_depth(task)}"
        )
        
        return task
    
    def _apply_matching_templates(self, task: TaskEntity) -> List[str]:
        """Apply matching decomposition templates to task"""
        applied = []
        
        for template_name, template in self._templates.items():
            try:
                subtasks = template.apply_to_task(task)
                if subtasks:
                    applied.append(template_name)
                    self._logger.debug(f"Applied template '{template_name}' to task {task.id}")
            except Exception as e:
                self._logger.warning(f"Failed to apply template '{template_name}': {e}")
        
        return applied
    
    def _apply_decomposition_rules(self, task: TaskEntity) -> List[str]:
        """Apply decomposition rules to task"""
        applied = []
        
        # Combine title and description for pattern matching
        text_to_match = f"{task.title} {task.description or ''}"
        
        for rule in sorted(self._rules, key=lambda r: r.priority, reverse=True):
            if re.search(rule.pattern, text_to_match, re.IGNORECASE):
                try:
                    self._apply_rule(rule, task)
                    applied.append(rule.pattern)
                    self._logger.debug(f"Applied rule '{rule.pattern}' to task {task.id}")
                except Exception as e:
                    self._logger.warning(f"Failed to apply rule '{rule.pattern}': {e}")
        
        return applied
    
    def _apply_rule(self, rule: DecompositionRule, task: TaskEntity) -> None:
        """Apply a specific decomposition rule to task"""
        strategy = rule.strategy
        params = rule.parameters
        
        if strategy == "microservice_pattern":
            self._decompose_microservice(task, params)
        elif strategy == "crud_pattern":
            self._decompose_crud(task, params)
        elif strategy == "ui_components":
            self._decompose_ui_components(task, params)
        elif strategy == "security_pattern":
            self._decompose_security(task, params)
        else:
            # Default decomposition
            task.decompose(
                decomposition_strategy=params.get("decomposition_strategy", "functional"),
                max_depth=params.get("max_depth", 3),
                target_complexity=TaskComplexityLevel.MODERATE
            )
    
    def _decompose_microservice(self, task: TaskEntity, params: Dict[str, Any]) -> None:
        """Decompose microservice task into services and shared components"""
        service_count = params.get("service_count", 3)
        shared_components = params.get("shared_components", [])
        
        # Create service tasks
        for i in range(service_count):
            service_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - Service {i+1}",
                description=f"Microservice {i+1} implementation",
                task_type="microservice",
                priority=task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours / (service_count + len(shared_components)),
                    required_capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.DEPLOYMENT],
                    estimation_source="microservice_decomposition"
                )
            )
            task.add_child_task(service_task)
        
        # Create shared component tasks
        for component in shared_components:
            component_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - {component.title()} Component",
                description=f"Shared {component} component for microservices",
                task_type="shared_component",
                priority=task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours * 0.5 / len(shared_components),
                    required_capabilities=[AgentCapability.CODE_GENERATION, AgentCapability.SYSTEM_DESIGN],
                    estimation_source="microservice_decomposition"
                )
            )
            
            # Add dependencies: services depend on shared components
            for i, service_task in enumerate(task.child_tasks[:service_count]):
                service_task.add_dependency(
                    component_task.id,
                    dependency_type=TaskDependencyType.START_TO_START,
                    description=f"Requires {component} component"
                )
            
            task.add_child_task(component_task)
    
    def _decompose_crud(self, task: TaskEntity, params: Dict[str, Any]) -> None:
        """Decompose CRUD task into entity operations"""
        entities = params.get("entities", ["create", "read", "update", "delete"])
        include_tests = params.get("include_tests", True)
        
        # Create entity operation tasks
        for entity_op in entities:
            op_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - {entity_op.title()}",
                description=f"{entity_op.title()} operation implementation",
                task_type="crud_operation",
                priority=task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours / len(entities),
                    required_capabilities=[AgentCapability.CODE_GENERATION],
                    estimation_source="crud_decomposition"
                )
            )
            task.add_child_task(op_task)
        
        # Add test task if requested
        if include_tests:
            test_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - Tests",
                description="CRUD operation tests",
                task_type="testing",
                priority=task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours * 0.3,
                    required_capabilities=[AgentCapability.TEST_GENERATION],
                    estimation_source="crud_decomposition"
                )
            )
            
            # Tests depend on all operations
            for op_task in task.child_tasks:
                if op_task.task_type == "crud_operation":
                    test_task.add_dependency(
                        op_task.id,
                        dependency_type=TaskDependencyType.FINISH_TO_START,
                        description=f"Test depends on {op_task.title}"
                    )
            
            task.add_child_task(test_task)
    
    def _decompose_ui_components(self, task: TaskEntity, params: Dict[str, Any]) -> None:
        """Decompose UI task into components"""
        components = params.get("components", ["layout", "navigation", "forms", "tables", "charts"])
        
        for component in components:
            component_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - {component.title()} Component",
                description=f"UI {component} component implementation",
                task_type="ui_component",
                priority=task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours / len(components),
                    required_capabilities=[AgentCapability.CODE_GENERATION],
                    estimation_source="ui_decomposition"
                )
            )
            
            # Add dependencies: some components depend on others
            if component in ["forms", "tables", "charts"]:
                # These depend on layout
                for layout_task in task.child_tasks:
                    if "layout" in layout_task.title.lower():
                        component_task.add_dependency(
                            layout_task.id,
                            dependency_type=TaskDependencyType.START_TO_START,
                            description="Requires layout component"
                        )
            
            task.add_child_task(component_task)
    
    def _decompose_security(self, task: TaskEntity, params: Dict[str, Any]) -> None:
        """Decompose security task with rigorous phases"""
        phases = params.get("phases", ["design", "implementation", "testing", "audit"])
        security_level = params.get("security_level", "high")
        
        # Adjust estimates based on security level
        level_multipliers = {
            "low": 0.5,
            "medium": 1.0,
            "high": 1.5,
            "critical": 2.0,
        }
        multiplier = level_multipliers.get(security_level, 1.0)
        
        previous_task = None
        for i, phase in enumerate(phases):
            phase_task = TaskEntity(
                session_id=task.session_id,
                parent_task_id=task.id,
                title=f"{task.title} - {phase.title()}",
                description=f"Security {phase} phase",
                task_type=f"security_{phase}",
                priority=TaskPriority.HIGH if security_level in ["high", "critical"] else task.priority,
                estimate=TaskEstimate(
                    likely_hours=task.estimate.likely_hours * multiplier / len(phases),
                    required_capabilities=self._get_security_capabilities(phase),
                    estimation_source="security_decomposition"
                )
            )
            
            # Add sequential dependencies
            if previous_task:
                phase_task.add_dependency(
                    previous_task.id,
                    dependency_type=TaskDependencyType.FINISH_TO_START,
                    description=f"Depends on {previous_task.title}"
                )
            
            task.add_child_task(phase_task)
            previous_task = phase_task
    
    def _get_security_capabilities(self, phase: str) -> List[AgentCapability]:
        """Get capabilities required for security phase"""
        phase_capabilities = {
            "design": [AgentCapability.SYSTEM_DESIGN, AgentCapability.SECURITY_AUDIT],
            "implementation": [AgentCapability.CODE_GENERATION, AgentCapability.SECURITY_AUDIT],
            "testing": [AgentCapability.TEST_GENERATION, AgentCapability.SECURITY_AUDIT],
            "audit": [AgentCapability.SECURITY_AUDIT, AgentCapability.CODE_REVIEW],
        }
        return phase_capabilities.get(phase, [Agent
