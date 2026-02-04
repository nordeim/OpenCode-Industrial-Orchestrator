"""
INDUSTRIAL REPOSITORY PORTS
Abstract interfaces for persistence operations following Hexagonal Architecture.
These ports define the contracts that infrastructure adapters must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Generic, TypeVar
from uuid import UUID
from datetime import datetime

# Generic type for entities
T = TypeVar('T')


class IndustrialRepositoryPort(ABC, Generic[T]):
    """
    Base repository port with common CRUD operations.
    
    Design Principles:
    1. Pure abstraction - no infrastructure dependencies
    2. Async-first for scalability
    3. Type-safe with generics
    """
    
    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """
        Retrieve entity by ID.
        
        Args:
            entity_id: Unique identifier
            
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        Persist entity (create or update).
        
        Args:
            entity: Entity to persist
            
        Returns:
            Persisted entity with updated metadata
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete entity by ID (soft delete preferred).
        
        Args:
            entity_id: Entity ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, entity_id: UUID) -> bool:
        """
        Check if entity exists.
        
        Args:
            entity_id: Entity ID to check
            
        Returns:
            True if exists
        """
        pass


class SessionRepositoryPort(ABC):
    """
    Session-specific repository operations.
    
    Industrial Features:
    1. Status-based queries
    2. Hierarchical queries (parent/child)
    3. Checkpoint management
    4. Bulk operations
    """
    
    @abstractmethod
    async def get_by_id(
        self,
        session_id: UUID,
        include_metrics: bool = False,
        include_checkpoints: bool = False
    ) -> Optional[Any]:  # Returns SessionEntity
        """
        Get session with optional eager loading.
        
        Args:
            session_id: Session UUID
            include_metrics: Load execution metrics
            include_checkpoints: Load checkpoint history
            
        Returns:
            SessionEntity or None
        """
        pass
    
    @abstractmethod
    async def save(self, session: Any) -> Any:  # SessionEntity
        """Persist session entity."""
        pass
    
    @abstractmethod
    async def delete(self, session_id: UUID) -> bool:
        """Soft delete session."""
        pass
    
    @abstractmethod
    async def find_by_status(
        self,
        status: Any,  # SessionStatus
        limit: int = 100,
        offset: int = 0
    ) -> List[Any]:  # List[SessionEntity]
        """Find sessions by status."""
        pass
    
    @abstractmethod
    async def find_active_sessions(self) -> List[Any]:
        """Find all non-terminal sessions."""
        pass
    
    @abstractmethod
    async def find_by_parent(self, parent_id: UUID) -> List[Any]:
        """Find child sessions of a parent."""
        pass
    
    @abstractmethod
    async def add_checkpoint(
        self,
        session_id: UUID,
        checkpoint_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add checkpoint to session."""
        pass
    
    @abstractmethod
    async def get_session_tree(
        self,
        root_session_id: UUID,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """Get hierarchical session tree."""
        pass
    
    @abstractmethod
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get aggregate session statistics."""
        pass
    
    @abstractmethod
    async def bulk_update_status(
        self,
        session_ids: List[UUID],
        new_status: Any  # SessionStatus
    ) -> int:
        """Bulk update session statuses. Returns count updated."""
        pass


class AgentRepositoryPort(ABC):
    """
    Agent registry and persistence operations.
    
    Industrial Features:
    1. Capability-based queries
    2. Heartbeat/health tracking
    3. Performance metrics persistence
    4. Load balancing support
    """
    
    @abstractmethod
    async def register(self, agent: Any) -> Any:  # AgentEntity
        """
        Register a new agent.
        
        Args:
            agent: Agent entity to register
            
        Returns:
            Registered agent with assigned ID
        """
        pass
    
    @abstractmethod
    async def deregister(self, agent_id: UUID) -> bool:
        """
        Deregister an agent.
        
        Args:
            agent_id: Agent ID to deregister
            
        Returns:
            True if deregistered, False if not found
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, agent_id: UUID) -> Optional[Any]:
        """Get agent by ID."""
        pass
    
    @abstractmethod
    async def find_by_capability(
        self,
        capability: Any,  # AgentCapability
        available_only: bool = True
    ) -> List[Any]:  # List[AgentEntity]
        """
        Find agents with specific capability.
        
        Args:
            capability: Required capability
            available_only: Filter to available agents
            
        Returns:
            List of matching agents sorted by performance tier
        """
        pass
    
    @abstractmethod
    async def find_available(self) -> List[Any]:
        """Find all available agents."""
        pass
    
    @abstractmethod
    async def update_metrics(
        self,
        agent_id: UUID,
        metrics: Any  # AgentPerformanceMetrics
    ) -> None:
        """Update agent performance metrics."""
        pass
    
    @abstractmethod
    async def heartbeat(self, agent_id: UUID) -> None:
        """
        Record agent heartbeat.
        
        Updates last_seen timestamp for health tracking.
        """
        pass
    
    @abstractmethod
    async def cleanup_stale_agents(self, max_age_seconds: int = 300) -> int:
        """
        Remove agents that haven't sent heartbeat.
        
        Args:
            max_age_seconds: Maximum age without heartbeat
            
        Returns:
            Number of agents cleaned up
        """
        pass
    
    @abstractmethod
    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get aggregate agent statistics."""
        pass


class ContextRepositoryPort(ABC):
    """
    Context storage and retrieval operations.
    
    Industrial Features:
    1. Scope-based storage (session, agent, global)
    2. Version tracking for optimistic locking
    3. Merge operations with conflict resolution
    4. Tiered storage (hot/cold)
    """
    
    @abstractmethod
    async def store(self, context: Any) -> Any:  # ContextEntity
        """
        Store context entity.
        
        Args:
            context: Context to store
            
        Returns:
            Stored context with updated version
        """
        pass
    
    @abstractmethod
    async def retrieve(self, context_id: UUID) -> Optional[Any]:
        """Retrieve context by ID."""
        pass
    
    @abstractmethod
    async def retrieve_by_session(
        self,
        session_id: UUID
    ) -> List[Any]:  # List[ContextEntity]
        """Get all contexts for a session."""
        pass
    
    @abstractmethod
    async def retrieve_by_agent(
        self,
        agent_id: UUID
    ) -> List[Any]:  # List[ContextEntity]
        """Get all contexts for an agent."""
        pass
    
    @abstractmethod
    async def update(
        self,
        context_id: UUID,
        updates: Dict[str, Any],
        expected_version: int
    ) -> Any:  # ContextEntity
        """
        Update context with optimistic locking.
        
        Args:
            context_id: Context ID
            updates: Data updates to apply
            expected_version: Expected version for conflict detection
            
        Returns:
            Updated context
            
        Raises:
            ContextConflictError if version mismatch
        """
        pass
    
    @abstractmethod
    async def merge(
        self,
        source_ids: List[UUID],
        merge_strategy: str = "LAST_WRITE_WINS"
    ) -> Any:  # ContextEntity
        """
        Merge multiple contexts.
        
        Args:
            source_ids: Context IDs to merge
            merge_strategy: LAST_WRITE_WINS, DEEP_MERGE, or MANUAL
            
        Returns:
            New merged context
        """
        pass
    
    @abstractmethod
    async def promote_to_global(self, context_id: UUID) -> Any:
        """Promote session/agent context to global scope."""
        pass
    
    @abstractmethod
    async def cleanup_temporary(self, max_age_seconds: int = 3600) -> int:
        """Clean up temporary contexts older than max_age."""
        pass


class TaskRepositoryPort(ABC):
    """
    Task persistence operations.
    
    Industrial Features:
    1. Hierarchical task queries (subtasks)
    2. Dependency graph persistence
    3. Status-based filtering
    4. Session association
    """
    
    @abstractmethod
    async def save(self, task: Any) -> Any:  # TaskEntity
        """Persist task entity."""
        pass
    
    @abstractmethod
    async def get_by_id(
        self,
        task_id: UUID,
        include_subtasks: bool = False
    ) -> Optional[Any]:
        """Get task with optional subtask loading."""
        pass
    
    @abstractmethod
    async def find_by_session(
        self,
        session_id: UUID,
        status: Optional[Any] = None  # TaskStatus
    ) -> List[Any]:
        """Find tasks belonging to a session."""
        pass
    
    @abstractmethod
    async def find_root_tasks(self, session_id: UUID) -> List[Any]:
        """Find top-level tasks without parents."""
        pass
    
    @abstractmethod
    async def get_task_tree(
        self,
        root_task_id: UUID,
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """Get hierarchical task tree."""
        pass
    
    @abstractmethod
    async def update_status(
        self,
        task_id: UUID,
        status: Any,  # TaskStatus
        result: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Update task status."""
        pass
    
    @abstractmethod
    async def add_dependency(
        self,
        task_id: UUID,
        depends_on_id: UUID,
        dependency_type: str = "FINISH_TO_START"
    ) -> None:
        """Add task dependency."""
        pass


class FineTuningRepositoryPort(ABC):
    """
    Fine-tuning job persistence operations.
    """
    
    @abstractmethod
    async def save(self, job: Any) -> Any:  # FineTuningJob
        """Persist fine-tuning job."""
        pass
    
    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> Optional[Any]:
        """Retrieve job by ID."""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: Any) -> List[Any]:
        """Find jobs by status."""
        pass
    
    @abstractmethod
    async def get_active_jobs(self) -> List[Any]:
        """Retrieve all currently running or queued jobs."""
        pass
