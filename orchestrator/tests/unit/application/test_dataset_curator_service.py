"""
UNIT TESTS - DATASET CURATOR SERVICE
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from pathlib import Path

from industrial_orchestrator.application.services.dataset_curator_service import DatasetCuratorService, DatasetSample
from industrial_orchestrator.domain.entities.session import SessionEntity, SessionStatus

@pytest.fixture
def mock_session_repo():
    return AsyncMock()

@pytest.fixture
def curator(mock_session_repo):
    return DatasetCuratorService(mock_session_repo)

@pytest.mark.asyncio
async def test_curate_dataset_success(curator, mock_session_repo, tmp_path):
    # Setup mock sessions
    session1 = MagicMock(spec=SessionEntity)
    session1.id = uuid4()
    session1.status = SessionStatus.COMPLETED
    session1.metrics = MagicMock()
    session1.metrics.success_rate = 0.95
    session1.metrics.result = {"code": "print(1)"}
    session1.initial_prompt = "Task 1"
    session1.session_type = MagicMock()
    session1.session_type.value = "execution"
    
    session2 = MagicMock(spec=SessionEntity)
    session2.id = uuid4()
    session2.status = SessionStatus.COMPLETED
    session2.metrics = MagicMock()
    session2.metrics.success_rate = 0.8 # Below threshold
    session2.metrics.result = {"code": "print(2)"}
    session2.initial_prompt = "Task 2"
    
    mock_session_repo.find_by_status.return_value = [session1, session2]
    
    # Execute
    output_dir = str(tmp_path)
    result_path = await curator.curate_dataset(output_dir, min_success_rate=0.9)
    
    # Verify
    assert result_path != ""
    assert Path(result_path).exists()
    
    with open(result_path, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1
        sample = json.loads(lines[0])
        assert sample["instruction"] == "Task 1"
        assert "print(1)" in sample["output"]

@pytest.mark.asyncio
async def test_curate_dataset_no_samples(curator, mock_session_repo, tmp_path):
    mock_session_repo.find_by_status.return_value = []
    
    result_path = await curator.curate_dataset(str(tmp_path))
    assert result_path == ""
