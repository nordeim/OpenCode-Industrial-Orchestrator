"""
UNIT TESTS - FINE-TUNING SERVICE
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from industrial_orchestrator.application.services.fine_tuning_service import FineTuningService
from industrial_orchestrator.domain.entities.fine_tuning import FineTuningJob, TrainingMetrics
from industrial_orchestrator.domain.value_objects.fine_tuning_status import FineTuningStatus

@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda x: x)
    repo.get_by_id = AsyncMock()
    return repo

@pytest.fixture
def mock_curator():
    curator = AsyncMock()
    curator.curate_dataset = AsyncMock()
    return curator

@pytest.fixture
def service(mock_repo, mock_curator):
    return FineTuningService(mock_repo, mock_curator)

@pytest.mark.asyncio
async def test_create_job(service, mock_repo):
    job = await service.create_job("base-model", "target-model")
    assert job.base_model == "base-model"
    assert job.target_model_name == "target-model"
    assert job.status == FineTuningStatus.PENDING
    mock_repo.save.assert_called_once()

@pytest.mark.asyncio
async def test_start_pipeline_success(service, mock_repo, mock_curator):
    job_id = uuid4()
    job = FineTuningJob(id=job_id, base_model="base", target_model_name="target")
    mock_repo.get_by_id.return_value = job
    mock_curator.curate_dataset.return_value = "/path/to/dataset.jsonl"
    
    updated_job = await service.start_pipeline(job_id, "/tmp")
    
    assert updated_job.status == FineTuningStatus.RUNNING
    assert updated_job.dataset_path == "/path/to/dataset.jsonl"
    assert mock_repo.save.call_count >= 2

@pytest.mark.asyncio
async def test_complete_job(service, mock_repo):
    job_id = uuid4()
    job = FineTuningJob(id=job_id, base_model="base", target_model_name="target", status=FineTuningStatus.RUNNING)
    mock_repo.get_by_id.return_value = job
    
    metrics = TrainingMetrics(final_loss=0.1)
    completed_job = await service.update_job_progress(job_id, metrics)
    
    assert completed_job.status == FineTuningStatus.COMPLETED
    assert completed_job.metrics.final_loss == 0.1
