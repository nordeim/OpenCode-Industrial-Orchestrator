"""
INDUSTRIAL REDIS AGENT REPOSITORY
Redis-backed implementation of AgentRepositoryPort for distributed deployments.
"""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from uuid import UUID

from ..database.redis_client import IndustrialRedisClient
from ...application.ports.repository_ports import AgentRepositoryPort
from ...domain.entities.registry import (
    RegisteredAgent,
    AgentCapability,
    AgentPerformanceTier,
    AgentLoadLevel,
)


class RedisAgentRepository(AgentRepositoryPort):
    """
    Redis-backed agent repository for distributed agent management.
    
    Storage Schema:
    - agent:{id}           -> Hash containing agent data
    - agents:all           -> Set of all agent IDs
    - agents:available     -> Set of available agent IDs
    - agents:cap:{cap}     -> Set of agent IDs with capability
    - agents:tier:{tier}   -> Set of agent IDs in tier
    - agents:metrics:{id}  -> Hash containing performance metrics
    
    Industrial Features:
    1. Atomic operations for registration/deregistration
    2. TTL-based heartbeat expiration
    3. Capability set indexing
    4. Pipeline-based bulk operations
    5. Automatic staleness detection
    """
    
    # Redis key prefixes
    KEY_AGENT = "agent:{}"
    KEY_ALL_AGENTS = "agents:all"
    KEY_AVAILABLE = "agents:available"
    KEY_CAPABILITY = "agents:cap:{}"
    KEY_TIER = "agents:tier:{}"
    KEY_METRICS = "agents:metrics:{}"
    
    # Default TTL for agent heartbeat (5 minutes)
    DEFAULT_HEARTBEAT_TTL = 300
    
    def __init__(
        self,
        redis_client: IndustrialRedisClient,
        heartbeat_ttl: int = DEFAULT_HEARTBEAT_TTL
    ):
        """
        Initialize Redis agent repository.
        
        Args:
            redis_client: Industrial Redis client
            heartbeat_ttl: TTL for heartbeat expiration in seconds
        """
        self._redis = redis_client
        self._heartbeat_ttl = heartbeat_ttl
    
    async def register(self, agent: Any) -> Any:
        """
        Register a new agent.
        
        Uses Redis pipeline for atomic multi-key operations.
        """
        agent_id = str(agent.id)
        agent_key = self.KEY_AGENT.format(agent_id)
        
        # Serialize agent data
        agent_data = self._serialize_agent(agent)
        
        # Use pipeline for atomicity
        async with self._redis.pipeline() as pipe:
            # Store agent hash
            await pipe.hset(agent_key, mapping=agent_data)
            await pipe.expire(agent_key, self._heartbeat_ttl)
            
            # Add to all agents set
            await pipe.sadd(self.KEY_ALL_AGENTS, agent_id)
            
            # Add to capability sets
            for cap in agent.capabilities:
                cap_key = self.KEY_CAPABILITY.format(cap.value if hasattr(cap, 'value') else cap)
                await pipe.sadd(cap_key, agent_id)
            
            # Add to tier set
            tier_value = agent.performance_tier.value if hasattr(agent.performance_tier, 'value') else agent.performance_tier
            tier_key = self.KEY_TIER.format(tier_value)
            await pipe.sadd(tier_key, agent_id)
            
            # Add to available if applicable
            if self._is_agent_available(agent):
                await pipe.sadd(self.KEY_AVAILABLE, agent_id)
            
            await pipe.execute()
        
        return agent
    
    async def deregister(self, agent_id: UUID) -> bool:
        """
        Deregister an agent.
        
        Removes agent from all indexes atomically.
        """
        agent_id_str = str(agent_id)
        agent_key = self.KEY_AGENT.format(agent_id_str)
        
        # Get agent data first to remove from indexes
        agent_data = await self._redis.hgetall(agent_key)
        if not agent_data:
            return False
        
        agent = self._deserialize_agent(agent_data, agent_id)
        
        async with self._redis.pipeline() as pipe:
            # Remove from main storage
            await pipe.delete(agent_key)
            
            # Remove from all agents set
            await pipe.srem(self.KEY_ALL_AGENTS, agent_id_str)
            
            # Remove from capability sets
            for cap in agent.capabilities:
                cap_key = self.KEY_CAPABILITY.format(cap.value if hasattr(cap, 'value') else cap)
                await pipe.srem(cap_key, agent_id_str)
            
            # Remove from tier set
            tier_value = agent.performance_tier.value if hasattr(agent.performance_tier, 'value') else agent.performance_tier
            tier_key = self.KEY_TIER.format(tier_value)
            await pipe.srem(tier_key, agent_id_str)
            
            # Remove from available
            await pipe.srem(self.KEY_AVAILABLE, agent_id_str)
            
            # Remove metrics
            metrics_key = self.KEY_METRICS.format(agent_id_str)
            await pipe.delete(metrics_key)
            
            await pipe.execute()
        
        return True
    
    async def get_by_id(self, agent_id: UUID) -> Optional[Any]:
        """Get agent by ID."""
        agent_key = self.KEY_AGENT.format(str(agent_id))
        agent_data = await self._redis.hgetall(agent_key)
        
        if not agent_data:
            return None
        
        return self._deserialize_agent(agent_data, agent_id)
    
    async def find_by_capability(
        self,
        capability: Any,
        available_only: bool = True
    ) -> List[Any]:
        """
        Find agents with specific capability.
        
        Uses set intersection for available filtering.
        """
        cap_value = capability.value if hasattr(capability, 'value') else capability
        cap_key = self.KEY_CAPABILITY.format(cap_value)
        
        if available_only:
            # Intersection of capability set and available set
            agent_ids = await self._redis.sinter(cap_key, self.KEY_AVAILABLE)
        else:
            agent_ids = await self._redis.smembers(cap_key)
        
        agents = []
        for agent_id_bytes in agent_ids:
            agent_id_str = agent_id_bytes.decode() if isinstance(agent_id_bytes, bytes) else agent_id_bytes
            agent = await self.get_by_id(UUID(agent_id_str))
            if agent:
                agents.append(agent)
        
        # Sort by performance tier then utilization
        tier_order = {
            AgentPerformanceTier.ELITE: 0,
            AgentPerformanceTier.ADVANCED: 1,
            AgentPerformanceTier.COMPETENT: 2,
            AgentPerformanceTier.TRAINEE: 3,
            AgentPerformanceTier.DEGRADED: 4,
        }
        
        agents.sort(key=lambda a: (
            tier_order.get(a.performance_tier, 5),
            a.utilization
        ))
        
        return agents
    
    async def find_available(self) -> List[Any]:
        """Find all available agents."""
        agent_ids = await self._redis.smembers(self.KEY_AVAILABLE)
        
        agents = []
        for agent_id_bytes in agent_ids:
            agent_id_str = agent_id_bytes.decode() if isinstance(agent_id_bytes, bytes) else agent_id_bytes
            agent = await self.get_by_id(UUID(agent_id_str))
            if agent:
                agents.append(agent)
        
        # Sort by utilization (lowest first)
        agents.sort(key=lambda a: a.utilization)
        
        return agents
    
    async def update_metrics(
        self,
        agent_id: UUID,
        metrics: Any
    ) -> None:
        """Update agent performance metrics."""
        metrics_key = self.KEY_METRICS.format(str(agent_id))
        
        metrics_data = {
            "total_tasks": str(metrics.total_tasks),
            "successful_tasks": str(metrics.successful_tasks),
            "failed_tasks": str(metrics.failed_tasks),
            "partial_successes": str(metrics.partial_successes),
            "success_rate": str(metrics.success_rate),
            "total_tokens_used": str(metrics.total_tokens_used),
            "total_cost_usd": str(metrics.total_cost_usd),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        if hasattr(metrics, 'average_quality_score') and metrics.average_quality_score is not None:
            metrics_data["average_quality_score"] = str(metrics.average_quality_score)
        
        if hasattr(metrics, 'average_execution_time') and metrics.average_execution_time is not None:
            metrics_data["average_execution_time"] = str(metrics.average_execution_time)
        
        await self._redis.hset(metrics_key, mapping=metrics_data)
        
        # Update agent's performance tier based on metrics
        await self._update_agent_tier(agent_id, metrics)
    
    async def heartbeat(self, agent_id: UUID) -> None:
        """
        Record agent heartbeat.
        
        Refreshes TTL on agent key and updates last_heartbeat.
        """
        agent_key = self.KEY_AGENT.format(str(agent_id))
        
        # Check if agent exists
        exists = await self._redis.exists(agent_key)
        if not exists:
            return
        
        async with self._redis.pipeline() as pipe:
            # Update heartbeat timestamp
            await pipe.hset(agent_key, "last_heartbeat", datetime.utcnow().isoformat())
            
            # Refresh TTL
            await pipe.expire(agent_key, self._heartbeat_ttl)
            
            await pipe.execute()
    
    async def cleanup_stale_agents(self, max_age_seconds: int = 300) -> int:
        """
        Remove agents that haven't sent heartbeat.
        
        Uses Redis key expiration - agents expire automatically.
        This method scans for orphaned index entries.
        """
        cleaned = 0
        
        # Get all registered agent IDs
        all_agent_ids = await self._redis.smembers(self.KEY_ALL_AGENTS)
        
        for agent_id_bytes in all_agent_ids:
            agent_id_str = agent_id_bytes.decode() if isinstance(agent_id_bytes, bytes) else agent_id_bytes
            agent_key = self.KEY_AGENT.format(agent_id_str)
            
            # If agent key doesn't exist (expired), clean up indexes
            exists = await self._redis.exists(agent_key)
            if not exists:
                # Get partial data from sets to clean up
                await self._cleanup_agent_indexes(UUID(agent_id_str))
                cleaned += 1
        
        return cleaned
    
    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get aggregate agent statistics."""
        all_count = await self._redis.scard(self.KEY_ALL_AGENTS)
        available_count = await self._redis.scard(self.KEY_AVAILABLE)
        
        # Count by tier
        by_tier = {}
        for tier in AgentPerformanceTier:
            tier_key = self.KEY_TIER.format(tier.value)
            count = await self._redis.scard(tier_key)
            by_tier[tier.value] = count
        
        # Count by capability
        by_capability = {}
        for cap in AgentCapability:
            cap_key = self.KEY_CAPABILITY.format(cap.value)
            count = await self._redis.scard(cap_key)
            if count > 0:
                by_capability[cap.value] = count
        
        return {
            "total_agents": all_count,
            "available_agents": available_count,
            "agents_by_tier": by_tier,
            "agents_by_capability": by_capability,
        }
    
    # =========================================================================
    # PRIVATE HELPER METHODS
    # =========================================================================
    
    def _serialize_agent(self, agent: RegisteredAgent) -> Dict[str, str]:
        """Serialize agent to Redis hash format."""
        caps = [c.value if hasattr(c, 'value') else c for c in agent.capabilities]
        
        return {
            "name": agent.name,
            "capabilities": json.dumps(caps),
            "performance_tier": agent.performance_tier.value if hasattr(agent.performance_tier, 'value') else agent.performance_tier,
            "load_level": agent.load_level.value if hasattr(agent.load_level, 'value') else agent.load_level,
            "current_tasks": str(agent.current_tasks),
            "max_concurrent_tasks": str(agent.max_concurrent_tasks),
            "last_heartbeat": agent.last_heartbeat.isoformat(),
            "metadata": json.dumps(agent.metadata) if agent.metadata else "{}",
        }
    
    def _deserialize_agent(self, data: Dict, agent_id: UUID) -> RegisteredAgent:
        """Deserialize agent from Redis hash format."""
        # Handle bytes from Redis
        def decode(value):
            if isinstance(value, bytes):
                return value.decode()
            return value
        
        data = {decode(k): decode(v) for k, v in data.items()}
        
        # Parse capabilities
        caps_raw = json.loads(data.get("capabilities", "[]"))
        capabilities = set()
        for cap in caps_raw:
            try:
                capabilities.add(AgentCapability(cap))
            except ValueError:
                pass  # Skip unknown capabilities
        
        # Parse enums
        try:
            tier = AgentPerformanceTier(data.get("performance_tier", "competent"))
        except ValueError:
            tier = AgentPerformanceTier.COMPETENT
        
        try:
            load = AgentLoadLevel(data.get("load_level", "idle"))
        except ValueError:
            load = AgentLoadLevel.IDLE
        
        # Parse timestamp
        try:
            last_heartbeat = datetime.fromisoformat(data.get("last_heartbeat", ""))
        except (ValueError, TypeError):
            last_heartbeat = datetime.utcnow()
        
        return RegisteredAgent(
            id=agent_id,
            name=data.get("name", ""),
            capabilities=capabilities,
            performance_tier=tier,
            load_level=load,
            current_tasks=int(data.get("current_tasks", 0)),
            max_concurrent_tasks=int(data.get("max_concurrent_tasks", 5)),
            last_heartbeat=last_heartbeat,
            metadata=json.loads(data.get("metadata", "{}")),
        )
    
    def _is_agent_available(self, agent: RegisteredAgent) -> bool:
        """Check if agent should be in available set."""
        return (
            agent.current_tasks < agent.max_concurrent_tasks
            and agent.load_level != AgentLoadLevel.OVERLOADED
            and agent.performance_tier != AgentPerformanceTier.DEGRADED
        )
    
    async def _update_agent_tier(self, agent_id: UUID, metrics: Any) -> None:
        """Update agent's performance tier based on metrics."""
        # Calculate new tier based on success rate
        success_rate = getattr(metrics, 'success_rate', 0.5)
        
        if success_rate >= 0.95:
            new_tier = AgentPerformanceTier.ELITE
        elif success_rate >= 0.85:
            new_tier = AgentPerformanceTier.ADVANCED
        elif success_rate >= 0.70:
            new_tier = AgentPerformanceTier.COMPETENT
        elif success_rate >= 0.50:
            new_tier = AgentPerformanceTier.TRAINEE
        else:
            new_tier = AgentPerformanceTier.DEGRADED
        
        agent = await self.get_by_id(agent_id)
        if agent and agent.performance_tier != new_tier:
            # Update tier in agent hash
            agent_key = self.KEY_AGENT.format(str(agent_id))
            await self._redis.hset(agent_key, "performance_tier", new_tier.value)
            
            # Update tier indexes
            old_tier_key = self.KEY_TIER.format(agent.performance_tier.value)
            new_tier_key = self.KEY_TIER.format(new_tier.value)
            
            async with self._redis.pipeline() as pipe:
                await pipe.srem(old_tier_key, str(agent_id))
                await pipe.sadd(new_tier_key, str(agent_id))
                await pipe.execute()
    
    async def _cleanup_agent_indexes(self, agent_id: UUID) -> None:
        """Clean up orphaned index entries for a removed agent."""
        agent_id_str = str(agent_id)
        
        async with self._redis.pipeline() as pipe:
            # Remove from all agents
            await pipe.srem(self.KEY_ALL_AGENTS, agent_id_str)
            
            # Remove from available
            await pipe.srem(self.KEY_AVAILABLE, agent_id_str)
            
            # Remove from all capability sets
            for cap in AgentCapability:
                cap_key = self.KEY_CAPABILITY.format(cap.value)
                await pipe.srem(cap_key, agent_id_str)
            
            # Remove from all tier sets
            for tier in AgentPerformanceTier:
                tier_key = self.KEY_TIER.format(tier.value)
                await pipe.srem(tier_key, agent_id_str)
            
            await pipe.execute()
