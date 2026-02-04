"""
FINE-TUNING JOB ENTITY
Tracks the lifecycle of an LLM fine-tuning process.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from pydantic import Field, ConfigDict

from .base import DomainEntity
from ..value_objects.fine_tuning_status import FineTuningStatus
from ..value_objects.model_version import ModelVersion
from ..exceptions.fine_tuning_exceptions import InvalidFineTuningTransition

class TrainingParameters(DomainEntity):
    """Configuration for training run"""
    epochs: int = Field(default=3, ge=1)
    learning_rate: float = Field(default=5e-5, gt=0)
    batch_size: int = Field(default=4, ge=1)
    lora_rank: int = Field(default=8, ge=1)
    lora_alpha: int = Field(default=16, ge=1)
    target_modules: List[str] = Field(default_factory=lambda: ["q_proj", "v_module"])

class TrainingMetrics(DomainEntity):
    """Metrics collected during training"""
    final_loss: Optional[float] = None
    eval_loss: Optional[float] = None
    accuracy: Optional[float] = None
    training_duration_seconds: Optional[float] = None
    tokens_processed: int = 0

class FineTuningJob(DomainEntity):
    """
    Industrial entity representing a fine-tuning job.
    """
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID = Field(...)  # Required for isolation
    base_model: str = Field(..., min_length=1)
    target_model_name: str = Field(..., min_length=1)
    version: ModelVersion = Field(default_factory=ModelVersion)
    status: FineTuningStatus = Field(default=FineTuningStatus.PENDING)
    
    # Provider integration
    external_job_id: Optional[str] = None
    
    # Dataset details
    dataset_path: Optional[str] = None
    sample_count: int = 0
    
    # Parameters & Metrics
    parameters: TrainingParameters = Field(default_factory=TrainingParameters)
    metrics: TrainingMetrics = Field(default_factory=TrainingMetrics)
    
    # Lifecycle Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def transition_to(self, new_status: FineTuningStatus) -> None:
        """Industrial state transition validation"""
        if not self.status.can_transition_to(new_status):
            raise InvalidFineTuningTransition(
                current_status=self.status,
                target_status=new_status,
                job_id=self.id
            )
        
        self.status = new_status
        
        if new_status == FineTuningStatus.RUNNING:
            self.started_at = datetime.now(timezone.utc)
        elif new_status in (FineTuningStatus.COMPLETED, FineTuningStatus.FAILED, FineTuningStatus.CANCELLED):
            self.completed_at = datetime.now(timezone.utc)
            
    def start_training(self, dataset_path: str, count: int) -> None:
        """Move job to training state"""
        if self.status != FineTuningStatus.PENDING:
            raise InvalidFineTuningTransition(
                current_status=self.status,
                target_status=FineTuningStatus.RUNNING,
                job_id=self.id
            )
        
        self.dataset_path = dataset_path
        self.sample_count = count
        self.transition_to(FineTuningStatus.QUEUED)
        
    def complete(self, metrics: TrainingMetrics) -> None:
        """Finalize job with success"""
        self.metrics = metrics
        self.transition_to(FineTuningStatus.COMPLETED)
        
    def fail(self, reason: str) -> None:
        """Mark job as failed"""
        self.error_message = reason
        self.transition_to(FineTuningStatus.FAILED)
