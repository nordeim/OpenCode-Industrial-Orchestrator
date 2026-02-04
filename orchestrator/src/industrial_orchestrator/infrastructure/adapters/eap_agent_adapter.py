"""
INDUSTRIAL EAP AGENT ADAPTER
Infrastructure adapter for communicating with external agents via the External Agent Protocol (EAP).
"""

import logging
from typing import Optional, Dict, Any
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ...application.ports.service_ports import ExternalAgentPort
from ...application.dtos.external_agent_protocol import (
    EAPTaskAssignment,
    EAPTaskResult,
    EAPHeartbeatRequest,
    EAPStatus,
)
from ...infrastructure.exceptions.opencode_exceptions import (
    OpenCodeConnectionError,
    OpenCodeTimeoutError,
    OpenCodeAPIError,
)

logger = logging.getLogger(__name__)

class EAPAgentAdapter(ExternalAgentPort):
    """
    Adapter for External Agent Protocol (EAP) over HTTP.
    
    Features:
    1. Robust HTTP client with retries
    2. Authentication via X-Agent-Token
    3. Strict DTO validation
    4. Timeout management
    """
    
    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds
        self._client = httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={
                "User-Agent": "IndustrialOrchestrator/1.0",
                "Content-Type": "application/json",
            }
        )
    
    async def close(self):
        await self._client.aclose()
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def send_task(
        self,
        agent_id: str,
        endpoint_url: str,
        auth_token: str,
        task_assignment: EAPTaskAssignment
    ) -> EAPTaskResult:
        """
        Send a task to an external agent via POST /task.
        """
        url = f"{endpoint_url.rstrip('/')}/task"
        headers = {"X-Agent-Token": auth_token}
        
        try:
            logger.info(f"Sending task {task_assignment.task_id} to external agent {agent_id} at {url}")
            
            response = await self._client.post(
                url,
                headers=headers,
                json=task_assignment.model_dump(mode='json'),
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return EAPTaskResult(**data)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending task to agent {agent_id}: {e.response.text}")
            raise OpenCodeAPIError(f"External agent returned error: {e.response.status_code}") from e
            
        except (httpx.ConnectError, httpx.ReadTimeout) as e:
            logger.error(f"Connection error sending task to agent {agent_id}: {str(e)}")
            raise OpenCodeConnectionError(f"Failed to connect to external agent: {str(e)}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error sending task to agent {agent_id}: {str(e)}")
            raise OpenCodeAPIError(f"Unexpected error communicating with external agent: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
    )
    async def check_health(
        self,
        agent_id: str,
        endpoint_url: str,
        auth_token: str
    ) -> EAPHeartbeatRequest:
        """
        Check health via GET /health (or equivalent).
        Note: EAP usually relies on agent PUSHING heartbeats, but this allows active probing.
        """
        url = f"{endpoint_url.rstrip('/')}/health"
        headers = {"X-Agent-Token": auth_token}
        
        try:
            response = await self._client.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return EAPHeartbeatRequest(**data)
            
        except Exception as e:
            logger.warning(f"Health check failed for agent {agent_id}: {str(e)}")
            # Return offline status instead of raising, for resilience
            return EAPHeartbeatRequest(
                status=EAPStatus.OFFLINE,
                current_load=0.0,
                metrics={"error": str(e)}
            )
