"""
TEST SESSION SERVICE
Comprehensive unit tests for SessionService business logic.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from src.industrial_orchestrator.application.services.session_service import SessionService
from src.industrial_orchestrator.domain.entities.session import (
    SessionEntity,
    SessionType,
    SessionPriority,
)
from src.industrial_orchestrator.domain.value_objects.session_status import SessionStatus
from src.industrial_orchestrator.domain.exceptions.session_exceptions import (
    InvalidSessionTransition,
    SessionNotFoundError,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_session_repo():
    """Create mock session repository."""
    repo = AsyncMock()
    repo.initialize = AsyncMock()
    repo.add = AsyncMock()
    repo.update = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_with_metrics = AsyncMock(return_value=None)
    repo.get_with_checkpoints = AsyncMock(return_value=None)
    repo.get_full_session = AsyncMock(return_value=None)
    repo.add_checkpoint = AsyncMock()
    repo.get_all = AsyncMock(return_value=[])
    repo.find_active_sessions = AsyncMock(return_value=[])
    repo.get_session_stats = AsyncMock(return_value={"total": 0})
    repo.get_session_tree = AsyncMock(return_value={})
    return repo


@pytest.fixture
def mock_opencode_client():
    """Create mock OpenCode client."""
    client = AsyncMock()
    client.initialize = AsyncMock()
    client.execute_session_task = AsyncMock(return_value={
        "session_id": "oc-123",
        "diff": {"files_changed": 2},
        "metrics": {"tokens": 1000},
    })
    return client


@pytest.fixture
def session_service(mock_session_repo, mock_opencode_client):
    """Create SessionService with mock dependencies."""
    return SessionService(
        session_repository=mock_session_repo,
        opencode_client=mock_opencode_client,
        lock_timeout=30
    )


@pytest.fixture
def sample_session():
    """Create a sample session entity."""
    return SessionEntity(
        tenant_id=uuid4(),
        title="IND-TEST-001: Sample Session",
        initial_prompt="Implement feature X",
        session_type=SessionType.EXECUTION,
        priority=SessionPriority.MEDIUM,
        created_by="test_user",
    )


# ============================================================================
# Test Session Creation
# ============================================================================

class TestSessionCreation:
    """Test session creation use cases."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, session_service, mock_session_repo):
        """Test successful session creation with all fields."""
        tenant_id = uuid4()
        # Arrange
        expected_session = SessionEntity(
            tenant_id=tenant_id,
            title="IND-TEST-001: New Feature",
            initial_prompt="Implement authentication",
            session_type=SessionType.EXECUTION,
            priority=SessionPriority.HIGH,
            created_by="dev_team",
        )
        mock_session_repo.add.return_value = expected_session
        
        # Act
        with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock', 
                   return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock())):
            with patch('src.industrial_orchestrator.application.services.session_service.get_current_tenant_id', return_value=tenant_id):
                result = await session_service.create_session(
                    title="IND-TEST-001: New Feature",
                    initial_prompt="Implement authentication",
                    session_type=SessionType.EXECUTION,
                    priority=SessionPriority.HIGH,
                    created_by="dev_team",
                    tags=["auth", "security"],
                    metadata={"sprint": 5},
                )
        
        # Assert
        assert result is not None
        mock_session_repo.add.assert_called_once()
        
        # Verify the session entity passed to add()
        added_session = mock_session_repo.add.call_args[0][0]
        assert added_session.title == "IND-TEST-001: New Feature"
        assert added_session.initial_prompt == "Implement authentication"
        assert added_session.session_type == SessionType.EXECUTION
        assert added_session.priority == SessionPriority.HIGH

    @pytest.mark.asyncio
    async def test_create_session_with_defaults(self, session_service, mock_session_repo):
        """Test session creation with minimal required fields."""
        tenant_id = uuid4()
        expected_session = SessionEntity(
            tenant_id=tenant_id,
            title="IND-MIN-001: Minimal Session",
            initial_prompt="Simple task",
        )
        mock_session_repo.add.return_value = expected_session
        
        with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock',
                   return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock())):
            with patch('src.industrial_orchestrator.application.services.session_service.get_current_tenant_id', return_value=tenant_id):
                result = await session_service.create_session(
                    title="IND-MIN-001: Minimal Session",
                    initial_prompt="Simple task",
                )
        
        assert result is not None
        added_session = mock_session_repo.add.call_args[0][0]
        assert added_session.session_type == SessionType.EXECUTION  # Default
        assert added_session.priority == SessionPriority.MEDIUM  # Default

    @pytest.mark.asyncio
    async def test_create_session_empty_title_fails(self, session_service):
        """Test that empty title is rejected."""
        with pytest.raises(ValueError, match="title is required"):
            await session_service.create_session(
                title="",
                initial_prompt="Some task",
            )

    @pytest.mark.asyncio
    async def test_create_session_empty_prompt_fails(self, session_service):
        """Test that empty prompt is rejected."""
        with pytest.raises(ValueError, match="prompt is required"):
            await session_service.create_session(
                title="IND-TEST-001: Valid Title",
                initial_prompt="",
            )

    @pytest.mark.asyncio
    async def test_create_session_whitespace_title_fails(self, session_service):
        """Test that whitespace-only title is rejected."""
        with pytest.raises(ValueError, match="title is required"):
            await session_service.create_session(
                title="   ",
                initial_prompt="Some task",
            )

    @pytest.mark.asyncio
    async def test_create_session_with_parent(self, session_service, mock_session_repo, sample_session):
        """Test session creation with parent session."""
        parent_id = uuid4()
        parent_session = sample_session
        parent_session.id = parent_id
        tenant_id = sample_session.tenant_id
    
        mock_session_repo.get_by_id.return_value = parent_session
        mock_session_repo.add.return_value = sample_session
    
        with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock',
                   return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock())):
            with patch('src.industrial_orchestrator.application.services.session_service.get_current_tenant_id', return_value=tenant_id):
                result = await session_service.create_session(
                    title="IND-CHILD-001: Child Session",
                    initial_prompt="Sub-task",
                    parent_session_id=parent_id,
                )
        assert result is not None
        mock_session_repo.get_by_id.assert_called_once_with(parent_id)

    @pytest.mark.asyncio
    async def test_create_session_nonexistent_parent_fails(self, session_service, mock_session_repo):
        """Test that creation fails if parent doesn't exist."""
        parent_id = uuid4()
        tenant_id = uuid4()
        mock_session_repo.get_by_id.return_value = None  # Parent not found
    
        lock_mock = AsyncMock()
        lock_mock.__aenter__.return_value = AsyncMock()
        lock_mock.__aexit__.return_value = None
    
        with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock', return_value=lock_mock):
            with patch('src.industrial_orchestrator.application.services.session_service.get_current_tenant_id', return_value=tenant_id):
                with pytest.raises(SessionNotFoundError):
                    await session_service.create_session(
                        title="IND-ORPHAN-001: Orphan",
                        initial_prompt="Orphan task",
                        parent_session_id=parent_id,
                    )


