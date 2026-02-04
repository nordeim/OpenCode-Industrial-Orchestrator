"""
EXTERNAL AGENT API ROUTER
Endpoints for External Agent Protocol (EAP) v1.0.
Handles registration, heartbeats, and task polling for external agents.
"""

from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Header

from ....application.services.agent_management_service import AgentManagementService
from ....application.dtos.external_agent_protocol import (
    EAPRegistrationRequest,
    EAPRegistrationResponse,
    EAPHeartbeatRequest,
    EAPStatus
)
from ..dependencies import get_agent_service

router = APIRouter(
    prefix="/api/v1/agents/external",
    tags=["External Agents"],
    responses={404: {"description": "Not found"}},
)

@router.post(
    "/register",
    response_model=EAPRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register external agent"
)
async def register_external_agent(
    request: EAPRegistrationRequest,
    service: Annotated[AgentManagementService, Depends(get_agent_service)]
):
    """
    Register a new external agent via EAP.
    Returns agent ID and authentication token.
    """
    try:
        return await service.register_external_agent(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post(
    "/{agent_id}/heartbeat",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Agent heartbeat"
)
async def agent_heartbeat(
    agent_id: UUID,
    request: EAPHeartbeatRequest,
    x_agent_token: Annotated[str, Header()],
    service: Annotated[AgentManagementService, Depends(get_agent_service)]
):
    """
    Receive heartbeat from external agent.
    Updates status, load, and metrics.
    Requires X-Agent-Token header.
    """
    # Authenticate
    is_authenticated = await service.authenticate_agent(agent_id, x_agent_token)
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent token"
        )
        
    # Process heartbeat
    success = await service.heartbeat(agent_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Update metrics/load if provided
    # Note: In a full implementation, we would update the agent's specific 
    # load metrics from the request here. For now, the heartbeat keeps it alive.
    # TODO: Map request.current_load and request.metrics to agent entity
