"""
FINE-TUNING DOMAIN EXCEPTIONS
"""

from uuid import UUID
from typing import Any

class FineTuningError(Exception):
    """Base exception for fine-tuning errors"""
    pass

class InvalidFineTuningTransition(FineTuningError):
    """Raised when an invalid state transition is attempted"""
    def __init__(self, current_status: Any, target_status: Any, job_id: UUID):
        self.current_status = current_status
        self.target_status = target_status
        self.job_id = job_id
        super().__init__(
            f"Invalid transition from {current_status} to {target_status} for job {job_id}"
        )

class DatasetEmptyError(FineTuningError):
    """Raised when a training dataset is empty or insufficient"""
    pass

class ModelRegistryError(FineTuningError):
    """Raised when model registration fails"""
    pass