# ============================================================================
# Test Session Lifecycle
# ============================================================================

class TestSessionLifecycle:
    """Test session state transitions."""

    @pytest.mark.asyncio
    async def test_start_session_success(self, session_service, mock_session_repo, sample_session):
        """Test successful session start."""
        session_id = sample_session.id
        sample_session.status = SessionStatus.PENDING
        mock_session_repo.get_by_id.return_value = sample_session
        mock_session_repo.update.return_value = sample_session
        
        with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock',
                   return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock())):
            result = await session_service.start_session(session_id)
        
        assert result is not None
        mock_session_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_nonexistent_session_fails(self, session_service, mock_session_repo):
        """Test that starting nonexistent session raises error."""
        session_id = uuid4()
        mock_session_repo.get_by_id.return_value = None
        mock_session_repo.get_with_metrics.return_value = None
    
        lock_mock = AsyncMock()
        lock_mock.__aenter__.return_value = AsyncMock()
        lock_mock.__aexit__.return_value = False
    
        with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock',
                   return_value=lock_mock):
            with pytest.raises(SessionNotFoundError):
                await session_service.start_session(session_id)

    @pytest.mark.asyncio
    async def test_complete_session_success(self, session_service, mock_session_repo, sample_session):
        """Test successful session completion."""
        session_id = sample_session.id
        sample_session.status = SessionStatus.PENDING
        sample_session.start_execution()  # PENDING -> RUNNING
        
        mock_session_repo.get_with_metrics.return_value = sample_session
        mock_session_repo.update.return_value = sample_session
        
        result_data = {"output": "Task completed", "files_changed": 5}
        
        with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock',
                   return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock())):
            result = await session_service.complete_session(
                session_id,
                result=result_data,
                success_rate=0.95,
                confidence_score=0.88,
            )
        
        assert result is not None
        mock_session_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_fail_session_success(self, session_service, mock_session_repo, sample_session):
        """Test session failure handling."""
        session_id = sample_session.id
        sample_session.status = SessionStatus.RUNNING
        
        mock_session_repo.get_with_metrics.return_value = sample_session
        mock_session_repo.update.return_value = sample_session
        
        error = RuntimeError("Connection timeout")
        
        with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock',
                   return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock())):
            result = await session_service.fail_session(
                session_id,
                error=error,
                error_context={"source": "api"},
                retryable=True,
            )
        
        assert result is not None
        mock_session_repo.update.assert_called_once()


