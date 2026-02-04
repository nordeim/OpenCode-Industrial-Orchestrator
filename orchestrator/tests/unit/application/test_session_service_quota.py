"""
UNIT TESTS - SESSION SERVICE QUOTA ENFORCEMENT
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from industrial_orchestrator.application.services.session_service import SessionService
from industrial_orchestrator.domain.entities.session import SessionEntity
from industrial_orchestrator.domain.entities.tenant import Tenant
from industrial_orchestrator.domain.exceptions.tenant_exceptions import QuotaExceededError

@pytest.fixture
def mock_session_repo():
    repo = AsyncMock()
    repo.add = AsyncMock(side_effect=lambda x: x)
    repo.count_active_by_tenant = AsyncMock()
    return repo

@pytest.fixture
def mock_tenant_repo():
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo

@pytest.fixture
def service(mock_session_repo, mock_tenant_repo):
    return SessionService(
        session_repository=mock_session_repo,
        tenant_repository=mock_tenant_repo
    )

@pytest.mark.asyncio
async def test_create_session_respects_quota(service, mock_session_repo, mock_tenant_repo):
    tenant_id = uuid4()
    
    # 1. Setup mock tenant with 2 sessions limit
    tenant = Tenant(id=tenant_id, name="Team A", slug="team-a", max_concurrent_sessions=2)
    mock_tenant_repo.get_by_id.return_value = tenant
    
    # 2. Setup mock active count at 2 (quota reached)
    mock_session_repo.count_active_by_tenant.return_value = 2
    
    # 3. Execute and expect failure
    with patch('industrial_orchestrator.application.services.session_service.get_current_tenant_id', return_value=tenant_id):
        with pytest.raises(QuotaExceededError) as exc:
            await service.create_session(title="Over Quota", initial_prompt="...")
        
        assert exc.value.limit == 2
        assert "concurrent_sessions" in str(exc.value)

@pytest.mark.asyncio
async def test_create_session_within_quota(service, mock_session_repo, mock_tenant_repo):
    tenant_id = uuid4()
    
    # 1. Setup mock tenant with 5 sessions limit
    tenant = Tenant(id=tenant_id, name="Team A", slug="team-a", max_concurrent_sessions=5)
    mock_tenant_repo.get_by_id.return_value = tenant
    
    # 2. Setup mock active count at 1 (within quota)
    mock_session_repo.count_active_by_tenant.return_value = 1
    
    # 3. Execute
    with patch('industrial_orchestrator.application.services.session_service.get_current_tenant_id', return_value=tenant_id):
        session = await service.create_session(title="Actionable title", initial_prompt="...")
        
        assert session.tenant_id == tenant_id
        mock_session_repo.add.assert_called_once()
