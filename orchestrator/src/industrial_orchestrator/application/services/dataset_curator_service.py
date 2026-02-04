"""
DATASET CURATOR SERVICE
Application service for extracting and filtering session data for model fine-tuning.
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID
from pathlib import Path

from pydantic import BaseModel, Field

from ...domain.entities.session import SessionEntity, SessionStatus
from ...application.ports.repository_ports import SessionRepositoryPort

logger = logging.getLogger(__name__)

class DatasetSample(BaseModel):
    """A single training sample for LLM fine-tuning"""
    instruction: str
    input: str = ""
    output: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DatasetCuratorService:
    """
    Industrial service for automated dataset curation from session history.
    """
    
    def __init__(self, session_repository: SessionRepositoryPort):
        self._session_repo = session_repository
        
    async def curate_dataset(
        self,
        output_dir: str,
        min_success_rate: float = 0.9,
        session_type: Optional[str] = None,
        limit: int = 1000
    ) -> str:
        """
        Extract high-quality sessions and save as JSONL dataset.
        
        Args:
            output_dir: Directory to save dataset
            min_success_rate: Minimum success rate threshold
            session_type: Optional filter by session type
            limit: Max samples to extract
            
        Returns:
            Path to the generated dataset file
        """
        # 1. Fetch COMPLETED sessions
        sessions = await self._session_repo.find_by_status(
            status=SessionStatus.COMPLETED,
            limit=limit
        )
        
        # 2. Filter by quality heuristics
        high_quality_sessions = [
            s for s in sessions 
            if s.metrics.success_rate >= min_success_rate
            and (session_type is None or s.session_type == session_type)
        ]
        
        if not high_quality_sessions:
            logger.warning("No sessions met the curation criteria.")
            return ""
            
        # 3. Format samples
        samples = []
        for session in high_quality_sessions:
            sample = DatasetSample(
                instruction=session.initial_prompt,
                output=json.dumps(session.metrics.result) if isinstance(session.metrics.result, dict) else str(session.metrics.result),
                metadata={
                    "session_id": str(session.id),
                    "success_rate": session.metrics.success_rate,
                    "session_type": session.session_type.value
                }
            )
            samples.append(sample)
            
        # 4. Save to JSONL
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"dataset_{timestamp}.jsonl"
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            for sample in samples:
                f.write(json.dumps(sample.model_dump()) + '\n')
                
        logger.info(f"Curated dataset with {len(samples)} samples: {output_path}")
        return str(output_path)
