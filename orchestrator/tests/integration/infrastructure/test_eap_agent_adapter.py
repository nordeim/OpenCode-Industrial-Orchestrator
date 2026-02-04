"""
Integration tests for EAPAgentAdapter.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from industrial_orchestrator.infrastructure.adapters.eap_agent_adapter import EAPAgentAdapter
from industrial_orchestrator.application.dtos.external_agent_protocol import (
    EAPTaskAssignment,
    EAPTaskResult,
    EAPHeartbeatRequest,
    EAPStatus
)
from industrial_orchestrator.infrastructure.exceptions.opencode_exceptions import OpenCodeAPIError

@pytest.fixture
def adapter():
    return EAPAgentAdapter()

@pytest.fixture
def task_assignment():
    return EAPTaskAssignment(
        task_id=uuid4(),
        session_id=uuid4(),
        task_type="code_generation",
        context={"foo": "bar"},
        input_data="Write a function",
        requirements=["python"]
    )

@pytest.mark.asyncio
async def test_send_task_success(adapter, task_assignment):
    # Mock response data
    response_data = {
        "task_id": str(task_assignment.task_id),
        "status": "completed",
        "artifacts": [{"path": "main.py", "content": "print('hello')"}],
        "execution_time_ms": 100.0,
        "tokens_used": 50
    }
    
    # Mock httpx client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = MagicMock()
    
    adapter._client.post = AsyncMock(return_value=mock_response)
    
    # Execute
    result = await adapter.send_task(
        agent_id="test-agent",
        endpoint_url="http://localhost:8080",
        auth_token="secret",
        task_assignment=task_assignment
    )
    
    # Verify
    assert isinstance(result, EAPTaskResult)
    assert result.task_id == task_assignment.task_id
    assert result.status == "completed"
    assert result.artifacts[0].path == "main.py"
    
    # Verify call
    adapter._client.post.assert_called_once()
    call_args = adapter._client.post.call_args
    assert call_args[0][0] == "http://localhost:8080/task"
    assert call_args[1]["headers"]["X-Agent-Token"] == "secret"
    assert call_args[1]["json"]["task_id"] == str(task_assignment.task_id)

@pytest.mark.asyncio
async def test_send_task_failure(adapter, task_assignment):
    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    
    # Create an HTTPStatusError
    import httpx
    error = httpx.HTTPStatusError(
        "500 Error", 
        request=MagicMock(), 
        response=mock_response
    )
    mock_response.raise_for_status.side_effect = error
    
    adapter._client.post = AsyncMock(return_value=mock_response)
    
    # Execute and expect exception
    with pytest.raises(OpenCodeAPIError):
        await adapter.send_task(
            agent_id="test-agent",
            endpoint_url="http://localhost:8080",
            auth_token="secret",
            task_assignment=task_assignment
        )

@pytest.mark.asyncio
async def test_check_health_success(adapter):
    response_data = {
        "status": "healthy",
        "current_load": 0.5,
        "metrics": {},
        "timestamp": datetime.now().isoformat()
    }
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = MagicMock()
    
    adapter._client.get = AsyncMock(return_value=mock_response)
    
    result = await adapter.check_health(
        agent_id="test-agent",
        endpoint_url="http://localhost:8080",
        auth_token="secret"
    )
    
    assert isinstance(result, EAPHeartbeatRequest)
    assert result.status == EAPStatus.HEALTHY
