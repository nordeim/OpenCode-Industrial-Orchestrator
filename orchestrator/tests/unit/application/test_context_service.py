"""
TEST CONTEXT SERVICE
Comprehensive unit tests for ContextService business logic.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, UUID

from src.industrial_orchestrator.application.services.context_service import ContextService
from src.industrial_orchestrator.domain.entities.context import (
    ContextEntity,
    ContextScope,
    MergeStrategy,
)
from src.industrial_orchestrator.domain.exceptions.context_exceptions import (
    ContextNotFoundError,
    ContextScopeMismatchError,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_context_repo():
    """Create mock context repository."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.save = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    repo.find_by_session = AsyncMock(return_value=[])
    repo.find_by_agent = AsyncMock(return_value=[])
    repo.find_by_scope = AsyncMock(return_value=[])
    repo.find_global_contexts = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def context_service(mock_context_repo):
    """Create ContextService with mock dependencies."""
    return ContextService(
        context_repository=mock_context_repo,
    )


@pytest.fixture
def sample_session_context():
    """Create sample session-scoped context."""
    return ContextEntity(
        session_id=uuid4(),
        scope=ContextScope.SESSION,
        data={"project": "test", "config": {"debug": True}},
        created_by="test_user",
    )


@pytest.fixture
def sample_agent_context():
    """Create sample agent-scoped context."""
    return ContextEntity(
        session_id=uuid4(),
        agent_id=uuid4(),
        scope=ContextScope.AGENT,
        data={"agent_state": "active", "preferences": {}},
        created_by="agent_system",
    )


@pytest.fixture
def sample_global_context():
    """Create sample global-scoped context."""
    return ContextEntity(
        scope=ContextScope.GLOBAL,
        data={"shared_config": "value", "system_wide": True},
        created_by="admin",
    )


# ============================================================================
# Test Context Creation
# ============================================================================

class TestContextCreation:
    """Test context creation use cases."""

    @pytest.mark.asyncio
    async def test_create_session_context(self, context_service, mock_context_repo):
        """Test creating session-scoped context."""
        session_id = uuid4()
        
        mock_context_repo.save.return_value = ContextEntity(
            session_id=session_id,
            scope=ContextScope.SESSION,
            data={"initial": "data"},
        )
        
        result = await context_service.create_context(
            session_id=session_id,
            scope=ContextScope.SESSION,
            initial_data={"initial": "data"},
            created_by="test_user",
        )
        
        assert result is not None
        mock_context_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_context(self, context_service, mock_context_repo):
        """Test creating agent-scoped context."""
        session_id = uuid4()
        agent_id = uuid4()
        
        mock_context_repo.save.return_value = ContextEntity(
            session_id=session_id,
            agent_id=agent_id,
            scope=ContextScope.AGENT,
            data={},
        )
        
        result = await context_service.create_context(
            session_id=session_id,
            agent_id=agent_id,
            scope=ContextScope.AGENT,
        )
        
        assert result is not None
        assert result.scope == ContextScope.AGENT

    @pytest.mark.asyncio
    async def test_create_global_context(self, context_service, mock_context_repo):
        """Test creating global-scoped context."""
        mock_context_repo.save.return_value = ContextEntity(
            scope=ContextScope.GLOBAL,
            data={"global": "config"},
        )
        
        result = await context_service.create_context(
            scope=ContextScope.GLOBAL,
            initial_data={"global": "config"},
        )
        
        assert result is not None
        assert result.scope == ContextScope.GLOBAL

    @pytest.mark.asyncio
    async def test_create_context_with_metadata(self, context_service, mock_context_repo):
        """Test creating context with custom metadata."""
        session_id = uuid4()
        
        mock_context_repo.save.return_value = ContextEntity(
            session_id=session_id,
            scope=ContextScope.SESSION,
            data={},
            metadata={"version": "1.0"},
        )
        
        result = await context_service.create_context(
            session_id=session_id,
            metadata={"version": "1.0"},
        )
        
        assert result is not None


# ============================================================================
# Test Context Retrieval
# ============================================================================

