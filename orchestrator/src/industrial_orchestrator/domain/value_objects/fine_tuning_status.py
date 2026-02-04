"""
FINE-TUNING STATUS VALUE OBJECT
Defines the lifecycle states for fine-tuning jobs.
"""

from enum import Enum, auto

class FineTuningStatus(str, Enum):
    """
    Lifecycle status for a fine-tuning job.
    
    States:
    - PENDING: Job created but not started
    - QUEUED: Job submitted to compute provider
    - RUNNING: Training in progress
    - EVALUATING: Running evaluation benchmarks
    - COMPLETED: Training finished successfully
    - FAILED: Training failed
    - CANCELLED: Job manually stopped
    """
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    def can_transition_to(self, new_status: 'FineTuningStatus') -> bool:
        """
        Validate state transitions.
        
        Transitions:
        - PENDING -> QUEUED, CANCELLED
        - QUEUED -> RUNNING, CANCELLED, FAILED
        - RUNNING -> EVALUATING, COMPLETED, FAILED, CANCELLED
        - EVALUATING -> COMPLETED, FAILED
        - COMPLETED -> (terminal)
        - FAILED -> PENDING (Retry)
        - CANCELLED -> PENDING (Retry)
        """
        # Terminal states
        if self in (FineTuningStatus.COMPLETED,):
            return False
            
        # Retry logic
        if self in (FineTuningStatus.FAILED, FineTuningStatus.CANCELLED):
            return new_status == FineTuningStatus.PENDING
            
        valid_transitions = {
            FineTuningStatus.PENDING: {
                FineTuningStatus.QUEUED,
                FineTuningStatus.CANCELLED
            },
            FineTuningStatus.QUEUED: {
                FineTuningStatus.RUNNING,
                FineTuningStatus.CANCELLED,
                FineTuningStatus.FAILED
            },
            FineTuningStatus.RUNNING: {
                FineTuningStatus.EVALUATING,
                FineTuningStatus.COMPLETED,
                FineTuningStatus.FAILED,
                FineTuningStatus.CANCELLED
            },
            FineTuningStatus.EVALUATING: {
                FineTuningStatus.COMPLETED,
                FineTuningStatus.FAILED
            }
        }
        
        return new_status in valid_transitions.get(self, set())
