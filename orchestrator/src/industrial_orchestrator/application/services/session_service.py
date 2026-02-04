"""
INDUSTRIAL SESSION SERVICE
Application service for session management with business logic.
Implements use cases and coordinates between domain, infrastructure, and presentation layers.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4

from ...domain.entities.session import SessionEntity, SessionType, SessionPriority
from ...domain.value_objects.session_status import SessionStatus
from ...domain.events.session_events import (
    SessionCreated,
    SessionStatusChanged,
    SessionCompleted,
    SessionFailed,
)
from ...domain.exceptions.session_exceptions import (
    InvalidSessionTransition,
    SessionNotFoundError,
    SessionTimeoutError,
)
from ...infrastructure.repositories.session_repository import SessionRepository
from ...infrastructure.locking.distributed_lock import distributed_lock
from ...infrastructure.adapters.opencode_client import IndustrialOpenCodeClient
from ...application.ports.service_ports import ExternalAgentPort
from ...application.ports.repository_ports import AgentRepositoryPort, TenantRepositoryPort
from ...application.dtos.external_agent_protocol import EAPTaskAssignment
from ...domain.exceptions.tenant_exceptions import QuotaExceededError, TenantNotFoundError
from ...application.context import get_current_tenant_id


class SessionService:
    """
    Industrial Session Service
    
    Orchestrates session management with:
    1. Business logic enforcement
    2. Event publishing
    3. Distributed coordination
    4. Error handling and retry
    5. Performance monitoring
    """
    
    def __init__(
        self,
        session_repository: Optional[SessionRepository] = None,
        agent_repository: Optional[AgentRepositoryPort] = None,
        tenant_repository: Optional[TenantRepositoryPort] = None,
        opencode_client: Optional[IndustrialOpenCodeClient] = None,
        external_agent_adapter: Optional[ExternalAgentPort] = None,
        lock_timeout: int = 30
    ):
        self.session_repository = session_repository or SessionRepository()
        self.agent_repository = agent_repository
        self.tenant_repository = tenant_repository
        self.opencode_client = opencode_client
        self.external_agent_adapter = external_agent_adapter
        self.lock_timeout = lock_timeout
        self._logger = logging.getLogger(__name__)
        
        # Event handlers (would be connected to event bus in production)
        self._event_handlers: Dict[str, List[callable]] = {}
    
    async def initialize(self) -> None:
        """Initialize service dependencies"""
        await self.session_repository.initialize()
        
        if self.opencode_client:
            await self.opencode_client.initialize()
    
    async def create_session(
        self,
        title: str,
        initial_prompt: str,
        session_type: SessionType = SessionType.EXECUTION,
        priority: SessionPriority = SessionPriority.MEDIUM,
        agent_config: Optional[Dict[str, Any]] = None,
        model_config: Optional[str] = None,
        parent_session_id: Optional[UUID] = None,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SessionEntity:
        """
        Create a new session with industrial validation
        
        Args:
            title: Industrial session title
            initial_prompt: Task description or prompt
            session_type: Type of session
            priority: Execution priority
            agent_config: Agent configuration
            model_config: Model configuration string
            parent_session_id: Parent session ID for hierarchies
            created_by: Creator identifier
            tags: Session tags
            metadata: Additional metadata
        
        Returns:
            SessionEntity: Created session
        """
        # Validate inputs
        if not title or not title.strip():
            raise ValueError("Session title is required")
        
        if not initial_prompt or not initial_prompt.strip():
            raise ValueError("Initial prompt is required")
        
        # Multi-tenant: Resolve tenant context
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            raise ValueError("Tenant context required for session creation")
            
        # Check Quota
        if self.tenant_repository:
            tenant = await self.tenant_repository.get_by_id(tenant_id)
            if not tenant:
                raise TenantNotFoundError(f"Tenant {tenant_id} not found")
                
            active_count = await self.session_repository.count_active_by_tenant(tenant_id)
            if active_count >= tenant.max_concurrent_sessions:
                raise QuotaExceededError("concurrent_sessions", tenant.max_concurrent_sessions)
        
        # Create session entity
        session = SessionEntity(
            tenant_id=tenant_id,
            title=title.strip(),
            initial_prompt=initial_prompt.strip(),
            session_type=session_type,
            priority=priority,
            agent_config=agent_config or {"default_agent": "industrial-coder"},
            model_config=model_config,
            parent_id=parent_session_id,
            created_by=created_by,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Use distributed lock for parent session if needed
        if parent_session_id:
            lock_resource = f"session:parent:{parent_session_id}"
            async with distributed_lock(lock_resource, timeout=10):
                # Verify parent exists
                parent = await self.session_repository.get_by_id(parent_session_id)
                if not parent:
                    raise SessionNotFoundError(f"Parent session not found: {parent_session_id}")
                
                # Add to repository
                created_session = await self.session_repository.add(session)
        else:
            # Add to repository
            created_session = await self.session_repository.add(session)
        
        # Publish event
        await self._publish_event(
            SessionCreated(
                session_id=created_session.id,
                title=created_session.title,
                session_type=created_session.session_type,
                created_by=created_session.created_by,
                timestamp=datetime.now(timezone.utc)
            )
        )
        
        self._logger.info(
            f"Session created: {created_session.id} "
            f"(type: {session_type}, priority: {priority})"
        )
        
        return created_session
    
    async def get_session(
        self,
        session_id: UUID,
        include_metrics: bool = False,
        include_checkpoints: bool = False
    ) -> Optional[SessionEntity]:
        """
        Get session by ID
        
        Args:
            session_id: Session ID
            include_metrics: Include execution metrics
            include_checkpoints: Include checkpoints
        
        Returns:
            SessionEntity or None if not found
        """
        if include_metrics and include_checkpoints:
            return await self.session_repository.get_full_session(session_id)
        elif include_metrics:
            return await self.session_repository.get_with_metrics(session_id)
        elif include_checkpoints:
            return await self.session_repository.get_with_checkpoints(session_id)
        else:
            return await self.session_repository.get_by_id(session_id)
    
    async def start_session(self, session_id: UUID) -> SessionEntity:
        """
        Start session execution
        
        Args:
            session_id: Session ID to start
        
        Returns:
            SessionEntity: Updated session
        
        Raises:
            SessionNotFoundError: If session not found
            InvalidSessionTransition: If session cannot be started
        """
        # Use distributed lock for session
        lock_resource = f"session:execution:{session_id}"
        async with distributed_lock(lock_resource, timeout=self.lock_timeout):
            # Get session
            session = await self.session_repository.get_by_id(session_id)
            if not session:
                raise SessionNotFoundError(f"Session not found: {session_id}")
            
            # Start execution
            try:
                session.start_execution()
            except InvalidSessionTransition as e:
                self._logger.error(f"Cannot start session {session_id}: {e}")
                raise
            
            # Update in repository
            updated_session = await self.session_repository.update(session)
            
            # Publish event
            await self._publish_event(
                SessionStatusChanged(
                    session_id=session_id,
                    old_status=SessionStatus.PENDING,
                    new_status=SessionStatus.RUNNING,
                    timestamp=datetime.now(timezone.utc)
                )
            )
            
            self._logger.info(f"Session started: {session_id}")
            
            return updated_session
    
    async def complete_session(
        self,
        session_id: UUID,
        result: Dict[str, Any],
        success_rate: float = 1.0,
        confidence_score: Optional[float] = None
    ) -> SessionEntity:
        """
        Complete session with results
        
        Args:
            session_id: Session ID to complete
            result: Execution results
            success_rate: Success rate (0.0 to 1.0)
            confidence_score: Confidence score (0.0 to 1.0)
        
        Returns:
            SessionEntity: Completed session
        """
        lock_resource = f"session:execution:{session_id}"
        async with distributed_lock(lock_resource, timeout=self.lock_timeout):
            # Get session with metrics
            session = await self.session_repository.get_with_metrics(session_id)
            if not session:
                raise SessionNotFoundError(f"Session not found: {session_id}")
            
            old_status = session.status
            
            # Complete session
            session.complete_with_result(result)
            
            # Update metrics
            session.metrics.success_rate = success_rate
            if confidence_score is not None:
                session.metrics.confidence_score = confidence_score
            
            # Update in repository
            updated_session = await self.session_repository.update(session)
            
            # Publish events
            await self._publish_event(
                SessionStatusChanged(
                    session_id=session_id,
                    old_status=old_status,
                    new_status=SessionStatus.COMPLETED,
                    timestamp=datetime.now(timezone.utc)
                )
            )
            
            await self._publish_event(
                SessionCompleted(
                    session_id=session_id,
                    result=result,
                    success_rate=success_rate,
                    execution_duration_seconds=session.metrics.execution_duration_seconds,
                    timestamp=datetime.now(timezone.utc)
                )
            )
            
            self._logger.info(
                f"Session completed: {session_id} "
                f"(success: {success_rate:.2%}, "
                f"duration: {session.metrics.execution_duration_seconds:.1f}s)"
            )
            
            return updated_session
    
    async def fail_session(
        self,
        session_id: UUID,
        error: Exception,
        error_context: Optional[Dict[str, Any]] = None,
        retryable: bool = True
    ) -> SessionEntity:
        """
        Mark session as failed
        
        Args:
            session_id: Session ID to fail
            error: Error that caused failure
            error_context: Additional error context
            retryable: Whether the failure is retryable
        
        Returns:
            SessionEntity: Failed session
        """
        lock_resource = f"session:execution:{session_id}"
        async with distributed_lock(lock_resource, timeout=self.lock_timeout):
            # Get session with metrics
            session = await self.session_repository.get_with_metrics(session_id)
            if not session:
                raise SessionNotFoundError(f"Session not found: {session_id}")
            
            old_status = session.status
            
            # Fail session
            session.fail_with_error(error, error_context)
            
            # Mark as retryable in metadata if applicable
            if retryable and session.metadata:
                session.metadata["retryable"] = True
                session.metadata["retry_count"] = session.metadata.get("retry_count", 0) + 1
            
            # Update in repository
            updated_session = await self.session_repository.update(session)
            
            # Publish events
            await self._publish_event(
                SessionStatusChanged(
                    session_id=session_id,
                    old_status=old_status,
                    new_status=SessionStatus.FAILED,
                    timestamp=datetime.now(timezone.utc)
                )
            )
            
            await self._publish_event(
                SessionFailed(
                    session_id=session_id,
                    error_type=error.__class__.__name__,
                    error_message=str(error),
                    error_context=error_context or {},
                    retryable=retryable,
                    timestamp=datetime.now(timezone.utc)
                )
            )
            
            self._logger.error(
                f"Session failed: {session_id} - {error.__class__.__name__}: {error}"
            )
            
            return updated_session
    
    async def add_checkpoint(
        self,
        session_id: UUID,
        checkpoint_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add checkpoint to session
        
        Args:
            session_id: Session ID
            checkpoint_data: Checkpoint data
            metadata: Checkpoint metadata
        
        Returns:
            Dict with checkpoint details
        """
        # Merge metadata
        full_checkpoint_data = checkpoint_data.copy()
        if metadata:
            full_checkpoint_data["_metadata"] = metadata
        
        # Add checkpoint via repository
        checkpoint = await self.session_repository.add_checkpoint(
            session_id,
            full_checkpoint_data
        )
        
        self._logger.debug(
            f"Checkpoint added to session {session_id}: "
            f"sequence {checkpoint['sequence']}"
        )
        
        return checkpoint
    
    async def retry_session(self, session_id: UUID) -> Optional[SessionEntity]:
        """
        Retry a failed session if recoverable
        
        Args:
            session_id: Session ID to retry
        
        Returns:
            SessionEntity if retried, None if not recoverable
        """
        # Get session with checkpoints
        session = await self.session_repository.get_with_checkpoints(session_id)
        if not session:
            return None
        
        # Check if session is recoverable
        if not session.is_recoverable():
            self._logger.warning(f"Session not recoverable: {session_id}")
            return None
        
        lock_resource = f"session:execution:{session_id}"
        async with distributed_lock(lock_resource, timeout=self.lock_timeout):
            # Reset session to PENDING status
            session.transition_to(SessionStatus.PENDING)
            
            # Update retry count in metrics
            session.metrics.increment_retry_count()
            
            # Update in repository
            updated_session = await self.session_repository.update(session)
            
            self._logger.info(
                f"Session retry scheduled: {session_id} "
                f"(retry count: {session.metrics.retry_count})"
            )
            
            return updated_session

    async def execute_session(
        self,
        session_id: UUID,
        additional_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute session handling both internal and external agents.
        
        Args:
            session_id: Session ID
            additional_prompt: Optional extra prompt
            
        Returns:
            Dict with execution result
        """
        # Get session
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(f"Session not found: {session_id}")
            
        # Identify agent
        agent_name = None
        if session.agent_config:
            # Assumes config is {agent_name: config} or similar
            # If default_agent key exists, might be different. 
            # Logic: keys() are usually agent names if not reserved.
            keys = [k for k in session.agent_config.keys() if k != "default_agent"]
            if keys:
                agent_name = keys[0]
            elif "default_agent" in session.agent_config:
                agent_name = session.agent_config["default_agent"]
        
        # Start session
        await self.start_session(session_id)
        
        try:
            execution_result = {}
            is_external = False
            
            # Resolve agent if repository available
            if self.agent_repository and agent_name:
                agent = await self.agent_repository.get_by_name(agent_name)
                if agent and agent.metadata.get("is_external"):
                    is_external = True
                    if not self.external_agent_adapter:
                        raise RuntimeError("External agent adapter not configured")
                    
                    # Prepare EAP payload
                    task_assignment = EAPTaskAssignment(
                        task_id=uuid4(),
                        session_id=session.id,
                        task_type="session_execution",
                        context=session.model_dump(mode='json'),
                        input_data=f"{session.initial_prompt}\n\n{additional_prompt or ''}",
                        requirements=session.tags
                    )
                    
                    # Dispatch to external agent
                    eap_result = await self.external_agent_adapter.send_task(
                        agent_id=str(agent.id),
                        endpoint_url=agent.metadata["endpoint_url"],
                        auth_token=agent.metadata["auth_token"],
                        task_assignment=task_assignment
                    )
                    
                    # Map EAP result to session result
                    execution_result = {
                        "success": eap_result.status == "completed",
                        "session_id": str(session_id),
                        "artifacts": [a.model_dump() for a in eap_result.artifacts],
                        "output": eap_result.output_data,
                        "metrics": {
                            "execution_time_ms": eap_result.execution_time_ms,
                            "tokens_used": eap_result.tokens_used,
                            "cost_usd": eap_result.cost_usd
                        }
                    }
                    
                    if eap_result.status == "failed":
                        raise RuntimeError(f"External agent failed: {eap_result.error_message}")

            # Fallback to internal OpenCode execution
            if not is_external:
                return await self.execute_with_opencode(session_id, additional_prompt)
            
            # Complete session for external execution
            await self.complete_session(
                session_id,
                execution_result,
                success_rate=1.0,
                confidence_score=0.9
            )
            
            return execution_result
            
        except Exception as e:
            await self.fail_session(
                session_id,
                e,
                error_context={"source": "agent_execution", "agent": agent_name},
                retryable=True
            )
            raise

    async def execute_with_opencode(
        self,
        session_id: UUID,
        additional_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute session using OpenCode API
        
        Requires OpenCode client to be configured
        
        Args:
            session_id: Session ID to execute
            additional_prompt: Additional prompt to append
        
        Returns:
            Dict with execution results
        """
        if not self.opencode_client:
            raise RuntimeError("OpenCode client not configured")
        
        # Get session
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        
        # Start session if not already running
        if session.status == SessionStatus.PENDING:
            await self.start_session(session_id)
        elif session.status != SessionStatus.RUNNING:
            raise InvalidSessionTransition(
                current_status=session.status,
                target_status=SessionStatus.RUNNING,
                session_id=session.id,
                reason="Session must be PENDING or RUNNING to execute"
            )
        
        try:
            # Prepare prompt
            prompt = session.initial_prompt
            if additional_prompt:
                prompt = f"{prompt}\n\n{additional_prompt}"
            
            # Execute with OpenCode
            result = await self.opencode_client.execute_session_task(session)
            
            # Extract relevant information
            execution_result = {
                "success": True,
                "session_id": str(session_id),
                "opencode_session_id": result.get("session_id"),
                "diff": result.get("diff", {}),
                "metrics": result.get("metrics", {}),
            }
            
            # Complete session
            await self.complete_session(
                session_id,
                execution_result,
                success_rate=1.0,
                confidence_score=0.9
            )
            
            return execution_result
            
        except Exception as e:
            # Fail session
            await self.fail_session(
                session_id,
                e,
                error_context={"source": "opencode_execution"},
                retryable=True
            )
            raise
    
    async def find_sessions(
        self,
        status: Optional[SessionStatus] = None,
        session_type: Optional[SessionType] = None,
        priority: Optional[SessionPriority] = None,
        created_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionEntity]:
        """
        Find sessions with various filters
        
        Args:
            status: Filter by status
            session_type: Filter by session type
            priority: Filter by priority
            created_by: Filter by creator
            tags: Filter by tags
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of matching sessions
        """
        # This would use repository's find method with appropriate filters
        # Simplified implementation for now
        all_sessions = await self.session_repository.get_all()
        
        filtered = []
        for session in all_sessions:
            if status and session.status != status:
                continue
            if session_type and session.session_type != session_type:
                continue
            if priority and session.priority != priority:
                continue
            if created_by and session.created_by != created_by:
                continue
            if tags and not all(tag in session.tags for tag in tags):
                continue
            
            filtered.append(session)
        
        # Apply pagination
        start = offset
        end = offset + limit
        return filtered[start:end]
    
    async def get_session_tree(self, root_session_id: UUID) -> Dict[str, Any]:
        """
        Get hierarchical session tree
        
        Args:
            root_session_id: Root session ID
        
        Returns:
            Hierarchical tree structure
        """
        return await self.session_repository.get_session_tree(root_session_id)
    
    async def monitor_sessions(self) -> Dict[str, Any]:
        """
        Monitor active and at-risk sessions
        
        Returns:
            Dict with monitoring information
        """
        # Get active sessions
        active_sessions = await self.session_repository.find_active_sessions()
        
        # Identify at-risk sessions (close to timeout)
        at_risk_sessions = []
        now = datetime.now(timezone.utc)
        
        for session in active_sessions:
            if session.status == SessionStatus.RUNNING and session.metrics.started_at:
                elapsed = (now - session.metrics.started_at).total_seconds()
                time_remaining = session.max_duration_seconds - elapsed
                
                if time_remaining < 300:  # 5 minutes
                    at_risk_sessions.append({
                        "session_id": str(session.id),
                        "title": session.title,
                        "elapsed_seconds": elapsed,
                        "time_remaining_seconds": time_remaining,
                        "health_score": session.calculate_health_score(),
                    })
        
        # Get statistics
        stats = await self.session_repository.get_session_stats()
        
        return {
            "active_sessions_count": len(active_sessions),
            "at_risk_sessions_count": len(at_risk_sessions),
            "at_risk_sessions": at_risk_sessions,
            "stats": stats,
            "timestamp": now.isoformat(),
        }
    
    async def cleanup_old_sessions(self, older_than_days: int = 30) -> Dict[str, int]:
        """
        Clean up old sessions
        
        Args:
            older_than_days: Age threshold in days
        
        Returns:
            Dict with cleanup statistics
        """
        self._logger.info(f"Starting cleanup of sessions older than {older_than_days} days")
        
        stats = await self.session_repository.cleanup_old_sessions(older_than_days)
        
        self._logger.info(
            f"Cleanup completed: {stats['sessions_cleaned']} sessions cleaned, "
            f"{stats['errors']} errors"
        )
        
        return stats
    
    def _register_event_handler(self, event_type: str, handler: callable) -> None:
        """Register event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def _publish_event(self, event: Any) -> None:
        """Publish event to registered handlers"""
        event_type = event.__class__.__name__
        
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    self._logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown service and release resources"""
        # In production, would also shutdown repositories, clients, etc.
        pass
