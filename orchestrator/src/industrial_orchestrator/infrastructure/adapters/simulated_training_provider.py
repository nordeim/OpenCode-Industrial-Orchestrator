"""
SIMULATED TRAINING PROVIDER
Infrastructure adapter for simulating LLM training for testing and development.
"""

import asyncio
import random
from typing import Dict, Any
from uuid import uuid4
from datetime import datetime, timezone

from ...application.ports.service_ports import TrainingProviderPort
from ...domain.entities.fine_tuning import FineTuningJob

class SimulatedTrainingProvider(TrainingProviderPort):
    """
    Simulates a training provider with realistic delays and status transitions.
    """
    
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        
    async def start_training(self, job: FineTuningJob) -> str:
        """
        Submit a job to the simulated cloud.
        """
        external_id = f"sim-{uuid4().hex[:8]}"
        self._jobs[external_id] = {
            "status": "running",
            "progress": 0.0,
            "started_at": datetime.now(timezone.utc),
            "total_epochs": job.parameters.epochs
        }
        
        # Start a background "simulation" task
        asyncio.create_task(self._simulate_training(external_id))
        
        return external_id
        
    async def get_status(self, external_job_id: str) -> Dict[str, Any]:
        """
        Retrieve simulated status.
        """
        if external_job_id not in self._jobs:
            return {"status": "failed", "error": "Not found"}
            
        return self._jobs[external_job_id]
        
    async def cancel_job(self, external_job_id: str) -> bool:
        """
        Manually stop simulation.
        """
        if external_job_id in self._jobs:
            self._jobs[external_job_id]["status"] = "cancelled"
            return True
        return False
        
    async def _simulate_training(self, external_id: str):
        """
        Background task to update progress over time.
        """
        # Training takes 10-20 seconds in simulation
        duration = random.randint(10, 20)
        steps = 10
        
        for i in range(steps):
            await asyncio.sleep(duration / steps)
            if external_id not in self._jobs or self._jobs[external_id]["status"] == "cancelled":
                return
                
            self._jobs[external_id]["progress"] = (i + 1) / steps
            
        # Finalize
        if external_id in self._jobs:
            self._jobs[external_id]["status"] = "completed"
            self._jobs[external_id]["metrics"] = {
                "final_loss": random.uniform(0.1, 0.5),
                "eval_loss": random.uniform(0.2, 0.6),
                "accuracy": random.uniform(0.85, 0.99)
            }
