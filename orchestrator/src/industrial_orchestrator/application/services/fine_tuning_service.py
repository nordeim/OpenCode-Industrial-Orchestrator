"""
FINE-TUNING APPLICATION SERVICE
Coordinates the dataset curation and model training pipeline.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID

from ...domain.entities.fine_tuning import FineTuningJob, TrainingParameters, TrainingMetrics
from ...domain.value_objects.fine_tuning_status import FineTuningStatus
from ...application.ports.repository_ports import FineTuningRepositoryPort
from ...application.ports.service_ports import TrainingProviderPort
from .dataset_curator_service import DatasetCuratorService
from ..context import get_current_tenant_id

logger = logging.getLogger(__name__)

class FineTuningService:
    """
    Industrial service for managing the fine-tuning pipeline.
    """
    
    def __init__(
        self,
        repository: FineTuningRepositoryPort,
        dataset_curator: DatasetCuratorService,
        training_provider: Optional[TrainingProviderPort] = None
    ):
        self._repo = repository
        self._curator = dataset_curator
        self._provider = training_provider
        
    async def create_job(
        self,
        base_model: str,
        target_model_name: str,
        parameters: Optional[TrainingParameters] = None
    ) -> FineTuningJob:
        """Create a new fine-tuning job entry"""
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            raise ValueError("Tenant context required for fine-tuning")

        job = FineTuningJob(
            tenant_id=tenant_id,
            base_model=base_model,
            target_model_name=target_model_name,
            parameters=parameters or TrainingParameters()
        )
        return await self._repo.save(job)
        
    async def start_pipeline(
        self,
        job_id: UUID,
        dataset_dir: str
    ) -> FineTuningJob:
        """
        Execute the full pipeline: Curate -> Queue -> (Simulated) Train
        """
        job = await self._repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
            
        try:
            # 1. Dataset Curation
            dataset_path = await self._curator.curate_dataset(
                output_dir=dataset_dir,
                limit=100
            )
            
            if not dataset_path:
                job.fail("Dataset curation yielded zero samples")
                return await self._repo.save(job)
                
            # 2. Update Job state
            job.start_training(dataset_path, 100) # Hardcoded sample count for stub
            await self._repo.save(job)
            
            # 3. Submit to Training Provider
            if self._provider:
                logger.info(f"Submitting job {job_id} to compute provider...")
                external_id = await self._provider.start_training(job)
                job.external_job_id = external_id
                job.transition_to(FineTuningStatus.RUNNING)
            else:
                logger.warning(f"No training provider configured for job {job_id}, simulation mode.")
                job.transition_to(FineTuningStatus.RUNNING)
                
            await self._repo.save(job)
            return job
            
        except Exception as e:
            logger.exception(f"Pipeline failure for job {job_id}")
            job.fail(str(e))
            return await self._repo.save(job)
            
    async def update_job_progress(
        self,
        job_id: UUID,
        metrics: TrainingMetrics
    ) -> FineTuningJob:
        """Update training metrics and potentially complete job"""
        job = await self._repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
            
        job.complete(metrics)
        return await self._repo.save(job)

    async def poll_jobs(self) -> int:
        """
        Poll active jobs from provider and update their state.
        Returns count of jobs updated.
        """
        if not self._provider:
            return 0
            
        active_jobs = await self._repo.get_active_jobs()
        updated_count = 0
        
        for job in active_jobs:
            if not job.external_job_id:
                continue
                
            status_data = await self._provider.get_status(job.external_job_id)
            status_str = status_data.get("status")
            
            if status_str == "completed":
                metrics_data = status_data.get("metrics", {})
                metrics = TrainingMetrics(**metrics_data)
                job.complete(metrics)
                updated_count += 1
            elif status_str == "failed":
                job.fail(status_data.get("error", "Unknown error"))
                updated_count += 1
            elif status_str == "running":
                # Optionally update progress in metadata
                job.metadata["progress"] = status_data.get("progress", 0.0)
                
            await self._repo.save(job)
            
        return updated_count