# ============================================================================
# Test Checkpointing
# ============================================================================

class TestCheckpointing:
    """Test session checkpoint operations."""

    @pytest.mark.asyncio
    async def test_add_checkpoint_success(self, session_service, mock_session_repo):
        """Test adding checkpoint to session."""
        session_id = uuid4()
        checkpoint_data = {"state": "step_3_complete", "progress": 0.75}
        
        mock_session_repo.add_checkpoint.return_value = {
            "sequence": 1,
            "data": checkpoint_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        result = await session_service.add_checkpoint(
            session_id,
            checkpoint_data=checkpoint_data,
            metadata={"phase": "execution"},
        )
        
        assert result is not None
        assert "sequence" in result
        mock_session_repo.add_checkpoint.assert_called_once()


# ============================================================================
# Test Session Retry
# ============================================================================

class TestSessionRetry:
    """Test session retry logic."""

    @pytest.mark.asyncio
    async def test_retry_recoverable_session(self, mock_session_repo, mock_opencode_client, sample_session):
        """Test retrying a recoverable session."""
        # Ensure we use a fresh service instance
        local_service = SessionService(session_repository=mock_session_repo, opencode_client=mock_opencode_client)
        session_id = sample_session.id
        sample_session.status = SessionStatus.FAILED
        # Force recoverability: must have status in set AND checkpoints AND retry count < 3
        sample_session.checkpoints = [{"sequence": 1, "data": {}, "timestamp": datetime.now(timezone.utc).isoformat()}]
        sample_session.metrics.retry_count = 0
    
        # Setup mocks
        mock_session_repo.get_with_checkpoints.return_value = sample_session
        mock_session_repo.update.return_value = sample_session
    
        lock_mock = AsyncMock()
        lock_mock.__aenter__.return_value = AsyncMock()
        lock_mock.__aexit__.return_value = False
    
        # Act
        with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock',
                   return_value=lock_mock):
            result = await local_service.retry_session(session_id)
        
        assert result is not None
        assert sample_session.status == SessionStatus.PENDING

    @pytest.mark.asyncio
    async def test_retry_nonrecoverable_session_returns_none(self, session_service, mock_session_repo, sample_session):
        """Test that non-recoverable session returns None."""
        session_id = sample_session.id
        sample_session.status = SessionStatus.FAILED
        # No checkpoints -> non-recoverable
        sample_session.checkpoints = []
        mock_session_repo.get_with_checkpoints.return_value = sample_session
        
        result = await session_service.retry_session(session_id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_retry_nonexistent_session_returns_none(self, session_service, mock_session_repo):
        """Test that retrying nonexistent session returns None."""
        session_id = uuid4()
        mock_session_repo.get_with_checkpoints.return_value = None
        
        result = await session_service.retry_session(session_id)
        
        assert result is None


# ============================================================================
# Test OpenCode Execution
# ============================================================================

class TestOpenCodeExecution:
    """Test OpenCode integration."""

    @pytest.mark.asyncio
    async def test_execute_without_client_raises_error(self, mock_session_repo):
        """Test that execute without client raises RuntimeError."""
        service = SessionService(
            session_repository=mock_session_repo,
            opencode_client=None,  # No client
        )
        
        with pytest.raises(RuntimeError, match="not configured"):
            await service.execute_with_opencode(uuid4())

    @pytest.mark.asyncio
    async def test_execute_nonexistent_session_fails(self, session_service, mock_session_repo):
        """Test that executing nonexistent session raises error."""
        session_id = uuid4()
        mock_session_repo.get_by_id.return_value = None
        
        with pytest.raises(SessionNotFoundError):
            await session_service.execute_with_opencode(session_id)


# ============================================================================
# Test Session Queries
# ============================================================================

class TestSessionQueries:
    """Test session query operations."""

    @pytest.mark.asyncio
    async def test_get_session_by_id(self, session_service, mock_session_repo, sample_session):
        """Test retrieving session by ID."""
        session_id = sample_session.id
        mock_session_repo.get_by_id.return_value = sample_session
        
        result = await session_service.get_session(session_id)
        
        assert result is not None
        assert result.id == session_id

    @pytest.mark.asyncio
    async def test_get_session_with_metrics(self, session_service, mock_session_repo, sample_session):
        """Test retrieving session with metrics."""
        session_id = sample_session.id
        mock_session_repo.get_with_metrics.return_value = sample_session
        
        result = await session_service.get_session(session_id, include_metrics=True)
        
        mock_session_repo.get_with_metrics.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_get_session_with_checkpoints(self, session_service, mock_session_repo, sample_session):
        """Test retrieving session with checkpoints."""
        session_id = sample_session.id
        mock_session_repo.get_with_checkpoints.return_value = sample_session
        
        result = await session_service.get_session(session_id, include_checkpoints=True)
        
        mock_session_repo.get_with_checkpoints.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_find_sessions_with_filters(self, session_service, mock_session_repo, sample_session):
        """Test finding sessions with filters."""
        sample_session.status = SessionStatus.PENDING
        sample_session.session_type = SessionType.EXECUTION
        mock_session_repo.get_all.return_value = [sample_session]
        
        result = await session_service.find_sessions(
            status=SessionStatus.PENDING,
            session_type=SessionType.EXECUTION,
        )
        
        assert len(result) == 1
        assert result[0].status == SessionStatus.PENDING

    @pytest.mark.asyncio
    async def test_monitor_sessions(self, session_service, mock_session_repo):
        """Test session monitoring."""
        mock_session_repo.find_active_sessions.return_value = []
        mock_session_repo.get_session_stats.return_value = {"total": 5}
        
        result = await session_service.monitor_sessions()
        
        assert "active_sessions_count" in result
        assert "stats" in result
        assert result["active_sessions_count"] == 0

    @pytest.mark.asyncio
    async def test_get_session_tree(self, session_service, mock_session_repo):
        """Test getting session hierarchy tree."""
        root_id = uuid4()
        expected_tree = {
            "id": str(root_id),
            "title": "Root",
            "children": [],
        }
        mock_session_repo.get_session_tree.return_value = expected_tree
        
        result = await session_service.get_session_tree(root_id)
        
        assert result == expected_tree
        mock_session_repo.get_session_tree.assert_called_once_with(root_id)


# ============================================================================
# Test Event Publishing
# ============================================================================

class TestEventPublishing:
    """Test event handling and publishing."""

    @pytest.mark.asyncio
    async def test_event_handler_registration(self, session_service):
        """Test that event handlers can be registered."""
        handler = MagicMock()
        session_service._register_event_handler("SessionCreated", handler)
        
        assert "SessionCreated" in session_service._event_handlers
        assert handler in session_service._event_handlers["SessionCreated"]

    @pytest.mark.asyncio
    async def test_event_publishing_calls_handlers(self, session_service):
        """Test that publishing events calls registered handlers."""
        handler = MagicMock()
        session_service._register_event_handler("TestEvent", handler)
        
        class TestEvent:
            pass
        
        await session_service._publish_event(TestEvent())
        
        handler.assert_called_once()