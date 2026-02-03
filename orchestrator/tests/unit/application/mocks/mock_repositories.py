"""
MOCK REPOSITORY IMPLEMENTATIONS
In-memory implementations of repository ports for unit testing.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from src.industrial_orchestrator.application.ports.repository_ports import (
    SessionRepositoryPort,
    AgentRepositoryPort,
    ContextRepositoryPort,
)
from src.industrial_orchestrator.domain.entities.session import SessionEntity
from src.industrial_orchestrator.domain.entities.context import ContextEntity, ContextScope
from src.industrial_orchestrator.domain.value_objects.session_status import SessionStatus


class MockSessionRepository(SessionRepositoryPort):
    """In-memory session repository for testing."""

    def __init__(self):
        self._sessions: Dict[UUID, SessionEntity] = {}
        self._checkpoints: Dict[UUID, List[Dict[str, Any]]] = {}

    def reset(self):
        """Clear all stored data."""
        self._sessions.clear()
        self._checkpoints.clear()

    def get_by_id(
        self,
        session_id: UUID,
        include_metrics: bool = False,
        include_checkpoints: bool = False
    ) -> Optional[SessionEntity]:
        """Get session by ID."""
        session = self._sessions.get(session_id)
        if session and include_checkpoints:
            session.checkpoints = self._checkpoints.get(session_id, [])
        return session

    def save(self, session: SessionEntity) -> SessionEntity:
        """Save session to in-memory store."""
        session.updated_at = datetime.now(timezone.utc)
        self._sessions[session.id] = session
        return session

    def delete(self, session_id: UUID) -> bool:
        """Delete session from store."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def find_by_status(
        self,
        status: SessionStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionEntity]:
        """Find sessions by status."""
        matching = [s for s in self._sessions.values() if s.status == status]
        return matching[offset:offset + limit]

    def find_active_sessions(self) -> List[SessionEntity]:
        """Find all non-terminal sessions."""
        terminal_statuses = {SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED}
        return [s for s in self._sessions.values() if s.status not in terminal_statuses]

    def find_by_parent(self, parent_id: UUID) -> List[SessionEntity]:
        """Find child sessions."""
        return [s for s in self._sessions.values() if s.parent_session_id == parent_id]

    def add_checkpoint(
        self,
        session_id: UUID,
        checkpoint_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add checkpoint to session."""
        if session_id not in self._checkpoints:
            self._checkpoints[session_id] = []
        
        checkpoint = {
            "sequence": len(self._checkpoints[session_id]) + 1,
            "data": checkpoint_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._checkpoints[session_id].append(checkpoint)
        return checkpoint

    def get_session_tree(
        self,
        root_session_id: UUID,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """Get hierarchical session tree."""
        root = self.get_by_id(root_session_id)
        if not root:
            return {}
        
        def build_tree(session: SessionEntity, depth: int) -> Dict[str, Any]:
            result = {
                "id": str(session.id),
                "title": session.title,
                "status": session.status.value,
                "children": [],
            }
            if depth < max_depth:
                children = self.find_by_parent(session.id)
                result["children"] = [build_tree(c, depth + 1) for c in children]
            return result
        
        return build_tree(root, 0)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics."""
        stats = {
            "total": len(self._sessions),
            "by_status": {},
        }
        for session in self._sessions.values():
            status_name = session.status.value
            stats["by_status"][status_name] = stats["by_status"].get(status_name, 0) + 1
        return stats

    def bulk_update_status(
        self,
        session_ids: List[UUID],
        new_status: SessionStatus
    ) -> int:
        """Bulk update session statuses."""
        count = 0
        for sid in session_ids:
            if sid in self._sessions:
                self._sessions[sid].status = new_status
                count += 1
        return count


class MockAgentRepository(AgentRepositoryPort):
    """In-memory agent repository for testing."""

    def __init__(self):
        self._agents: Dict[UUID, Any] = {}
        self._heartbeats: Dict[UUID, datetime] = {}

    def reset(self):
        """Clear all stored data."""
        self._agents.clear()
        self._heartbeats.clear()

    def register(self, agent: Any) -> Any:
        """Register agent."""
        self._agents[agent.id] = agent
        self._heartbeats[agent.id] = datetime.now(timezone.utc)
        return agent

    def deregister(self, agent_id: UUID) -> bool:
        """Deregister agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            self._heartbeats.pop(agent_id, None)
            return True
        return False

    def get_by_id(self, agent_id: UUID) -> Optional[Any]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def find_by_capabilities(
        self,
        required_capabilities: List[Any],
        available_only: bool = True
    ) -> List[Any]:
        """Find agents with capabilities."""
        matching = []
        for agent in self._agents.values():
            agent_caps = set(agent.capabilities) if hasattr(agent, 'capabilities') else set()
            required_caps = set(required_capabilities)
            if required_caps.issubset(agent_caps):
                matching.append(agent)
        return matching

    def find_available(self) -> List[Any]:
        """Find available agents."""
        return [a for a in self._agents.values() 
                if getattr(a, 'status', 'AVAILABLE') == 'AVAILABLE']

    def update_heartbeat(self, agent_id: UUID) -> bool:
        """Update agent heartbeat."""
        if agent_id in self._agents:
            self._heartbeats[agent_id] = datetime.now(timezone.utc)
            return True
        return False

    def update_performance_metrics(
        self,
        agent_id: UUID,
        metrics: Dict[str, Any]
    ) -> bool:
        """Update agent performance metrics."""
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            if hasattr(agent, 'performance_metrics'):
                agent.performance_metrics.update(metrics)
            return True
        return False

    def cleanup_stale_agents(self, max_age_seconds: int = 300) -> int:
        """Cleanup stale agents."""
        now = datetime.now(timezone.utc)
        stale = []
        for agent_id, last_heartbeat in self._heartbeats.items():
            age = (now - last_heartbeat).total_seconds()
            if age > max_age_seconds:
                stale.append(agent_id)
        
        for agent_id in stale:
            self.deregister(agent_id)
        
        return len(stale)

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get aggregate agent statistics."""
        return {
            "total": len(self._agents),
            "available": len(self.find_available()),
        }


class MockContextRepository(ContextRepositoryPort):
    """In-memory context repository for testing."""

    def __init__(self):
        self._contexts: Dict[UUID, ContextEntity] = {}

    def reset(self):
        """Clear all stored data."""
        self._contexts.clear()

    def get_by_id(self, context_id: UUID) -> Optional[ContextEntity]:
        """Get context by ID."""
        return self._contexts.get(context_id)

    def save(self, context: ContextEntity) -> ContextEntity:
        """Save context."""
        context.updated_at = datetime.now(timezone.utc)
        self._contexts[context.id] = context
        return context

    def delete(self, context_id: UUID) -> bool:
        """Delete context."""
        if context_id in self._contexts:
            del self._contexts[context_id]
            return True
        return False

    def find_by_session(self, session_id: UUID) -> List[ContextEntity]:
        """Find contexts for session."""
        return [c for c in self._contexts.values() if c.session_id == session_id]

    def find_by_agent(self, agent_id: UUID) -> List[ContextEntity]:
        """Find contexts for agent."""
        return [c for c in self._contexts.values() if c.agent_id == agent_id]

    def find_by_scope(self, scope: ContextScope) -> List[ContextEntity]:
        """Find contexts by scope."""
        return [c for c in self._contexts.values() if c.scope == scope]

    def find_global_contexts(self) -> List[ContextEntity]:
        """Find all global contexts."""
        return self.find_by_scope(ContextScope.GLOBAL)
