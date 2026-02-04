"""
INTEGRATION TESTS - EXTERNAL AGENTS API
Verify EAP registration and heartbeat flows.
"""

import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from src.industrial_orchestrator.presentation.api.main import app
from src.industrial_orchestrator.presentation.api.dependencies import get_agent_service
from src.industrial_orchestrator.application.services.agent_management_service import AgentManagementService
from src.industrial_orchestrator.application.dtos.external_agent_protocol import (
    EAPRegistrationResponse
)
from src.industrial_orchestrator.domain.entities.agent import AgentType, AgentCapability

# Mock the service dependency
mock_agent_service = AsyncMock(spec=AgentManagementService)

def get_mock_agent_service():
    return mock_agent_service

# Override dependency
app.dependency_overrides[get_agent_service] = get_mock_agent_service

client = TestClient(app)

@pytest.mark.integration
def test_register_external_agent_success():
    """Test successful external agent registration"""
    
    # Setup mock response
    mock_response = EAPRegistrationResponse(
        agent_id="12345678-1234-5678-1234-567812345678",
        status="registered",
        auth_token="secure_token_123",
        heartbeat_interval_seconds=30
    )
    mock_agent_service.register_external_agent.return_value = mock_response
    
    payload = {
        "protocol_version": "1.0",
        "name": "AGENT-EXT-TEST-01",
        "version": "1.0.0",
        "agent_type": "implementer",
        "capabilities": ["code_generation", "test_generation"], # Valid capabilities
        "endpoint_url": "http://localhost:8080/webhook",
        "metadata": {"env": "test"}
    }
    
    response = client.post("/api/v1/agents/external/register", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "registered"
    assert "agent_id" in data
    assert "auth_token" in data
    
    # Verify service call
    mock_agent_service.register_external_agent.assert_called_once()

@pytest.mark.integration
def test_agent_heartbeat_success():
    """Test heartbeat with valid token"""
    
    agent_id = "12345678-1234-5678-1234-567812345678"
    token = "secure_token_123"
    
    # Setup mocks
    mock_agent_service.authenticate_agent.return_value = True
    mock_agent_service.heartbeat.return_value = True
    
    payload = {
        "status": "healthy",
        "current_load": 0.5,
        "metrics": {"uptime": 100}
    }
    
    headers = {"X-Agent-Token": token}
    
    response = client.post(f"/api/v1/agents/external/{agent_id}/heartbeat", json=payload, headers=headers)
    
    assert response.status_code == 204
    
    # Verify service calls
    mock_agent_service.authenticate_agent.assert_called_with(UUID(agent_id), token)
    mock_agent_service.heartbeat.assert_called_with(UUID(agent_id))

@pytest.mark.integration
def test_agent_heartbeat_unauthorized():
    """Test heartbeat with invalid token"""
    
    agent_id = "12345678-1234-5678-1234-567812345678"
    
    mock_agent_service.authenticate_agent.return_value = False
    
    payload = {
        "status": "healthy",
        "current_load": 0.5
    }
    
    headers = {"X-Agent-Token": "wrong_token"}
    
    response = client.post(f"/api/v1/agents/external/{agent_id}/heartbeat", json=payload, headers=headers)
    
    assert response.status_code == 401
