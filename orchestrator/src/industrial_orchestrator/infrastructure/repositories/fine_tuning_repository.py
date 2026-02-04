"""
FINE-TUNING REPOSITORY
Infrastructure adapter for fine-tuning job persistence.
"""

from typing import Type, Optional, List, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ...domain.entities.fine_tuning import FineTuningJob, TrainingParameters, TrainingMetrics
from ...domain.value_objects.fine_tuning_status import FineTuningStatus
from ...domain.value_objects.model_version import ModelVersion
from ...application.ports.repository_ports import FineTuningRepositoryPort
from ..database.models import FineTuningJobModel
from .base import IndustrialRepository

class FineTuningRepository(IndustrialRepository[FineTuningJob, FineTuningJobModel, UUID], FineTuningRepositoryPort):
    """
    Industrial repository for managing fine-tuning jobs.
    """
    
    @property
    def model_class(self) -> Type[FineTuningJobModel]:
        return FineTuningJobModel
        
    @property
    def entity_class(self) -> Type[FineTuningJob]:
        return FineTuningJob
        
    @property
    def cache_prefix(self) -> str:
        return "fine_tuning"
        
    def _to_entity(self, model: FineTuningJobModel) -> FineTuningJob:
        """Convert database model to domain entity"""
        return FineTuningJob(
            id=model.id,
            base_model=model.base_model,
            target_model_name=model.target_model_name,
            status=FineTuningStatus(model.status),
            version=ModelVersion.model_validate(model.version),
            parameters=TrainingParameters.model_validate(model.parameters),
            metrics=TrainingMetrics.model_validate(model.metrics),
            dataset_path=model.dataset_path,
            sample_count=model.sample_count,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            error_message=model.error_message
        )
        
    def _to_model(self, entity: FineTuningJob, existing_model: Optional[FineTuningJobModel] = None) -> FineTuningJobModel:
        """Convert domain entity to database model"""
        model = existing_model or FineTuningJobModel(id=entity.id)
        
        model.base_model = entity.base_model
        model.target_model_name = entity.target_model_name
        model.status = entity.status.value
        model.version = entity.version.model_dump()
        model.parameters = entity.parameters.model_dump()
        model.metrics = entity.metrics.model_dump()
        model.dataset_path = entity.dataset_path
        model.sample_count = entity.sample_count
        model.started_at = entity.started_at
        model.completed_at = entity.completed_at
        model.error_message = entity.error_message
        
        return model

    async def save(self, job: FineTuningJob) -> FineTuningJob:
        """Implementation of FineTuningRepositoryPort.save"""
        # IndustrialRepository has add() and update()
        # We'll use a unified save approach
        if await self.exists(job.id):
            return await self.update(job)
        else:
            return await self.add(job)

    async def find_by_status(self, status: FineTuningStatus) -> List[FineTuningJob]:
        """Find jobs by status"""
        async with self._get_session() as session:
            query = select(self.model_class).where(self.model_class.status == status.value)
            result = await session.execute(query)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]

    async def get_active_jobs(self) -> List[FineTuningJob]:
        """Retrieve all currently running or queued jobs"""
        active_statuses = [
            FineTuningStatus.PENDING.value,
            FineTuningStatus.QUEUED.value,
            FineTuningStatus.RUNNING.value,
            FineTuningStatus.EVALUATING.value
        ]
        async with self._get_session() as session:
            query = select(self.model_class).where(self.model_class.status.in_(active_statuses))
            result = await session.execute(query)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]
