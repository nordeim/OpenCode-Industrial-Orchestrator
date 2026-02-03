"""
INDUSTRIAL AGENT MANAGEMENT SERVICE
Orchestrates agent lifecycle, capability routing, and performance tracking.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import logging

from ...application.ports.repository_ports import AgentRepositoryPort
from ...application.ports.service_ports import DistributedLockPort
from ...domain.entities.registry import (
    RegisteredAgent,
    AgentRegistry,
    AgentCapability,
    AgentPerformanceTier,
    AgentLoadLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class TaskExecutionResult:
    """Result of a task execution on an agent."""
    success: bool
    partial_success: bool = False
    quality_score: Optional[float] = None
    execution_time_seconds: Optional[float] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class AgentPerformanceMetrics:
    """Aggregate performance metrics for an agent."""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    partial_successes: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    average_quality_score: Optional[float] = None
    average_execution_time: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks


@dataclass
class RebalanceResult:
    """Result of workload rebalancing."""
    tasks_rebalanced: int = 0
    agents_affected: List[UUID] = None
    before_utilization: float = 0.0
    after_utilization: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.agents_affected is None:
            self.agents_affected = []
        if self.errors is None:
            self.errors = []


@dataclass
class RouteTaskResult:
    """Result of task routing decision."""
    selected_agent: RegisteredAgent
    routing_score: float
    alternatives: List[RegisteredAgent]
    routing_reason: str


class AgentManagementService:
    """
    Industrial-grade service for managing agent lifecycle and task routing.
    
    Features:
    1. Agent registration with validation
    2. Capability-based task routing
    3. Performance-weighted load balancing
    4. Circuit breaker for degraded agents
    5. Workload rebalancing
    """
    
    # Routing weights
    WEIGHT_PERFORMANCE_TIER = 0.4
    WEIGHT_CAPABILITY_MATCH = 0.3
    WEIGHT_LOAD_LEVEL = 0.2
    WEIGHT_AVAILABILITY = 0.1
    
    # Circuit breaker thresholds
    CIRCUIT_BREAKER_THRESHOLD = 0.3  # Degraded below 30% success rate
    CIRCUIT_BREAKER_RECOVERY = 0.5   # Recover above 50% success rate
    
    def __init__(
        self,
        agent_repository: AgentRepositoryPort,
        lock_manager: Optional[DistributedLockPort] = None,
        local_registry: Optional[AgentRegistry] = None
    ):
        """
        Initialize agent management service.
        
        Args:
            agent_repository: Repository for agent persistence
            lock_manager: Distributed lock for coordination
            local_registry: Optional local registry for fast lookups
        """
        self._repository = agent_repository
        self._lock_manager = lock_manager
        self._local_registry = local_registry or AgentRegistry()
        self._metrics_cache: Dict[UUID, AgentPerformanceMetrics] = {}
    
    async def register_agent(
        self,
        name: str,
        agent_type: str,
        capabilities: List[AgentCapability],
        max_concurrent_capacity: int = 5,
        preferred_technologies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RegisteredAgent:
        """
        Register a new agent.
        
        Args:
            name: Agent name (must follow AGENT-XXX pattern)
            agent_type: Agent specialization type
            capabilities: Agent capabilities
            max_concurrent_capacity: Max concurrent tasks
            preferred_technologies: Preferred tech stack
            metadata: Additional metadata
            
        Returns:
            Registered agent
            
        Raises:
            ValueError: If validation fails
        """
        # Validate name format
        if not name.startswith("AGENT-"):
            raise ValueError("Agent name must start with 'AGENT-'")
        
        if len(capabilities) == 0:
            raise ValueError("Agent must have at least one capability")
        
        if max_concurrent_capacity < 1 or max_concurrent_capacity > 50:
            raise ValueError("max_concurrent_capacity must be between 1 and 50")
        
        # Create agent entity
        agent = RegisteredAgent(
            id=uuid4(),
            name=name,
            capabilities=set(capabilities),
            performance_tier=AgentPerformanceTier.COMPETENT,  # Start as competent
            load_level=AgentLoadLevel.IDLE,
            current_tasks=0,
            max_concurrent_tasks=max_concurrent_capacity,
            last_heartbeat=datetime.utcnow(),
            metadata={
                "agent_type": agent_type,
                "preferred_technologies": preferred_technologies or [],
                **(metadata or {})
            }
        )
        
        # Acquire lock if available
        lock_resource = f"agent:register:{name}"
        if self._lock_manager:
            acquired = await self._lock_manager.acquire(lock_resource, timeout=10.0)
            if not acquired:
                raise RuntimeError(f"Could not acquire lock for agent registration: {name}")
        
        try:
            # Register in repository
            await self._repository.register(agent)
            
            # Register in local registry for fast lookups
            self._local_registry.register(agent)
            
            # Initialize metrics
            self._metrics_cache[agent.id] = AgentPerformanceMetrics()
            
            logger.info(f"Registered agent: {name} ({agent.id}) with capabilities: {[c.value for c in capabilities]}")
            
            return agent
            
        finally:
            if self._lock_manager:
                await self._lock_manager.release(lock_resource)
    
    async def deregister_agent(
        self,
        agent_id: UUID,
        graceful: bool = True
    ) -> bool:
        """
        Deregister an agent.
        
        Args:
            agent_id: Agent ID to deregister
            graceful: Wait for current tasks to complete
            
        Returns:
            True if deregistered
        """
        agent = await self._repository.get_by_id(agent_id)
        if not agent:
            return False
        
        if graceful and agent.current_tasks > 0:
            logger.warning(f"Agent {agent.name} has {agent.current_tasks} active tasks, waiting...")
            # In production, would wait or reschedule tasks
        
        # Deregister from repository
        success = await self._repository.deregister(agent_id)
        
        if success:
            # Remove from local registry
            self._local_registry.deregister(agent_id)
            
            # Remove metrics cache
            self._metrics_cache.pop(agent_id, None)
            
            logger.info(f"Deregistered agent: {agent.name} ({agent_id})")
        
        return success
    
    async def route_task(
        self,
        task_description: str,
        required_capabilities: List[AgentCapability],
        preferred_agent_type: Optional[str] = None,
        preferred_agent_ids: Optional[List[UUID]] = None,
        min_performance_tier: Optional[AgentPerformanceTier] = None,
        estimated_complexity: float = 1.0
    ) -> RouteTaskResult:
        """
        Route a task to the best available agent.
        
        Uses weighted scoring based on:
        1. Performance tier
        2. Capability match
        3. Load level
        4. Availability
        
        Args:
            task_description: Task description for logging
            required_capabilities: Required agent capabilities
            preferred_agent_type: Preferred agent type
            preferred_agent_ids: Preferred specific agents
            min_performance_tier: Minimum required tier
            estimated_complexity: Task complexity (affects load calculation)
            
        Returns:
            RouteTaskResult with selected agent and alternatives
            
        Raises:
            ValueError: If no suitable agent found
        """
        # Find candidates from local registry first (fast)
        candidates = self._local_registry.find_by_capabilities(
            required_capabilities,
            available_only=True,
            match_all=True
        )
        
        if not candidates:
            # Fall back to repository
            for cap in required_capabilities:
                cap_agents = await self._repository.find_by_capability(cap, available_only=True)
                if not candidates:
                    candidates = cap_agents
                else:
                    # Intersection
                    cap_ids = {a.id for a in cap_agents}
                    candidates = [a for a in candidates if a.id in cap_ids]
        
        if not candidates:
            raise ValueError(f"No available agents with required capabilities: {required_capabilities}")
        
        # Filter by minimum tier if specified
        if min_performance_tier:
            tier_order = {
                AgentPerformanceTier.ELITE: 0,
                AgentPerformanceTier.ADVANCED: 1,
                AgentPerformanceTier.COMPETENT: 2,
                AgentPerformanceTier.TRAINEE: 3,
                AgentPerformanceTier.DEGRADED: 4,
            }
            min_order = tier_order.get(min_performance_tier, 4)
            candidates = [a for a in candidates if tier_order.get(a.performance_tier, 5) <= min_order]
        
        if not candidates:
            raise ValueError(f"No agents meet minimum tier requirement: {min_performance_tier}")
        
        # Filter out circuit-broken agents
        candidates = [a for a in candidates if a.performance_tier != AgentPerformanceTier.DEGRADED]
        
        if not candidates:
            raise ValueError("All capable agents are in degraded state")
        
        # Score candidates
        scored_candidates = []
        for agent in candidates:
            score = self._calculate_routing_score(
                agent,
                required_capabilities,
                preferred_agent_type,
                preferred_agent_ids,
                estimated_complexity
            )
            scored_candidates.append((agent, score))
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Select best agent
        selected_agent, best_score = scored_candidates[0]
        alternatives = [a for a, s in scored_candidates[1:4]]  # Top 3 alternatives
        
        # Determine routing reason
        routing_reason = self._generate_routing_reason(
            selected_agent,
            required_capabilities,
            best_score
        )
        
        logger.info(
            f"Routed task to agent {selected_agent.name} "
            f"(score: {best_score:.2f}, tier: {selected_agent.performance_tier.value})"
        )
        
        return RouteTaskResult(
            selected_agent=selected_agent,
            routing_score=best_score,
            alternatives=alternatives,
            routing_reason=routing_reason
        )
    
    async def update_agent_performance(
        self,
        agent_id: UUID,
        result: TaskExecutionResult
    ) -> None:
        """
        Update agent performance metrics based on task result.
        
        Args:
            agent_id: Agent ID
            result: Task execution result
        """
        # Get or create metrics
        if agent_id not in self._metrics_cache:
            self._metrics_cache[agent_id] = AgentPerformanceMetrics()
        
        metrics = self._metrics_cache[agent_id]
        
        # Update counts
        metrics.total_tasks += 1
        if result.success:
            metrics.successful_tasks += 1
        elif result.partial_success:
            metrics.partial_successes += 1
        else:
            metrics.failed_tasks += 1
        
        # Update aggregates
        if result.tokens_used:
            metrics.total_tokens_used += result.tokens_used
        
        if result.cost_usd:
            metrics.total_cost_usd += result.cost_usd
        
        # Update averages (simple moving average)
        if result.quality_score is not None:
            if metrics.average_quality_score is None:
                metrics.average_quality_score = result.quality_score
            else:
                metrics.average_quality_score = (
                    metrics.average_quality_score * 0.9 + result.quality_score * 0.1
                )
        
        if result.execution_time_seconds is not None:
            if metrics.average_execution_time is None:
                metrics.average_execution_time = result.execution_time_seconds
            else:
                metrics.average_execution_time = (
                    metrics.average_execution_time * 0.9 + result.execution_time_seconds * 0.1
                )
        
        # Update repository
        await self._repository.update_metrics(agent_id, metrics)
        
        # Check circuit breaker
        await self._check_circuit_breaker(agent_id, metrics)
        
        # Decrement task count
        self._local_registry.decrement_task_count(agent_id)
    
    async def get_agent_summary(
        self,
        agent_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive agent performance summary.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Performance summary dict or None
        """
        agent = await self._repository.get_by_id(agent_id)
        if not agent:
            return None
        
        metrics = self._metrics_cache.get(agent_id, AgentPerformanceMetrics())
        
        # Determine trend
        if metrics.total_tasks < 10:
            trend = "INSUFFICIENT_DATA"
        elif metrics.success_rate >= 0.9:
            trend = "IMPROVING"
        elif metrics.success_rate >= 0.7:
            trend = "STABLE"
        else:
            trend = "DECLINING"
        
        # Generate recommendations
        recommendations = []
        if metrics.success_rate < 0.7:
            recommendations.append("Consider reducing task complexity")
        if agent.load_level in [AgentLoadLevel.CRITICAL, AgentLoadLevel.OVERLOADED]:
            recommendations.append("Agent is overloaded, reduce task assignment")
        if metrics.average_execution_time and metrics.average_execution_time > 3600:
            recommendations.append("Average execution time is high, optimize task decomposition")
        
        return {
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "agent_type": agent.metadata.get("agent_type", "unknown"),
            "performance_tier": agent.performance_tier.value,
            "success_rate": metrics.success_rate,
            "average_quality_score": metrics.average_quality_score,
            "load_level": agent.load_level.value,
            "utilization_percentage": agent.utilization,
            "tasks_completed": metrics.total_tasks,
            "tasks_in_progress": agent.current_tasks,
            "average_cost_per_task": (
                metrics.total_cost_usd / metrics.total_tasks
                if metrics.total_tasks > 0 else None
            ),
            "average_tokens_per_task": (
                metrics.total_tokens_used // metrics.total_tasks
                if metrics.total_tasks > 0 else None
            ),
            "success_rate_trend": trend,
            "recommendations": recommendations,
        }
    
    async def rebalance_workload(self) -> RebalanceResult:
        """
        Rebalance workload across agents.
        
        Moves tasks from overloaded to underutilized agents.
        
        Returns:
            RebalanceResult with rebalancing details
        """
        result = RebalanceResult()
        
        # Get all agents
        available = await self._repository.find_available()
        overloaded = [a for a in self._local_registry._agents.values()
                      if a.load_level == AgentLoadLevel.OVERLOADED]
        
        if not overloaded or not available:
            return result
        
        # Calculate utilization before
        all_agents = list(self._local_registry._agents.values())
        if all_agents:
            result.before_utilization = sum(a.utilization for a in all_agents) / len(all_agents)
        
        # In production, would actually reassign tasks
        # For now, just log the rebalancing opportunity
        for agent in overloaded:
            logger.info(f"Agent {agent.name} is overloaded ({agent.current_tasks} tasks)")
            result.agents_affected.append(agent.id)
        
        # Calculate utilization after (unchanged in this stub)
        result.after_utilization = result.before_utilization
        
        return result
    
    async def heartbeat(self, agent_id: UUID) -> bool:
        """
        Process agent heartbeat.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if heartbeat processed
        """
        success = self._local_registry.update_heartbeat(agent_id)
        if success:
            await self._repository.heartbeat(agent_id)
        return success
    
    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================
    
    def _calculate_routing_score(
        self,
        agent: RegisteredAgent,
        required_capabilities: List[AgentCapability],
        preferred_agent_type: Optional[str],
        preferred_agent_ids: Optional[List[UUID]],
        estimated_complexity: float
    ) -> float:
        """Calculate routing score for an agent."""
        score = 0.0
        
        # Performance tier score (0-1)
        tier_scores = {
            AgentPerformanceTier.ELITE: 1.0,
            AgentPerformanceTier.ADVANCED: 0.8,
            AgentPerformanceTier.COMPETENT: 0.6,
            AgentPerformanceTier.TRAINEE: 0.4,
            AgentPerformanceTier.DEGRADED: 0.0,
        }
        score += tier_scores.get(agent.performance_tier, 0.5) * self.WEIGHT_PERFORMANCE_TIER
        
        # Capability match score (0-1)
        matched = sum(1 for cap in required_capabilities if cap in agent.capabilities)
        cap_score = matched / len(required_capabilities) if required_capabilities else 1.0
        score += cap_score * self.WEIGHT_CAPABILITY_MATCH
        
        # Load level score (0-1, lower load = higher score)
        load_scores = {
            AgentLoadLevel.IDLE: 1.0,
            AgentLoadLevel.OPTIMAL: 0.8,
            AgentLoadLevel.HIGH: 0.5,
            AgentLoadLevel.CRITICAL: 0.2,
            AgentLoadLevel.OVERLOADED: 0.0,
        }
        score += load_scores.get(agent.load_level, 0.5) * self.WEIGHT_LOAD_LEVEL
        
        # Availability bonus
        if agent.is_available:
            score += 1.0 * self.WEIGHT_AVAILABILITY
        
        # Preference bonuses
        if preferred_agent_ids and agent.id in preferred_agent_ids:
            score += 0.1
        
        if preferred_agent_type and agent.metadata.get("agent_type") == preferred_agent_type:
            score += 0.05
        
        return min(score, 1.0)
    
    def _generate_routing_reason(
        self,
        agent: RegisteredAgent,
        capabilities: List[AgentCapability],
        score: float
    ) -> str:
        """Generate human-readable routing explanation."""
        reasons = []
        
        if agent.performance_tier in [AgentPerformanceTier.ELITE, AgentPerformanceTier.ADVANCED]:
            reasons.append(f"high performance tier ({agent.performance_tier.value})")
        
        matched = sum(1 for cap in capabilities if cap in agent.capabilities)
        if matched == len(capabilities):
            reasons.append("full capability match")
        else:
            reasons.append(f"matched {matched}/{len(capabilities)} capabilities")
        
        if agent.load_level in [AgentLoadLevel.IDLE, AgentLoadLevel.OPTIMAL]:
            reasons.append("low current load")
        
        return f"Selected for: {', '.join(reasons)}. Score: {score:.2f}"
    
    async def _check_circuit_breaker(
        self,
        agent_id: UUID,
        metrics: AgentPerformanceMetrics
    ) -> None:
        """Check and apply circuit breaker if needed."""
        agent = self._local_registry.get_agent(agent_id)
        if not agent:
            return
        
        if metrics.total_tasks < 5:
            return  # Not enough data
        
        success_rate = metrics.success_rate
        
        if success_rate < self.CIRCUIT_BREAKER_THRESHOLD:
            if agent.performance_tier != AgentPerformanceTier.DEGRADED:
                agent.performance_tier = AgentPerformanceTier.DEGRADED
                self._local_registry.update_agent(agent)
                logger.warning(f"Circuit breaker OPEN for agent {agent.name} (success rate: {success_rate:.2%})")
        
        elif success_rate > self.CIRCUIT_BREAKER_RECOVERY:
            if agent.performance_tier == AgentPerformanceTier.DEGRADED:
                agent.performance_tier = AgentPerformanceTier.TRAINEE
                self._local_registry.update_agent(agent)
                logger.info(f"Circuit breaker CLOSED for agent {agent.name} (success rate: {success_rate:.2%})")
