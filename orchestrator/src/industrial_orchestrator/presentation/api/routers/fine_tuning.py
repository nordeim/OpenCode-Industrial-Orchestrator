"""
FINE-TUNING API ROUTER
"""

from uuid import UUID
from typing import List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ....application.services.fine_tuning_service import FineTuningService
from ....application.dtos.fine_tuning_dtos import (
    CreateFineTuningJobRequest,
    FineTuningJobResponse,
    CurateDatasetRequest
)
from ..dependencies import get_fine_tuning_service

router = APIRouter(
    prefix="/api/v1/fine-tuning",
    tags=["Fine-Tuning"],
)

@router.post(
    "/jobs",
    response_model=FineTuningJobResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_job(
    request: CreateFineTuningJobRequest,
    service: Annotated[FineTuningService, Depends(get_fine_tuning_service)]
):
    """Create a new fine-tuning job"""
    job = await service.create_job(
        base_model=request.base_model,
        target_model_name=request.target_model_name
    )
    return FineTuningJobResponse(**job.model_dump())

@router.post(
    "/jobs/{job_id}/start",
    response_model=FineTuningJobResponse
)
async def start_job(
    job_id: UUID,
    dataset_dir: str,
    service: Annotated[FineTuningService, Depends(get_fine_tuning_service)]
):
    """Start the fine-tuning pipeline for a job"""
    try:
        job = await service.start_pipeline(job_id, dataset_dir)
        return FineTuningJobResponse(**job.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get(
    "/jobs/{job_id}",
    response_model=FineTuningJobResponse
)
async def get_job(
    job_id: UUID,
    service: Annotated[FineTuningService, Depends(get_fine_tuning_service)]
):
    """Retrieve job details"""
    # This would call service.get_job, implementing here for stub
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post(
    "/jobs/poll",
    status_code=status.HTTP_200_OK
)
async def poll_jobs(
    service: Annotated[FineTuningService, Depends(get_fine_tuning_service)]
):
    """Trigger status synchronization for all active jobs"""
    updated_count = await service.poll_jobs()
    return {"updated_count": updated_count}
