"""
INDUSTRIAL AGENT REGISTRY
Domain entity for managing agent registration and capability-based discovery.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Set
from uuid import UUID
from threading import RLock
from enum import Enum

from .agent import AgentCapability, AgentPerformanceTier, AgentLoadLevel


@dataclass
class RegistryStatistics:
    """Aggregate statistics about the agent registry."""
    total_agents: int = 0
    available_agents: int = 0
    busy_agents: int = 0
    degraded_agents: int = 0
    agents_by_capability: Dict[str, int] = field(default_factory=dict)
    agents_by_tier: Dict[str, int] = field(default_factory=dict)
    agents_by_load: Dict[str, int] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RegisteredAgent:
    """
    Lightweight agent record for registry storage.
    Represents minimal data needed for capability-based routing.
    """
    id: UUID
    tenant_id: UUID
    name: str
    agent_type: str
    capabilities: Set[AgentCapability]
    preferred_technologies: List[str] = field(default_factory=list)
    performance_tier: AgentPerformanceTier = AgentPerformanceTier.COMPETENT
    load_level: AgentLoadLevel = AgentLoadLevel.IDLE
    current_tasks: int = 0
    max_concurrent_capacity: int = 5
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict = field(default_factory=dict)
    
    @property
    def is_available(self) -> bool:
        """Check if agent can accept new tasks."""
        return (
            self.current_tasks < self.max_concurrent_capacity
            and self.load_level != AgentLoadLevel.OVERLOADED
            and self.performance_tier != AgentPerformanceTier.DEGRADED
        )
    
    @property
    def utilization(self) -> float:
        """Calculate current utilization percentage."""
        if self.max_concurrent_capacity == 0:
            return 100.0
        return (self.current_tasks / self.max_concurrent_capacity) * 100
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities
    
    def has_all_capabilities(self, required: List[AgentCapability]) -> bool:
        """Check if agent has all required capabilities."""
        return all(cap in self.capabilities for cap in required)


class AgentRegistry:
    """
    Industrial-grade agent registry with capability-based discovery.
    
    Features:
    1. Thread-safe operations for concurrent access
    2. Capability-based indexing for fast lookups
    3. Performance tier tracking
    4. Load-aware availability checks
    5. Heartbeat-based health monitoring
    """
    
    def __init__(self):
        """Initialize empty registry with indexes."""
        self._agents: Dict[UUID, RegisteredAgent] = {}
        self._capability_index: Dict[AgentCapability, Set[UUID]] = {}
        self._tier_index: Dict[AgentPerformanceTier, Set[UUID]] = {}
        self._lock = RLock()
        self._statistics_cache: Optional[RegistryStatistics] = None
        self._stats_cache_time: Optional[datetime] = None
        self._stats_cache_ttl_seconds: float = 5.0
    
    def register(self, agent: RegisteredAgent) -> bool:
        """
        Register a new agent in the registry.
        
        Args:
            agent: Agent to register
            
        Returns:
            True if registered, False if already exists
        """
        with self._lock:
            if agent.id in self._agents:
                return False
            
            # Add to main storage
            self._agents[agent.id] = agent
            
            # Index by capabilities
            for capability in agent.capabilities:
                if capability not in self._capability_index:
                    self._capability_index[capability] = set()
                self._capability_index[capability].add(agent.id)
            
            # Index by tier
            if agent.performance_tier not in self._tier_index:
                self._tier_index[agent.performance_tier] = set()
            self._tier_index[agent.performance_tier].add(agent.id)
            
            # Invalidate stats cache
            self._invalidate_stats_cache()
            
            return True
    
    def deregister(self, agent_id: UUID) -> bool:
        """
        Remove an agent from the registry.
        
        Args:
            agent_id: ID of agent to remove
            
        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if agent_id not in self._agents:
                return False
            
            agent = self._agents[agent_id]
            
            # Remove from capability index
            for capability in agent.capabilities:
                if capability in self._capability_index:
                    self._capability_index[capability].discard(agent_id)
                    if not self._capability_index[capability]:
                        del self._capability_index[capability]
            
            # Remove from tier index
            if agent.performance_tier in self._tier_index:
                self._tier_index[agent.performance_tier].discard(agent_id)
                if not self._tier_index[agent.performance_tier]:
                    del self._tier_index[agent.performance_tier]
            
            # Remove from main storage
            del self._agents[agent_id]
            
            # Invalidate stats cache
            self._invalidate_stats_cache()
            
            return True
    
    def get_agent(self, agent_id: UUID) -> Optional[RegisteredAgent]:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent UUID
            
        Returns:
            RegisteredAgent or None
        """
        with self._lock:
            return self._agents.get(agent_id)
    
    def update_agent(self, agent: RegisteredAgent) -> bool:
        """
        Update an existing agent's data.
        
        Args:
            agent: Updated agent data
            
        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if agent.id not in self._agents:
                return False
            
            old_agent = self._agents[agent.id]
            
            # Handle capability changes
            old_caps = old_agent.capabilities
            new_caps = agent.capabilities
            
            removed_caps = old_caps - new_caps
            added_caps = new_caps - old_caps
            
            for cap in removed_caps:
                if cap in self._capability_index:
                    self._capability_index[cap].discard(agent.id)
            
            for cap in added_caps:
                if cap not in self._capability_index:
                    self._capability_index[cap] = set()
                self._capability_index[cap].add(agent.id)
            
            # Handle tier changes
            if old_agent.performance_tier != agent.performance_tier:
                if old_agent.performance_tier in self._tier_index:
                    self._tier_index[old_agent.performance_tier].discard(agent.id)
                if agent.performance_tier not in self._tier_index:
                    self._tier_index[agent.performance_tier] = set()
                self._tier_index[agent.performance_tier].add(agent.id)
            
            # Update main storage
            self._agents[agent.id] = agent
            
            # Invalidate stats cache
            self._invalidate_stats_cache()
            
            return True
    
    def find_by_capability(
        self,
        capability: AgentCapability,
        available_only: bool = True
    ) -> List[RegisteredAgent]:
        """
        Find agents with a specific capability.
        
        Args:
            capability: Required capability
            available_only: Filter to available agents
            
        Returns:
            List of matching agents sorted by performance tier
        """
        with self._lock:
            if capability not in self._capability_index:
                return []
            
            agent_ids = self._capability_index[capability]
            agents = [self._agents[aid] for aid in agent_ids if aid in self._agents]
            
            if available_only:
                agents = [a for a in agents if a.is_available]
            
            # Sort by performance tier (best first) then utilization (lowest first)
            tier_order = {
                AgentPerformanceTier.ELITE: 0,
                AgentPerformanceTier.ADVANCED: 1,
                AgentPerformanceTier.COMPETENT: 2,
                AgentPerformanceTier.TRAINEE: 3,
                AgentPerformanceTier.DEGRADED: 4,
            }
            
            agents.sort(key=lambda a: (tier_order.get(a.performance_tier, 5), a.utilization))
            
            return agents
    
    def find_by_capabilities(
        self,
        capabilities: List[AgentCapability],
        available_only: bool = True,
        match_all: bool = True
    ) -> List[RegisteredAgent]:
        """
        Find agents with multiple capabilities.
        
        Args:
            capabilities: Required capabilities
            available_only: Filter to available agents
            match_all: If True, agent must have ALL capabilities
            
        Returns:
            List of matching agents sorted by fit score
        """
        with self._lock:
            if not capabilities:
                return list(self._agents.values())
            
            if match_all:
                # Find agents with ALL capabilities (intersection)
                capability_sets = [
                    self._capability_index.get(cap, set())
                    for cap in capabilities
                ]
                if not all(capability_sets):
                    return []
                matching_ids = set.intersection(*capability_sets)
            else:
                # Find agents with ANY capability (union)
                matching_ids = set()
                for cap in capabilities:
                    matching_ids.update(self._capability_index.get(cap, set()))
            
            agents = [self._agents[aid] for aid in matching_ids if aid in self._agents]
            
            if available_only:
                agents = [a for a in agents if a.is_available]
            
            # Sort by capability match count (descending), then tier, then utilization
            tier_order = {
                AgentPerformanceTier.ELITE: 0,
                AgentPerformanceTier.ADVANCED: 1,
                AgentPerformanceTier.COMPETENT: 2,
                AgentPerformanceTier.TRAINEE: 3,
                AgentPerformanceTier.DEGRADED: 4,
            }
            
            def sort_key(agent: RegisteredAgent):
                cap_match = sum(1 for cap in capabilities if cap in agent.capabilities)
                return (-cap_match, tier_order.get(agent.performance_tier, 5), agent.utilization)
            
            agents.sort(key=sort_key)
            
            return agents
    
    def find_available(self) -> List[RegisteredAgent]:
        """
        Find all available agents.
        
        Returns:
            List of available agents sorted by utilization
        """
        with self._lock:
            agents = [a for a in self._agents.values() if a.is_available]
            agents.sort(key=lambda a: a.utilization)
            return agents
    
    def find_by_tier(
        self,
        tier: AgentPerformanceTier,
        available_only: bool = True
    ) -> List[RegisteredAgent]:
        """
        Find agents by performance tier.
        
        Args:
            tier: Target performance tier
            available_only: Filter to available agents
            
        Returns:
            List of matching agents
        """
        with self._lock:
            if tier not in self._tier_index:
                return []
            
            agent_ids = self._tier_index[tier]
            agents = [self._agents[aid] for aid in agent_ids if aid in self._agents]
            
            if available_only:
                agents = [a for a in agents if a.is_available]
            
            return agents
    
    def update_heartbeat(self, agent_id: UUID) -> bool:
        """
        Update agent's last heartbeat timestamp.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if agent_id not in self._agents:
                return False
            
            self._agents[agent_id].last_heartbeat = datetime.utcnow()
            return True
    
    def increment_task_count(self, agent_id: UUID) -> bool:
        """
        Increment agent's current task count.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if agent_id not in self._agents:
                return False
            
            agent = self._agents[agent_id]
            agent.current_tasks += 1
            
            # Update load level based on utilization
            agent.load_level = self._calculate_load_level(agent.utilization)
            
            self._invalidate_stats_cache()
            return True
    
    def decrement_task_count(self, agent_id: UUID) -> bool:
        """
        Decrement agent's current task count.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if agent_id not in self._agents:
                return False
            
            agent = self._agents[agent_id]
            agent.current_tasks = max(0, agent.current_tasks - 1)
            
            # Update load level based on utilization
            agent.load_level = self._calculate_load_level(agent.utilization)
            
            self._invalidate_stats_cache()
            return True
    
    def get_statistics(self, force_refresh: bool = False) -> RegistryStatistics:
        """
        Get aggregate registry statistics.
        
        Args:
            force_refresh: Bypass cache
            
        Returns:
            RegistryStatistics with current data
        """
        with self._lock:
            now = datetime.utcnow()
            
            # Check cache validity
            if (
                not force_refresh
                and self._statistics_cache is not None
                and self._stats_cache_time is not None
            ):
                age = (now - self._stats_cache_time).total_seconds()
                if age < self._stats_cache_ttl_seconds:
                    return self._statistics_cache
            
            # Compute fresh statistics
            stats = RegistryStatistics()
            stats.total_agents = len(self._agents)
            
            for agent in self._agents.values():
                # Availability
                if agent.is_available:
                    stats.available_agents += 1
                else:
                    stats.busy_agents += 1
                
                if agent.performance_tier == AgentPerformanceTier.DEGRADED:
                    stats.degraded_agents += 1
                
                # By capability
                for cap in agent.capabilities:
                    cap_name = cap.value
                    stats.agents_by_capability[cap_name] = stats.agents_by_capability.get(cap_name, 0) + 1
                
                # By tier
                tier_name = agent.performance_tier.value
                stats.agents_by_tier[tier_name] = stats.agents_by_tier.get(tier_name, 0) + 1
                
                # By load
                load_name = agent.load_level.value
                stats.agents_by_load[load_name] = stats.agents_by_load.get(load_name, 0) + 1
            
            stats.last_updated = now
            
            # Cache the result
            self._statistics_cache = stats
            self._stats_cache_time = now
            
            return stats
    
    def get_stale_agents(self, max_age_seconds: float = 300.0) -> List[RegisteredAgent]:
        """
        Find agents with stale heartbeats.
        
        Args:
            max_age_seconds: Maximum acceptable heartbeat age
            
        Returns:
            List of stale agents
        """
        with self._lock:
            now = datetime.utcnow()
            stale = []
            
            for agent in self._agents.values():
                age = (now - agent.last_heartbeat).total_seconds()
                if age > max_age_seconds:
                    stale.append(agent)
            
            return stale
    
    def cleanup_stale_agents(self, max_age_seconds: float = 300.0) -> int:
        """
        Remove agents with stale heartbeats.
        
        Args:
            max_age_seconds: Maximum acceptable heartbeat age
            
        Returns:
            Number of agents removed
        """
        stale = self.get_stale_agents(max_age_seconds)
        removed = 0
        
        for agent in stale:
            if self.deregister(agent.id):
                removed += 1
        
        return removed
    
    def _calculate_load_level(self, utilization: float) -> AgentLoadLevel:
        """Calculate load level from utilization percentage."""
        if utilization == 0:
            return AgentLoadLevel.IDLE
        elif utilization < 50:
            return AgentLoadLevel.OPTIMAL
        elif utilization < 80:
            return AgentLoadLevel.HIGH
        elif utilization < 100:
            return AgentLoadLevel.CRITICAL
        else:
            return AgentLoadLevel.OVERLOADED
    
    def _invalidate_stats_cache(self) -> None:
        """Invalidate statistics cache."""
        self._statistics_cache = None
        self._stats_cache_time = None
    
    def __len__(self) -> int:
        """Return number of registered agents."""
        with self._lock:
            return len(self._agents)
    
    def __contains__(self, agent_id: UUID) -> bool:
        """Check if agent is registered."""
        with self._lock:
            return agent_id in self._agents
