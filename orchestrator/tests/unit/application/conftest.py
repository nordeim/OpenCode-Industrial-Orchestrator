"""
CONFTEST - Application Services Test Fixtures
Shared fixtures for application service unit testing.

NOTE: These tests use mock-based testing to avoid importing infrastructure
modules that have deep dependencies.
"""

import pytest
from uuid import uuid4
from typing import Generator
from unittest.mock import AsyncMock, MagicMock


# ============================================================================
# Mock Repository Fixtures
# ============================================================================

@pytest.fixture
def mock_session_repository():
    """Fresh mock session repository for each test."""
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
def mock_agent_repository():
    """Fresh mock agent repository for each test."""
    repo = AsyncMock()
    repo.register = AsyncMock()
    repo.deregister = AsyncMock(return_value=True)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.find_by_capabilities = AsyncMock(return_value=[])
    repo.find_available = AsyncMock(return_value=[])
    repo.update_heartbeat = AsyncMock(return_value=True)
    repo.update_performance_metrics = AsyncMock(return_value=True)
    repo.cleanup_stale_agents = AsyncMock(return_value=0)
    repo.get_agent_stats = AsyncMock(return_value={"total": 0})
    return repo


@pytest.fixture
def mock_context_repository():
    """Fresh mock context repository for each test."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.save = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    repo.find_by_session = AsyncMock(return_value=[])
    repo.find_by_agent = AsyncMock(return_value=[])
    repo.find_by_scope = AsyncMock(return_value=[])
    repo.find_global_contexts = AsyncMock(return_value=[])
    return repo


# ============================================================================
# Mock Port Fixtures
# ============================================================================

@pytest.fixture
def mock_lock():
    """Fresh mock distributed lock for each test."""
    lock = MagicMock()
    lock.acquire = MagicMock(return_value=True)
    lock.release = MagicMock(return_value=True)
    return lock


@pytest.fixture
def mock_opencode_client():
    """Fresh mock OpenCode client."""
    client = AsyncMock()
    client.initialize = AsyncMock()
    client.execute_session_task = AsyncMock(return_value={
        "session_id": "oc-123",
        "diff": {"files_changed": 2},
        "metrics": {"tokens": 1000},
    })
    return client


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_session_id():
    """Generate a sample session UUID."""
    return uuid4()


@pytest.fixture
def sample_agent_id():
    """Generate a sample agent UUID."""
    return uuid4()


@pytest.fixture
def sample_context_id():
    """Generate a sample context UUID."""
    return uuid4()
