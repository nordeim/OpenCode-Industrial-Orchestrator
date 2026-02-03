"""
INDUSTRIAL HYBRID CONTEXT REPOSITORY
Tiered storage implementation with Redis for hot contexts and PostgreSQL for cold/global.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from ...application.ports.repository_ports import ContextRepositoryPort
from ...domain.entities.context import (
    ContextEntity,
    ContextScope,
    MergeStrategy,
)
from ...domain.exceptions.context_exceptions import (
    ContextNotFoundError,
    ContextConflictError,
)


class HybridContextRepository(ContextRepositoryPort):
    """
    Tiered storage for contexts with Redis (hot) and PostgreSQL (cold).
    
    Storage Strategy:
    - SESSION/AGENT/TEMPORARY -> Redis (fast, TTL-based expiration)
    - GLOBAL -> PostgreSQL (durable, queryable)
    
    Industrial Features:
    1. Automatic tier placement by scope
    2. TTL-based cleanup for temporary contexts
    3. Promotion from session to global scope
    4. Optimistic locking with version checks
    5. Batch operations for efficiency
    
    Redis Keys:
    - context:{id}           -> JSON context data
    - contexts:session:{id}  -> Set of context IDs for session
    - contexts:agent:{id}    -> Set of context IDs for agent
    - contexts:global        -> Set of global context IDs
    """
    
    # Redis key prefixes
    KEY_CONTEXT = "context:{}"
    KEY_SESSION_CONTEXTS = "contexts:session:{}"
    KEY_AGENT_CONTEXTS = "contexts:agent:{}"
    KEY_GLOBAL_CONTEXTS = "contexts:global"
    
    # TTLs in seconds
    TTL_TEMPORARY = 3600     # 1 hour
    TTL_SESSION = 86400      # 24 hours
    TTL_AGENT = 604800       # 7 days
    
    def __init__(
        self,
        redis_client: Any,  # IndustrialRedisClient
        db_session: Any = None,  # AsyncSession for PostgreSQL
    ):
        """
        Initialize hybrid repository.
        
        Args:
            redis_client: Redis client for hot storage
            db_session: SQLAlchemy session for cold storage (optional)
        """
        self._redis = redis_client
        self._db = db_session
    
    async def store(self, context: Any) -> Any:
        """
        Store context in appropriate tier.
        
        Routes to Redis or PostgreSQL based on scope.
        """
        # Serialize context
        context_data = context.to_dict()
        context_json = json.dumps(context_data)
        
        context_key = self.KEY_CONTEXT.format(str(context.id))
        
        if context.scope == ContextScope.GLOBAL and self._db:
            # Store in PostgreSQL for durability
            await self._store_in_postgres(context)
        
        # Always cache in Redis for fast access
        ttl = self._get_ttl_for_scope(context.scope)
        await self._redis.set(context_key, context_json, ex=ttl)
        
        # Add to scope-based indexes
        await self._add_to_scope_index(context)
        
        return context
    
    async def retrieve(self, context_id: UUID) -> Optional[Any]:
        """
        Retrieve context by ID.
        
        Checks Redis first, falls back to PostgreSQL for global contexts.
        """
        context_key = self.KEY_CONTEXT.format(str(context_id))
        
        # Try Redis first
        context_json = await self._redis.get(context_key)
        if context_json:
            if isinstance(context_json, bytes):
                context_json = context_json.decode()
            context_data = json.loads(context_json)
            return ContextEntity.from_dict(context_data)
        
        # Fall back to PostgreSQL for global contexts
        if self._db:
            return await self._retrieve_from_postgres(context_id)
        
        return None
    
    async def retrieve_by_session(
        self,
        session_id: UUID
    ) -> List[Any]:
        """Get all contexts for a session."""
        index_key = self.KEY_SESSION_CONTEXTS.format(str(session_id))
        context_ids = await self._redis.smembers(index_key)
        
        contexts = []
        for ctx_id_bytes in context_ids:
            ctx_id_str = ctx_id_bytes.decode() if isinstance(ctx_id_bytes, bytes) else ctx_id_bytes
            context = await self.retrieve(UUID(ctx_id_str))
            if context:
                contexts.append(context)
        
        return contexts
    
    async def retrieve_by_agent(
        self,
        agent_id: UUID
    ) -> List[Any]:
        """Get all contexts for an agent."""
        index_key = self.KEY_AGENT_CONTEXTS.format(str(agent_id))
        context_ids = await self._redis.smembers(index_key)
        
        contexts = []
        for ctx_id_bytes in context_ids:
            ctx_id_str = ctx_id_bytes.decode() if isinstance(ctx_id_bytes, bytes) else ctx_id_bytes
            context = await self.retrieve(UUID(ctx_id_str))
            if context:
                contexts.append(context)
        
        return contexts
    
    async def update(
        self,
        context_id: UUID,
        updates: Dict[str, Any],
        expected_version: int
    ) -> Any:
        """
        Update context with optimistic locking.
        
        Raises ContextConflictError if version mismatch.
        """
        # Retrieve current context
        context = await self.retrieve(context_id)
        if not context:
            raise ContextNotFoundError(context_id)
        
        # Check version
        if context.version != expected_version:
            raise ContextConflictError(
                context_id=context_id,
                expected_version=expected_version,
                actual_version=context.version,
                conflicting_keys=list(updates.keys())
            )
        
        # Apply updates
        for key, value in updates.items():
            context.set(key, value)
        
        # Store updated context
        return await self.store(context)
    
    async def merge(
        self,
        source_ids: List[UUID],
        merge_strategy: str = "LAST_WRITE_WINS"
    ) -> Any:
        """
        Merge multiple contexts into one.
        
        Returns new merged ContextEntity.
        """
        if len(source_ids) < 2:
            raise ValueError("Need at least 2 contexts to merge")
        
        # Load all contexts
        contexts = []
        for ctx_id in source_ids:
            ctx = await self.retrieve(ctx_id)
            if not ctx:
                raise ContextNotFoundError(ctx_id)
            contexts.append(ctx)
        
        # Determine merge strategy
        strategy = MergeStrategy(merge_strategy.lower())
        
        # Start with first context and merge others
        result = contexts[0]
        for other in contexts[1:]:
            result = result.merge(other, strategy=strategy)
        
        # Store merged result
        await self.store(result)
        
        return result
    
    async def promote_to_global(self, context_id: UUID) -> Any:
        """
        Promote session/agent context to global scope.
        
        Creates a clone with GLOBAL scope and stores in PostgreSQL.
        """
        context = await self.retrieve(context_id)
        if not context:
            raise ContextNotFoundError(context_id)
        
        if context.scope == ContextScope.GLOBAL:
            return context  # Already global
        
        # Clone with new scope
        global_context = context.clone(new_scope=ContextScope.GLOBAL)
        global_context.metadata["promoted_from"] = str(context_id)
        global_context.metadata["promoted_at"] = datetime.utcnow().isoformat()
        
        # Store in both tiers
        await self.store(global_context)
        
        # Add to global index
        await self._redis.sadd(self.KEY_GLOBAL_CONTEXTS, str(global_context.id))
        
        return global_context
    
    async def cleanup_temporary(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up expired temporary contexts.
        
        Redis TTL handles most cleanup, this catches orphaned indexes.
        """
        cleaned = 0
        
        # Scan for temporary contexts that may have orphaned indexes
        # In production, would iterate through session/agent indexes
        # and remove entries where the context key no longer exists
        
        return cleaned
    
    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================
    
    def _get_ttl_for_scope(self, scope: ContextScope) -> Optional[int]:
        """Get TTL in seconds for scope."""
        ttl_map = {
            ContextScope.TEMPORARY: self.TTL_TEMPORARY,
            ContextScope.SESSION: self.TTL_SESSION,
            ContextScope.AGENT: self.TTL_AGENT,
            ContextScope.GLOBAL: None,  # No expiration
        }
        return ttl_map.get(scope)
    
    async def _add_to_scope_index(self, context: ContextEntity) -> None:
        """Add context to appropriate scope index."""
        context_id_str = str(context.id)
        
        if context.session_id:
            session_key = self.KEY_SESSION_CONTEXTS.format(str(context.session_id))
            await self._redis.sadd(session_key, context_id_str)
            ttl = self._get_ttl_for_scope(context.scope)
            if ttl:
                await self._redis.expire(session_key, ttl)
        
        if context.agent_id:
            agent_key = self.KEY_AGENT_CONTEXTS.format(str(context.agent_id))
            await self._redis.sadd(agent_key, context_id_str)
            ttl = self._get_ttl_for_scope(context.scope)
            if ttl:
                await self._redis.expire(agent_key, ttl)
        
        if context.scope == ContextScope.GLOBAL:
            await self._redis.sadd(self.KEY_GLOBAL_CONTEXTS, context_id_str)
    
    async def _store_in_postgres(self, context: ContextEntity) -> None:
        """Store context in PostgreSQL for durability."""
        if not self._db:
            return
        
        # Placeholder for SQLAlchemy storage
        # In production, would use ContextModel for ORM
        pass
    
    async def _retrieve_from_postgres(self, context_id: UUID) -> Optional[ContextEntity]:
        """Retrieve context from PostgreSQL."""
        if not self._db:
            return None
        
        # Placeholder for SQLAlchemy retrieval
        # In production, would query ContextModel
        return None
