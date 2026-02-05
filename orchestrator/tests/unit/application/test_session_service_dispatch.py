"""
TEST SESSION SERVICE DISPATCH
Tests for Agent routing and execution dispatch (Internal vs External).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.industrial_orchestrator.application.services.session_service import SessionService
from src.industrial_orchestrator.domain.entities.session import (
    SessionEntity,
    SessionStatus,
)
from src.industrial_orchestrator.domain.entities.registry import RegisteredAgent
from src.industrial_orchestrator.application.dtos.external_agent_protocol import (
    EAPTaskAssignment,
    EAPTaskResult,
)


@pytest.fixture
def mock_session_repo():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_with_metrics = AsyncMock()
    repo.update = AsyncMock()
    repo.add = AsyncMock()
    return repo


@pytest.fixture
def mock_agent_repo():
    repo = AsyncMock()
    repo.get_by_name = AsyncMock()
    return repo


@pytest.fixture
def mock_external_adapter():
    return AsyncMock()


@pytest.fixture
def mock_opencode_client():
    client = AsyncMock()
    client.execute_session_task = AsyncMock()
    return client


@pytest.fixture
def service(mock_session_repo, mock_agent_repo, mock_external_adapter, mock_opencode_client):
    return SessionService(
        session_repository=mock_session_repo,
        agent_repository=mock_agent_repo,
        external_agent_adapter=mock_external_adapter,
        opencode_client=mock_opencode_client
    )


@pytest.mark.asyncio
async def test_execute_session_external_dispatch(service, mock_session_repo, mock_agent_repo, mock_external_adapter):
    # Setup Session
    session_id = uuid4()
    tenant_id = uuid4()
    session = SessionEntity(
        id=session_id,
        tenant_id=tenant_id,
        title="Test External",
        initial_prompt="Do work",
        agent_config={"AGENT-EXT-01": {}},
        status=SessionStatus.PENDING
    )
    mock_session_repo.get_by_id.return_value = session
    mock_session_repo.get_with_metrics.return_value = session
    mock_session_repo.update.return_value = session

    # Setup Agent
    agent = MagicMock(spec=RegisteredAgent)
    agent.id = uuid4()
    agent.name = "AGENT-EXT-01"
    agent.metadata = {
        "is_external": True,
        "endpoint_url": "http://ext-agent",
        "auth_token": "token"
    }
    mock_agent_repo.get_by_name.return_value = agent

    # Setup Adapter Response
    eap_result = EAPTaskResult(
        task_id=uuid4(),
        status="completed",
        output_data={"result": "done"},
        execution_time_ms=100
    )
    mock_external_adapter.send_task.return_value = eap_result

    # Mock distributed_lock context manager
    with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock') as mock_lock:
        mock_lock.return_value.__aenter__.return_value = True
        
        # Execute
        result = await service.execute_session(session_id)

    # Verify
    assert result["success"] is True
    assert result["output"] == {"result": "done"}
    
    # Verify call to external adapter
    mock_external_adapter.send_task.assert_called_once()


@pytest.mark.asyncio
async def test_execute_session_internal_fallback(service, mock_session_repo, mock_agent_repo, mock_opencode_client):
    # Setup Session
    session_id = uuid4()
    tenant_id = uuid4()
    session = SessionEntity(
        id=session_id,
        tenant_id=tenant_id,
        title="Test Internal",
        initial_prompt="Do work",
        agent_config={"AGENT-INT-01": {}},
        status=SessionStatus.PENDING
    )
    mock_session_repo.get_by_id.return_value = session
    mock_session_repo.get_with_metrics.return_value = session
    mock_session_repo.update.return_value = session

    # Setup Agent (Not external)
    agent = MagicMock(spec=RegisteredAgent)
    agent.id = uuid4()
    agent.name = "AGENT-INT-01"
    agent.metadata = {"is_external": False}
    mock_agent_repo.get_by_name.return_value = agent

    # Setup OpenCode Response
    mock_opencode_client.execute_session_task.return_value = {
        "session_id": "oc-123",
        "diff": {"patch": "---"},
        "metrics": {"duration": 1.0}
    }

    # Mock distributed_lock
    with patch('src.industrial_orchestrator.application.services.session_service.distributed_lock') as mock_lock:
        mock_lock.return_value.__aenter__.return_value = True
        
        # Execute
        result = await service.execute_session(session_id)

    # Verify
    assert result["success"] is True
    assert result["opencode_session_id"] == "oc-123"
    mock_opencode_client.execute_session_task.assert_called_once()
