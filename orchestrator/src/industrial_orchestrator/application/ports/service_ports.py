"""
INDUSTRIAL SERVICE PORTS
Abstract interfaces for external service integrations following Hexagonal Architecture.
These ports define contracts for infrastructure-agnostic service communication.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Type, Callable, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ServiceHealth(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ExecutionResult:
    """Result of an OpenCode execution."""
    success: bool
    output: str
    error: Optional[str] = None
    tokens_used: int = 0
    execution_time_seconds: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def is_error(self) -> bool:
        return not self.success or self.error is not None


@dataclass
class HealthCheckResult:
    """Result of a service health check."""
    status: ServiceHealth
    latency_ms: float
    details: Optional[Dict[str, Any]] = None
    checked_at: datetime = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.utcnow()


class OpenCodeClientPort(ABC):
    """
    Abstract interface for OpenCode API communication.
    
    Industrial Features:
    1. Async execution with timeout
    2. Health monitoring
    3. Configuration flexibility
    4. Result normalization
    """
    
    @abstractmethod
    async def execute_prompt(
        self,
        prompt: str,
        config: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 300.0
    ) -> ExecutionResult:
        """
        Execute a prompt via OpenCode API.
        
        Args:
            prompt: The prompt/task to execute
            config: Optional configuration overrides
            timeout_seconds: Maximum execution time
            
        Returns:
            ExecutionResult with output or error
        """
        pass
    
    @abstractmethod
    async def get_status(self) -> HealthCheckResult:
        """
        Check OpenCode service health.
        
        Returns:
            HealthCheckResult with status and latency
        """
        pass
    
    @abstractmethod
    async def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel an in-progress execution.
        
        Args:
            execution_id: ID of execution to cancel
            
        Returns:
            True if cancelled, False if not found or already complete
        """
        pass
    
    @abstractmethod
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get status of an ongoing execution.
        
        Args:
            execution_id: ID of execution
            
        Returns:
            Status dictionary with progress info
        """
        pass


class DistributedLockPort(ABC):
    """
    Abstract interface for distributed locking.
    
    Industrial Features:
    1. Fair locking with timeout
    2. Lock renewal (heartbeat)
    3. Deadlock prevention
    4. Lock metadata for debugging
    """
    
    @abstractmethod
    async def acquire(
        self,
        resource: str,
        timeout: float = 30.0,
        blocking: bool = True
    ) -> bool:
        """
        Acquire a distributed lock.
        
        Args:
            resource: Resource identifier to lock
            timeout: Maximum wait time for lock acquisition
            blocking: Whether to wait or return immediately
            
        Returns:
            True if lock acquired, False on timeout
        """
        pass
    
    @abstractmethod
    async def release(self, resource: str) -> bool:
        """
        Release a distributed lock.
        
        Args:
            resource: Resource identifier to release
            
        Returns:
            True if released, False if not owned
        """
        pass
    
    @abstractmethod
    async def renew(self, resource: str, additional_time: float = 30.0) -> bool:
        """
        Renew lock expiration.
        
        Args:
            resource: Resource identifier
            additional_time: Time to add to lock
            
        Returns:
            True if renewed, False if not owned
        """
        pass
    
    @abstractmethod
    async def is_locked(self, resource: str) -> bool:
        """
        Check if resource is currently locked.
        
        Args:
            resource: Resource identifier
            
        Returns:
            True if locked by any owner
        """
        pass
    
    @abstractmethod
    async def get_lock_info(self, resource: str) -> Optional[Dict[str, Any]]:
        """
        Get lock metadata.
        
        Args:
            resource: Resource identifier
            
        Returns:
            Lock metadata dict or None if not locked
        """
        pass
    
    @abstractmethod
    async def force_release(self, resource: str) -> bool:
        """
        Force release a lock (admin operation).
        
        Use with caution - may cause data inconsistency.
        
        Args:
            resource: Resource identifier
            
        Returns:
            True if released
        """
        pass


class MessageBusPort(ABC):
    """
    Abstract interface for event publishing and subscription.
    
    Industrial Features:
    1. Async event publishing
    2. Type-safe subscriptions
    3. Dead letter handling
    4. Event replay capability
    """
    
    @abstractmethod
    async def publish(
        self,
        event: Any,  # DomainEvent
        routing_key: Optional[str] = None
    ) -> None:
        """
        Publish a domain event.
        
        Args:
            event: Domain event to publish
            routing_key: Optional routing key for topic-based routing
        """
        pass
    
    @abstractmethod
    async def publish_batch(
        self,
        events: List[Any],  # List[DomainEvent]
        routing_key: Optional[str] = None
    ) -> None:
        """
        Publish multiple events atomically.
        
        Args:
            events: List of domain events
            routing_key: Optional routing key
        """
        pass
    
    @abstractmethod
    def subscribe(
        self,
        event_type: Type,
        handler: Callable,
        queue_name: Optional[str] = None
    ) -> None:
        """
        Subscribe to domain events.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Async handler function
            queue_name: Optional named queue for competing consumers
        """
        pass
    
    @abstractmethod
    def unsubscribe(
        self,
        event_type: Type,
        handler: Callable
    ) -> bool:
        """
        Unsubscribe from domain events.
        
        Args:
            event_type: Event type
            handler: Handler to remove
            
        Returns:
            True if handler was removed
        """
        pass
    
    @abstractmethod
    async def get_pending_events(
        self,
        event_type: Optional[Type] = None,
        limit: int = 100
    ) -> List[Any]:
        """
        Get pending events (for debugging/admin).
        
        Args:
            event_type: Optional filter by type
            limit: Maximum events to return
            
        Returns:
            List of pending events
        """
        pass


class CachePort(ABC):
    """
    Abstract interface for caching operations.
    
    Industrial Features:
    1. TTL-based expiration
    2. Namespace isolation
    3. Bulk operations
    4. Cache invalidation patterns
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set cached value with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cached value."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple cached values."""
        pass
    
    @abstractmethod
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set multiple cached values."""
        pass
    
    @abstractmethod
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern.
        
        Args:
            pattern: Glob-style pattern (e.g., "session:*")
            
        Returns:
            Number of keys deleted
        """
        pass
    
    @abstractmethod
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        pass


