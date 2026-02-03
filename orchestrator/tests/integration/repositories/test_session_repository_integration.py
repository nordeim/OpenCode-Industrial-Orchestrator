"""
INDUSTRIAL SESSION REPOSITORY INTEGRATION TESTS
Test session repository with real database connection.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from uuid import uuid4

from src.industrial_orchestrator.domain.entities.session import (
    SessionEntity, SessionType, SessionPriority
)
from src.industrial_orchestrator.domain.value_objects.session_status import SessionStatus
from src.industrial_orchestrator.infrastructure.repositories.session_repository import (
    SessionRepository, QueryOptions, FilterOperator, FilterCondition
)
from src.industrial_orchestrator.infrastructure.config.database import (
    get_database_manager, shutdown_database
)
from src.industrial_orchestrator.infrastructure.config.redis import (
    get_redis_client, shutdown_redis
)
from tests.unit.domain.factories.session_factory import (
    SessionEntityFactory, create_session_batch
)


class TestSessionRepositoryIntegration:
    """Integration tests for SessionRepository"""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Initialize dependencies
        db_manager = await get_database_manager()
        redis_client = await get_redis_client()
        
        # Clean test database
        async with db_manager.get_session() as session:
            # Clear test data
            await session.execute("DELETE FROM session_checkpoints")
            await session.execute("DELETE FROM session_metrics")
            await session.execute("DELETE FROM sessions")
            await session.commit()
        
        # Clear Redis cache
        await redis_client._client.flushdb()
        
        yield
        
        # Cleanup
        await shutdown_database()
        await shutdown_redis()
    
    @pytest.fixture
    async def session_repository(self):
        """Create session repository for testing"""
        repository = SessionRepository()
        await repository.initialize()
        return repository
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_add_and_get_session(self, session_repository):
        """Test adding and retrieving a session"""
        # Create test session
        session_entity = SessionEntityFactory()
        
        # Add to repository
        added_session = await session_repository.add(session_entity)
        
        assert added_session.id is not None
        assert added_session.title == session_entity.title
        assert added_session.status == SessionStatus.PENDING
        
        # Retrieve from repository
        retrieved_session = await session_repository.get_by_id(added_session.id)
        
        assert retrieved_session is not None
        assert retrieved_session.id == added_session.id
        assert retrieved_session.title == added_session.title
        assert retrieved_session.status == added_session.status
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_session(self, session_repository):
        """Test updating a session"""
        # Create and add session
        session_entity = SessionEntityFactory()
        added_session = await session_repository.add(session_entity)
        
        # Update session
        added_session.title = "UPDATED INDUSTRIAL SESSION"
        added_session.description = "Updated description"
        added_session.transition_to(SessionStatus.RUNNING)
        
        updated_session = await session_repository.update(added_session)
        
        assert updated_session.title == "UPDATED INDUSTRIAL SESSION"
        assert updated_session.description == "Updated description"
        assert updated_session.status == SessionStatus.RUNNING
        
        # Verify update persisted
        retrieved_session = await session_repository.get_by_id(added_session.id)
        assert retrieved_session.title == "UPDATED INDUSTRIAL SESSION"
        assert retrieved_session.status == SessionStatus.RUNNING
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_session(self, session_repository):
        """Test soft deleting a session"""
        # Create and add session
        session_entity = SessionEntityFactory()
        added_session = await session_repository.add(session_entity)
        
        # Soft delete
        deleted = await session_repository.delete(added_session.id)
        assert deleted is True
        
        # Should not find with default options
        retrieved = await session_repository.get_by_id(added_session.id)
        assert retrieved is None
        
        # Should find with include_deleted option
        options = QueryOptions(include_deleted=True)
        retrieved_deleted = await session_repository.get_by_id(added_session.id, options)
        assert retrieved_deleted is not None
        assert retrieved_deleted.id == added_session.id
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_find_by_status(self, session_repository):
        """Test finding sessions by status"""
        # Create sessions with different statuses
        pending_session = SessionEntityFactory(status=SessionStatus.PENDING)
        running_session = SessionEntityFactory(status=SessionStatus.RUNNING)
        completed_session = SessionEntityFactory(status=SessionStatus.COMPLETED)
        
        await session_repository.add(pending_session)
        await session_repository.add(running_session)
        await session_repository.add(completed_session)
        
        # Find pending sessions
        pending_sessions = await session_repository.find_by_status(SessionStatus.PENDING)
        assert len(pending_sessions) == 1
        assert pending_sessions[0].status == SessionStatus.PENDING
        
        # Find running sessions
        running_sessions = await session_repository.find_by_status(SessionStatus.RUNNING)
        assert len(running_sessions) == 1
        assert running_sessions[0].status == SessionStatus.RUNNING
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_find_active_sessions(self, session_repository):
        """Test finding active sessions"""
        # Create mix of active and terminal sessions
        pending_session = SessionEntityFactory(status=SessionStatus.PENDING)
        running_session = SessionEntityFactory(status=SessionStatus.RUNNING)
        completed_session = SessionEntityFactory(status=SessionStatus.COMPLETED)
        failed_session = SessionEntityFactory(status=SessionStatus.FAILED)
        
        await session_repository.add(pending_session)
        await session_repository.add(running_session)
        await session_repository.add(completed_session)
        await session_repository.add(failed_session)
        
        # Find active sessions
        active_sessions = await session_repository.find_active_sessions()
        
        assert len(active_sessions) == 2
        statuses = {s.status for s in active_sessions}
        assert SessionStatus.PENDING in statuses
        assert SessionStatus.RUNNING in statuses
        assert SessionStatus.COMPLETED not in statuses
        assert SessionStatus.FAILED not in statuses
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pagination(self, session_repository):
        """Test pagination functionality"""
        # Create multiple sessions
        sessions = create_session_batch(25)
        
        for session in sessions:
            await session_repository.add(session)
        
        # Test pagination
        page1 = await session_repository.paginate(page=1, page_size=10)
        page2 = await session_repository.paginate(page=2, page_size=10)
        page3 = await session_repository.paginate(page=3, page_size=10)
        
        assert page1.total_count == 25
        assert page1.page == 1
        assert page1.page_size == 10
        assert page1.total_pages == 3
        assert len(page1.items) == 10
        
        assert page2.page == 2
        assert len(page2.items) == 10
        
        assert page3.page == 3
        assert len(page3.items) == 5  # Last page has 5 items
        
        assert page1.has_next is True
        assert page1.has_previous is False
        assert page3.has_next is False
        assert page3.has_previous is True
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complex_filters(self, session_repository):
        """Test complex filtering with multiple conditions"""
        # Create sessions with different priorities and types
        high_priority_planning = SessionEntityFactory(
            priority=SessionPriority.HIGH,
            session_type=SessionType.PLANNING
        )
        medium_priority_execution = SessionEntityFactory(
            priority=SessionPriority.MEDIUM,
            session_type=SessionType.EXECUTION
        )
        low_priority_review = SessionEntityFactory(
            priority=SessionPriority.LOW,
            session_type=SessionType.REVIEW
        )
        
        await session_repository.add(high_priority_planning)
        await session_repository.add(medium_priority_execution)
        await session_repository.add(low_priority_review)
        
        # Filter by priority HIGH and type PLANNING
        filters = [
            FilterCondition(
                field="priority",
                operator=FilterOperator.EQUALS,
                value=SessionPriority.HIGH.value
            ),
            FilterCondition(
                field="session_type",
                operator=FilterOperator.EQUALS,
                value=SessionType.PLANNING.value
            )
        ]
        
        options = QueryOptions(filters=filters)
        results = await session_repository.find(options)
        
        assert len(results) == 1
        assert results[0].priority == SessionPriority.HIGH
        assert results[0].session_type == SessionType.PLANNING
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_with_metrics(self, session_repository):
        """Test getting session with eager-loaded metrics"""
        # Create session with metrics
        session_entity = SessionEntityFactory()
        session_entity.metrics.start_timing()
        session_entity.metrics.complete_timing()
        session_entity.metrics.success_rate = 0.95
        
        added_session = await session_repository.add(session_entity)
        
        # Get with metrics
        session_with_metrics = await session_repository.get_with_metrics(added_session.id)
        
        assert session_with_metrics is not None
        assert session_with_metrics.metrics is not None
        assert session_with_metrics.metrics.success_rate == 0.95
        assert session_with_metrics.metrics.started_at is not None
        assert session_with_metrics.metrics.completed_at is not None
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_add_checkpoint(self, session_repository):
        """Test adding checkpoint to session"""
        # Create and add session
        session_entity = SessionEntityFactory()
        added_session = await session_repository.add(session_entity)
        
        # Add checkpoint
        checkpoint_data = {
            "progress": 0.5,
            "files": ["main.py", "utils.py"],
            "status": "processing"
        }
        
        checkpoint = await session_repository.add_checkpoint(
            added_session.id,
            checkpoint_data
        )
        
        assert checkpoint["sequence"] == 1
        assert checkpoint["data"] == checkpoint_data
        
        # Get session with checkpoints
        session_with_checkpoints = await session_repository.get_with_checkpoints(added_session.id)
        
        assert session_with_checkpoints is not None
        assert len(session_with_checkpoints.checkpoints) == 1
        assert session_with_checkpoints.checkpoints[0]["data"] == checkpoint_data
        assert session_with_checkpoints.checkpoints[0]["sequence"] == 1
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_status(self, session_repository):
        """Test updating session status"""
        # Create and add session
        session_entity = SessionEntityFactory(status=SessionStatus.PENDING)
        added_session = await session_repository.add(session_entity)
        
        # Update status to RUNNING
        updated = await session_repository.update_status(
            added_session.id,
            SessionStatus.RUNNING
        )
        
        assert updated is True
        
        # Verify status update
        updated_session = await session_repository.get_by_id(added_session.id)
        assert updated_session.status == SessionStatus.RUNNING
        
        # Verify metrics were updated
        session_with_metrics = await session_repository.get_with_metrics(added_session.id)
        assert session_with_metrics.metrics.started_at is not None
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_session_stats(self, session_repository):
        """Test getting session statistics"""
        # Create sessions with different statuses
        sessions = create_session_batch(10, {
            SessionStatus.PENDING: 0.3,
            SessionStatus.RUNNING: 0.3,
            SessionStatus.COMPLETED: 0.3,
            SessionStatus.FAILED: 0.1,
        })
        
        for session in sessions:
            await session_repository.add(session)
        
        # Get stats
        stats = await session_repository.get_session_stats()
        
        assert "status_distribution" in stats
        assert "type_distribution" in stats
        assert "priority_distribution" in stats
        assert "duration_stats" in stats
        
        # Verify status distribution sums to 100% (approximately)
        total_percentage = sum(s["percentage"] for s in stats["status_distribution"])
        assert abs(total_percentage - 100.0) < 0.01  # Allow small floating point error
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bulk_operations(self, session_repository):
        """Test bulk insert and update operations"""
        # Create multiple sessions
        sessions = create_session_batch(5)
        
        # Bulk insert
        inserted_sessions = await session_repository.bulk_insert(sessions)
        
        assert len(inserted_sessions) == 5
        for session in inserted_sessions:
            assert session.id is not None
        
        # Update all sessions
        for session in inserted_sessions:
            session.title = f"UPDATED: {session.title}"
        
        updated_sessions = await session_repository.bulk_update(inserted_sessions)
        
        assert len(updated_sessions) == 5
        for session in updated_sessions:
            assert session.title.startswith("UPDATED:")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_optimistic_locking(self, session_repository):
        """Test optimistic locking conflict detection"""
        # Create and add session
        session_entity = SessionEntityFactory()
        added_session = await session_repository.add(session_entity)
        
        # Simulate concurrent modification
        session1 = await session_repository.get_by_id(added_session.id)
        session2 = await session_repository.get_by_id(added_session.id)
        
        # Modify and update first session
        session1.title = "First Update"
        await session_repository.update(session1)
        
        # Try to update second session (should fail with optimistic lock error)
        session2.title = "Second Update"
        
        with pytest.raises(Exception) as exc_info:
            await session_repository.update(session2)
        
        # Should be an optimistic lock error
        assert "optimistic lock" in str(exc_info.value).lower() or \
               "version" in str(exc_info.value).lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, session_repository):
        """Test cache invalidation on updates"""
        # Create and add session
        session_entity = SessionEntityFactory()
        added_session = await session_repository.add(session_entity)
        
        # Get session (should cache)
        session1 = await session_repository.get_by_id(added_session.id)
        assert session1 is not None
        
        # Update session (should invalidate cache)
        session1.title = "Updated Title"
        await session_repository.update(session1)
        
        # Get session again (should get fresh from database)
        session2 = await session_repository.get_by_id(added_session.id)
        assert session2.title == "Updated Title"
