"""
INDUSTRIAL CONTEXT SERVICE
Orchestrates context creation, sharing, and lifecycle management.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import logging

from ...application.ports.repository_ports import ContextRepositoryPort
from ...domain.entities.context import (
    ContextEntity,
    ContextScope,
    ContextDiff,
    MergeStrategy,
)
from ...domain.exceptions.context_exceptions import (
    ContextNotFoundError,
    ContextScopeMismatchError,
    ContextAccessDeniedError,
)
from ..context import get_current_tenant_id

logger = logging.getLogger(__name__)


class ContextService:
    """
    Industrial-grade service for context management.
    
    Features:
    1. Context creation with scope validation
    2. Cross-session context sharing
    3. Conflict detection and resolution
    4. Lifecycle management (cleanup)
    5. Access control enforcement
    """
    
    def __init__(
        self,
        context_repository: ContextRepositoryPort,
        session_validator: Optional[Any] = None,  # SessionService for validation
        agent_validator: Optional[Any] = None,    # AgentManagementService for validation
    ):
        """
        Initialize context service.
        
        Args:
            context_repository: Repository for context persistence
            session_validator: Optional session validation service
            agent_validator: Optional agent validation service
        """
        self._repository = context_repository
        self._session_validator = session_validator
        self._agent_validator = agent_validator
    
    async def create_context(
        self,
        session_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        scope: ContextScope = ContextScope.SESSION,
        initial_data: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextEntity:
        """
        Create a new context.
        
        Args:
            session_id: Associated session ID (required for SESSION scope)
            agent_id: Associated agent ID (required for AGENT scope)
            scope: Context visibility scope
            initial_data: Initial key-value data
            created_by: Creator identifier
            metadata: Additional metadata
            
        Returns:
            Created ContextEntity
            
        Raises:
            ValueError: If scope requirements not met
        """
        # Validate scope requirements
        if scope == ContextScope.SESSION and not session_id:
            raise ValueError("SESSION scope requires session_id")
        
        if scope == ContextScope.AGENT and not agent_id:
            raise ValueError("AGENT scope requires agent_id")
        
        # Multi-tenant: Resolve tenant context
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            raise ValueError("Tenant context required for context creation")

        # Create context entity
        context = ContextEntity(
            id=uuid4(),
            tenant_id=tenant_id,
            session_id=session_id,
            agent_id=agent_id,
            scope=scope,
            data=initial_data or {},
            version=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=created_by,
            metadata=metadata or {}
        )
        
        # Store in repository
        await self._repository.store(context)
        
        logger.info(
            f"Created context {context.id} with scope {scope.value} "
            f"for session={session_id}, agent={agent_id}"
        )
        
        return context
    
    async def get_context(self, context_id: UUID) -> ContextEntity:
        """
        Get context by ID.
        
        Args:
            context_id: Context UUID
            
        Returns:
            ContextEntity
            
        Raises:
            ContextNotFoundError: If context not found
        """
        context = await self._repository.retrieve(context_id)
        if not context:
            raise ContextNotFoundError(context_id)
        return context
    
    async def get_or_create_context(
        self,
        session_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        scope: ContextScope = ContextScope.SESSION
    ) -> ContextEntity:
        """
        Get existing context or create new one.
        
        Useful for ensuring a context exists for a session/agent.
        """
        # Try to find existing context
        if session_id:
            contexts = await self._repository.retrieve_by_session(session_id)
            matching = [c for c in contexts if c.scope == scope]
            if matching:
                return matching[0]
        
        if agent_id:
            contexts = await self._repository.retrieve_by_agent(agent_id)
            matching = [c for c in contexts if c.scope == scope]
            if matching:
                return matching[0]
        
        # Create new context
        return await self.create_context(
            session_id=session_id,
            agent_id=agent_id,
            scope=scope
        )
    
    async def update_context(
        self,
        context_id: UUID,
        updates: Dict[str, Any],
        expected_version: Optional[int] = None,
        changed_by: Optional[str] = None
    ) -> ContextEntity:
        """
        Update context with optional version check.
        
        Args:
            context_id: Context UUID
            updates: Dict of key-value updates
            expected_version: Optional version for optimistic locking
            changed_by: Identifier of who made changes
            
        Returns:
            Updated ContextEntity
            
        Raises:
            ContextNotFoundError: If not found
            ContextConflictError: If version mismatch
        """
        context = await self.get_context(context_id)
        
        # Use repository's optimistic locking if version provided
        if expected_version is not None:
            return await self._repository.update(
                context_id,
                updates,
                expected_version
            )
        
        # Direct update without locking
        for key, value in updates.items():
            context.set(key, value, changed_by=changed_by)
        
        await self._repository.store(context)
        
        logger.debug(f"Updated context {context_id} with {len(updates)} changes")
        
        return context
    
    async def share_context(
        self,
        source_session_id: UUID,
        target_session_id: UUID,
        context_id: Optional[UUID] = None,
        merge_existing: bool = True
    ) -> ContextEntity:
        """
        Share context from one session to another.
        
        Args:
            source_session_id: Session to share from
            target_session_id: Session to share to
            context_id: Specific context to share (or share all)
            merge_existing: Merge with target's existing context
            
        Returns:
            Shared or merged ContextEntity
            
        Raises:
            ContextNotFoundError: If source context not found
        """
        # Get source context(s)
        if context_id:
            source_context = await self.get_context(context_id)
            if source_context.session_id != source_session_id:
                raise ContextAccessDeniedError(
                    context_id=context_id,
                    accessor_id=str(source_session_id),
                    required_permission="read",
                    message=f"Context {context_id} does not belong to session {source_session_id}"
                )
            source_contexts = [source_context]
        else:
            source_contexts = await self._repository.retrieve_by_session(source_session_id)
        
        if not source_contexts:
            raise ContextNotFoundError(
                context_id=context_id or UUID(int=0),
                message=f"No contexts found for session {source_session_id}"
            )
        
        # Get or create target context
        target_contexts = await self._repository.retrieve_by_session(target_session_id)
        target_context = target_contexts[0] if target_contexts else None
        
        # Merge or clone
        for source in source_contexts:
            if merge_existing and target_context:
                # Merge source into target
                merged = target_context.merge(source, strategy=MergeStrategy.DEEP_MERGE)
                merged.session_id = target_session_id
                await self._repository.store(merged)
                target_context = merged
            else:
                # Clone source for target
                cloned = source.clone()
                cloned.session_id = target_session_id
                cloned.metadata["shared_from"] = str(source_session_id)
                cloned.metadata["shared_at"] = datetime.now(timezone.utc).isoformat()
                await self._repository.store(cloned)
                target_context = cloned
        
        logger.info(
            f"Shared context from session {source_session_id} to {target_session_id}"
        )
        
        return target_context
    
    async def merge_contexts(
        self,
        context_ids: List[UUID],
        strategy: MergeStrategy = MergeStrategy.LAST_WRITE_WINS
    ) -> ContextEntity:
        """
        Merge multiple contexts into one.
        
        Args:
            context_ids: List of context IDs to merge
            strategy: Merge strategy for conflicts
            
        Returns:
            New merged ContextEntity
        """
        if len(context_ids) < 2:
            raise ValueError("Need at least 2 contexts to merge")
        
        merged = await self._repository.merge(
            context_ids,
            merge_strategy=strategy.value
        )
        
        logger.info(
            f"Merged {len(context_ids)} contexts into {merged.id} "
            f"using strategy {strategy.value}"
        )
        
        return merged
    
    async def promote_to_global(
        self,
        context_id: UUID,
        promoted_by: Optional[str] = None
    ) -> ContextEntity:
        """
        Promote a session/agent context to global scope.
        
        Args:
            context_id: Context to promote
            promoted_by: Identifier of who promoted
            
        Returns:
            New global ContextEntity
        """
        context = await self.get_context(context_id)
        
        if context.scope == ContextScope.GLOBAL:
            logger.debug(f"Context {context_id} is already global")
            return context
        
        if context.scope == ContextScope.TEMPORARY:
            raise ContextScopeMismatchError(
                context_id=context_id,
                expected_scope="session or agent",
                actual_scope=context.scope.value,
                operation="promote_to_global",
                message="Cannot promote temporary context to global"
            )
        
        global_context = await self._repository.promote_to_global(context_id)
        global_context.metadata["promoted_by"] = promoted_by
        
        logger.info(
            f"Promoted context {context_id} to global scope as {global_context.id}"
        )
        
        return global_context
    
    async def get_context_diff(
        self,
        context_id_a: UUID,
        context_id_b: UUID
    ) -> ContextDiff:
        """
        Calculate difference between two contexts.
        
        Args:
            context_id_a: First context
            context_id_b: Second context
            
        Returns:
            ContextDiff with additions, modifications, deletions
        """
        context_a = await self.get_context(context_id_a)
        context_b = await self.get_context(context_id_b)
        
        return context_a.diff(context_b)
    
    async def cleanup_session_contexts(
        self,
        session_id: UUID,
        promote_important: bool = True
    ) -> int:
        """
        Clean up contexts for a completed session.
        
        Args:
            session_id: Session whose contexts to clean
            promote_important: Promote marked-important contexts to global
            
        Returns:
            Number of contexts cleaned up
        """
        contexts = await self._repository.retrieve_by_session(session_id)
        cleaned = 0
        
        for context in contexts:
            # Check if should promote
            if promote_important and context.metadata.get("important"):
                await self.promote_to_global(context.id)
            else:
                # Let TTL expire naturally, or explicitly delete
                cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} contexts for session {session_id}")
        
        return cleaned
    
    async def get_global_contexts(self) -> List[ContextEntity]:
        """Get all global contexts."""
        return await self._repository.retrieve_global()
    
    async def get_session_context_summary(
        self,
        session_id: UUID
    ) -> Dict[str, Any]:
        """
        Get summary of contexts for a session.
        
        Returns:
            Summary with counts, sizes, and recent changes
        """
        contexts = await self._repository.retrieve_by_session(session_id)
        
        total_keys = 0
        recent_changes = []
        
        for context in contexts:
            total_keys += len(context.all_keys())
            recent = context.get_recent_changes(5)
            recent_changes.extend([
                {
                    "context_id": str(context.id),
                    "key": c.key,
                    "changed_at": c.changed_at.isoformat(),
                    "changed_by": c.changed_by,
                }
                for c in recent
            ])
        
        # Sort by time, most recent first
        recent_changes.sort(key=lambda x: x["changed_at"], reverse=True)
        
        return {
            "session_id": str(session_id),
            "context_count": len(contexts),
            "total_keys": total_keys,
            "contexts": [
                {
                    "id": str(c.id),
                    "scope": c.scope.value,
                    "version": c.version,
                    "key_count": len(c.all_keys()),
                    "updated_at": c.updated_at.isoformat(),
                }
                for c in contexts
            ],
            "recent_changes": recent_changes[:10],
        }