class MetricsPort(ABC):
    """
    Abstract interface for metrics collection.
    
    Industrial Features:
    1. Counter/Gauge/Histogram support
    2. Label-based dimensions
    3. Batch recording
    """
    
    @abstractmethod
    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        pass
    
    @abstractmethod
    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric value."""
        pass
    
    @abstractmethod
    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a value in a histogram."""
        pass
    
    @abstractmethod
    def record_timing(
        self,
        name: str,
        duration_seconds: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timing/latency metric."""
        pass


class ExternalAgentPort(ABC):
    """
    Abstract interface for communicating with external agents via EAP.
    
    Industrial Features:
    1. Protocol-agnostic dispatch (HTTP/WS)
    2. Type-safe DTOs
    3. Health monitoring
    """
    
    @abstractmethod
    async def send_task(
        self,
        agent_id: str,
        endpoint_url: str,
        auth_token: str,
        task_assignment: 'EAPTaskAssignment'
    ) -> 'EAPTaskResult':
        """
        Send a task to an external agent.
        
        Args:
            agent_id: ID of the agent
            endpoint_url: Agent's webhook URL
            auth_token: Authentication token
            task_assignment: Task details
            
        Returns:
            EAPTaskResult with status and artifacts
        """
        pass
    
    @abstractmethod
    async def check_health(
        self,
        agent_id: str,
        endpoint_url: str,
        auth_token: str
    ) -> 'EAPHeartbeatRequest':
        """
        Active health check for an external agent.
        
        Args:
            agent_id: ID of the agent
            endpoint_url: Agent's webhook URL
            auth_token: Authentication token
            
        Returns:
            EAPHeartbeatRequest with status metrics
        """
        pass


class TrainingProviderPort(ABC):
    """
    Abstract interface for external LLM training compute providers.
    """
    
    @abstractmethod
    async def start_training(self, job: Any) -> str: # Returns external_job_id
        """
        Submit a fine-tuning job to the provider.
        """
        pass
        
    @abstractmethod
    async def get_status(self, external_job_id: str) -> Dict[str, Any]:
        """
        Poll for job status and metrics.
        """
        pass
        
    @abstractmethod
    async def cancel_job(self, external_job_id: str) -> bool:
        """
        Stop an active training run.
        """
        pass