class TestContextRetrieval:
    """Test context retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_context_by_id(self, context_service, mock_context_repo, sample_session_context):
        """Test retrieving context by ID."""
        context_id = sample_session_context.id
        mock_context_repo.get_by_id.return_value = sample_session_context
        
        result = await context_service.get_context(context_id)
        
        assert result is not None
        assert result.id == context_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_context(self, context_service, mock_context_repo):
        """Test retrieving nonexistent context raises error."""
        context_id = uuid4()
        mock_context_repo.get_by_id.return_value = None
        
        with pytest.raises(ContextNotFoundError):
            await context_service.get_context(context_id)

    @pytest.mark.asyncio
    async def test_get_or_create_existing(self, context_service, mock_context_repo, sample_session_context):
        """Test get_or_create returns existing context."""
        session_id = sample_session_context.session_id
        mock_context_repo.find_by_session.return_value = [sample_session_context]
        
        result = await context_service.get_or_create_context(
            session_id=session_id,
            scope=ContextScope.SESSION,
        )
        
        assert result is not None
        # Should not call save since context exists
        mock_context_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_creates_new(self, context_service, mock_context_repo):
        """Test get_or_create creates new when none exists."""
        session_id = uuid4()
        mock_context_repo.find_by_session.return_value = []  # None exists
        
        new_context = ContextEntity(
            session_id=session_id,
            scope=ContextScope.SESSION,
            data={},
        )
        mock_context_repo.save.return_value = new_context
        
        result = await context_service.get_or_create_context(
            session_id=session_id,
            scope=ContextScope.SESSION,
        )
        
        assert result is not None
        mock_context_repo.save.assert_called_once()


# ============================================================================
# Test Context Update
# ============================================================================

class TestContextUpdate:
    """Test context update operations."""

    @pytest.mark.asyncio
    async def test_update_context(self, context_service, mock_context_repo, sample_session_context):
        """Test updating context data."""
        context_id = sample_session_context.id
        mock_context_repo.get_by_id.return_value = sample_session_context
        mock_context_repo.save.return_value = sample_session_context
        
        updates = {"new_key": "new_value", "config.timeout": 30}
        
        result = await context_service.update_context(
            context_id=context_id,
            updates=updates,
            changed_by="updater",
        )
        
        assert result is not None
        mock_context_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_context(self, context_service, mock_context_repo):
        """Test updating nonexistent context raises error."""
        context_id = uuid4()
        mock_context_repo.get_by_id.return_value = None
        
        with pytest.raises(ContextNotFoundError):
            await context_service.update_context(
                context_id=context_id,
                updates={"key": "value"},
            )


# ============================================================================
# Test Context Sharing
# ============================================================================

class TestContextSharing:
    """Test context sharing between sessions."""

    @pytest.mark.asyncio
    async def test_share_context_between_sessions(
        self, context_service, mock_context_repo, sample_session_context
    ):
        """Test sharing context from one session to another."""
        source_session_id = sample_session_context.session_id
        target_session_id = uuid4()
        
        mock_context_repo.find_by_session.return_value = [sample_session_context]
        mock_context_repo.get_by_id.return_value = sample_session_context
        mock_context_repo.save.return_value = sample_session_context
        
        result = await context_service.share_context(
            source_session_id=source_session_id,
            target_session_id=target_session_id,
        )
        
        assert result is not None

    @pytest.mark.asyncio
    async def test_share_specific_context(
        self, context_service, mock_context_repo, sample_session_context
    ):
        """Test sharing specific context by ID."""
        source_session_id = sample_session_context.session_id
        target_session_id = uuid4()
        context_id = sample_session_context.id
        
        mock_context_repo.get_by_id.return_value = sample_session_context
        mock_context_repo.save.return_value = sample_session_context
        
        result = await context_service.share_context(
            source_session_id=source_session_id,
            target_session_id=target_session_id,
            context_id=context_id,
        )
        
        assert result is not None


# ============================================================================
# Test Context Merging
# ============================================================================

class TestContextMerging:
    """Test context merge operations."""

    @pytest.mark.asyncio
    async def test_merge_two_contexts(self, context_service, mock_context_repo):
        """Test merging two contexts."""
        ctx1 = ContextEntity(
            session_id=uuid4(),
            scope=ContextScope.SESSION,
            data={"key1": "value1", "shared": "from_ctx1"},
        )
        ctx2 = ContextEntity(
            session_id=ctx1.session_id,
            scope=ContextScope.SESSION,
            data={"key2": "value2", "shared": "from_ctx2"},
        )
        
        mock_context_repo.get_by_id.side_effect = [ctx1, ctx2]
        mock_context_repo.save.return_value = ContextEntity(
            session_id=ctx1.session_id,
            scope=ContextScope.SESSION,
            data={},  # Merged data
        )
        
        result = await context_service.merge_contexts(
            context_ids=[ctx1.id, ctx2.id],
            strategy=MergeStrategy.LAST_WRITE_WINS,
        )
        
        assert result is not None
        mock_context_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_merge_with_deep_strategy(self, context_service, mock_context_repo):
        """Test merging with DEEP_MERGE strategy."""
        ctx1 = ContextEntity(
            session_id=uuid4(),
            scope=ContextScope.SESSION,
            data={"nested": {"key1": "v1"}},
        )
        ctx2 = ContextEntity(
            session_id=ctx1.session_id,
            scope=ContextScope.SESSION,
            data={"nested": {"key2": "v2"}},
        )
        
        mock_context_repo.get_by_id.side_effect = [ctx1, ctx2]
        mock_context_repo.save.return_value = ContextEntity(
            session_id=ctx1.session_id,
            scope=ContextScope.SESSION,
            data={"nested": {"key1": "v1", "key2": "v2"}},
        )
        
        result = await context_service.merge_contexts(
            context_ids=[ctx1.id, ctx2.id],
            strategy=MergeStrategy.DEEP_MERGE,
        )
        
        assert result is not None


# ============================================================================
# Test Global Promotion
# ============================================================================

class TestGlobalPromotion:
    """Test context promotion to global scope."""

    @pytest.mark.asyncio
    async def test_promote_session_to_global(
        self, context_service, mock_context_repo, sample_session_context
    ):
        """Test promoting session context to global scope."""
        context_id = sample_session_context.id
        mock_context_repo.get_by_id.return_value = sample_session_context
        
        global_context = ContextEntity(
            scope=ContextScope.GLOBAL,
            data=sample_session_context.data.copy(),
        )
        mock_context_repo.save.return_value = global_context
        
        result = await context_service.promote_to_global(
            context_id=context_id,
            promoted_by="admin",
        )
        
        assert result is not None
        assert result.scope == ContextScope.GLOBAL

    @pytest.mark.asyncio
    async def test_promote_nonexistent_context(self, context_service, mock_context_repo):
        """Test promoting nonexistent context raises error."""
        context_id = uuid4()
        mock_context_repo.get_by_id.return_value = None
        
        with pytest.raises(ContextNotFoundError):
            await context_service.promote_to_global(context_id)


# ============================================================================
# Test Context Diff
# ============================================================================

class TestContextDiff:
    """Test context diff operations."""

    @pytest.mark.asyncio
    async def test_get_context_diff(self, context_service, mock_context_repo):
        """Test getting diff between two contexts."""
        ctx_a = ContextEntity(
            session_id=uuid4(),
            scope=ContextScope.SESSION,
            data={"key1": "value1", "shared": "old_value"},
        )
        ctx_b = ContextEntity(
            session_id=ctx_a.session_id,
            scope=ContextScope.SESSION,
            data={"key2": "value2", "shared": "new_value"},
        )
        
        mock_context_repo.get_by_id.side_effect = [ctx_a, ctx_b]
        
        result = await context_service.get_context_diff(
            context_id_a=ctx_a.id,
            context_id_b=ctx_b.id,
        )
        
        assert result is not None


# ============================================================================
# Test Context Cleanup
# ============================================================================

class TestContextCleanup:
    """Test context cleanup operations."""

    @pytest.mark.asyncio
    async def test_cleanup_session_contexts(
        self, context_service, mock_context_repo, sample_session_context
    ):
        """Test cleaning up contexts for a session."""
        session_id = sample_session_context.session_id
        mock_context_repo.find_by_session.return_value = [sample_session_context]
        mock_context_repo.delete.return_value = True
        
        result = await context_service.cleanup_session_contexts(
            session_id=session_id,
            promote_important=False,
        )
        
        assert result >= 0

    @pytest.mark.asyncio
    async def test_get_global_contexts(self, context_service, mock_context_repo, sample_global_context):
        """Test retrieving all global contexts."""
        mock_context_repo.find_global_contexts.return_value = [sample_global_context]
        
        result = await context_service.get_global_contexts()
        
        assert len(result) == 1
        assert result[0].scope == ContextScope.GLOBAL


# ============================================================================
# Test Context Summary
# ============================================================================

class TestContextSummary:
    """Test context summary operations."""

    @pytest.mark.asyncio
    async def test_get_session_context_summary(
        self, context_service, mock_context_repo, sample_session_context
    ):
        """Test getting context summary for a session."""
        session_id = sample_session_context.session_id
        mock_context_repo.find_by_session.return_value = [sample_session_context]
        
        result = await context_service.get_session_context_summary(session_id)
        
        assert result is not None
        assert "total_contexts" in result or "count" in result or len(result) > 0
