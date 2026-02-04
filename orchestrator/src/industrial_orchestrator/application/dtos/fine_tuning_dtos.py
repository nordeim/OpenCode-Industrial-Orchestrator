"""
FINE-TUNING API DTOS
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

from ...domain.value_objects.fine_tuning_status import FineTuningStatus

class CreateFineTuningJobRequest(BaseModel):
    base_model: str
    target_model_name: str
    epochs: int = 3
    learning_rate: float = 5e-5

class FineTuningJobResponse(BaseModel):
    id: UUID
    base_model: str
    target_model_name: str
    status: FineTuningStatus
    sample_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class CurateDatasetRequest(BaseModel):
    output_dir: str
    min_success_rate: float = 0.9
    limit: int = 100
