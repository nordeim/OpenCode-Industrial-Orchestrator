"""
MULTI-TENANCY MIDDLEWARE
Extracts tenant context from request headers and sets application context.
"""

from typing import Optional
from uuid import UUID
import logging

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from ....application.context import set_current_tenant_id

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract X-Tenant-ID header and set request-scoped context.
    """
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. Extract tenant ID from header
        tenant_id_str = request.headers.get("X-Tenant-ID")
        
        # 2. Skip for health checks or public endpoints if needed
        if request.url.path in ["/health", "/health/ready", "/health/live", "/docs", "/openapi.json"]:
            return await call_next(request)
            
        if not tenant_id_str:
            # In production, this might be a 401/403. 
            # For now, we allow empty for transition but log warning.
            logger.warning(f"Request to {request.url.path} missing X-Tenant-ID header")
            # return Response(content="Missing X-Tenant-ID", status_code=403)
            set_current_tenant_id(None)
        else:
            try:
                tenant_id = UUID(tenant_id_str)
                set_current_tenant_id(tenant_id)
            except ValueError:
                return Response(
                    content="Invalid X-Tenant-ID format", 
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        # 3. Process request
        response = await call_next(request)
        
        # 4. Cleanup (optional as contextvars are task-local)
        return response
