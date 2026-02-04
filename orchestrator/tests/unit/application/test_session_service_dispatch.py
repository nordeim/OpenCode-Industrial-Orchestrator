"""
Unit tests for SessionService dispatch logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from industrial_orchestrator.application.services.session_service import SessionService
from industrial_orchestrator.domain.entities.session import SessionEntity, SessionStatus
from industrial_orchestrator.application.dtos.external_agent_protocol import EAPTaskResult, EAPTaskAssignment

@pytest.fixture
def mock_session_repo():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.get_with_metrics = AsyncMock()
    return repo

@pytest.fixture
def mock_agent_repo():
    repo = AsyncMock()
    repo.get_by_name = AsyncMock()
    return repo

@pytest.fixture
def mock_external_adapter():
    adapter = AsyncMock()
    adapter.send_task = AsyncMock()
    return adapter

@pytest.fixture
def mock_opencode_client():
    client = AsyncMock()
    client.execute_session_task = AsyncMock()
    return client

@pytest.fixture
def service(mock_session_repo, mock_agent_repo, mock_external_adapter, mock_opencode_client):
    svc = SessionService(
        session_repository=mock_session_repo,
        agent_repository=mock_agent_repo,
        external_agent_adapter=mock_external_adapter,
        opencode_client=mock_opencode_client,
        lock_timeout=1  # Fast tests
    )
    return svc

@pytest.mark.asyncio
async def test_execute_session_external_dispatch(service, mock_session_repo, mock_agent_repo, mock_external_adapter):
    # Setup Session
    session_id = uuid4()
    session = SessionEntity(
        id=session_id,
        title="Test External",
        initial_prompt="Do work",
        agent_config={"AGENT-EXT-01": {}},
        status=SessionStatus.PENDING
    )
    mock_session_repo.get_by_id.return_value = session
    mock_session_repo.get_with_metrics.return_value = session # For completion
    mock_session_repo.update.return_value = session

    # Setup Agent
    agent = MagicMock()
    agent.id = uuid4()
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
    with patch('industrial_orchestrator.application.services.session_service.distributed_lock') as mock_lock:
        mock_lock.return_value.__aenter__.return_value = True
        
        # Execute
        result = await service.execute_session(session_id)

    # Verify
    assert result["success"] is True
    assert result["output"] == {"result": "done"}
    
    # Verify call to external adapter
    mock_external_adapter.send_task.assert_called_once()
    call_args = mock_external_adapter.send_task.call_args
    assert call_args[1]["endpoint_url"] == "http://ext-agent"
    assert isinstance(call_args[1]["task_assignment"], EAPTaskAssignment)

@pytest.mark.asyncio
async def test_execute_session_internal_fallback(service, mock_session_repo, mock_agent_repo, mock_opencode_client):
    # Setup Session
    session_id = uuid4()
    session = SessionEntity(
        id=session_id,
        title="Test Internal",
        initial_prompt="Do work",
        agent_config={"AGENT-INT-01": {}},
        status=SessionStatus.PENDING
    )
    mock_session_repo.get_by_id.return_value = session
    mock_session_repo.get_with_metrics.return_value = session
    mock_session_repo.update.return_value = session

    # Setup Agent (Internal)
    agent = MagicMock()
    agent.metadata = {"is_external": False}
    mock_agent_repo.get_by_name.return_value = agent

    # Setup OpenCode Client Response
    mock_opencode_client.execute_session_task.return_value = {
        "session_id": str(session_id),
        "result": {"status": "ok"}
    }

    # Mock distributed_lock
    with patch('industrial_orchestrator.application.services.session_service.distributed_lock') as mock_lock:
        mock_lock.return_value.__aenter__.return_value = True
        
        # Execute
        result = await service.execute_session(session_id)

    # Verify
    mock_opencode_client.execute_session_task.assert_called_once()
    assert result["success"] is True