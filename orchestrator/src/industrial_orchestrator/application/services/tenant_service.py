"""
TENANT MANAGEMENT SERVICE
Handles tenant onboarding, user management, and quota enforcement.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from ...domain.entities.tenant import Tenant
from ...domain.entities.user import User, Role
from ...application.ports.repository_ports import IndustrialRepositoryPort

logger = logging.getLogger(__name__)

class TenantService:
    """
    Industrial service for multi-tenant orchestration.
    """
    
    def __init__(
        self,
        tenant_repository: IndustrialRepositoryPort[Tenant],
        user_repository: IndustrialRepositoryPort[User]
    ):
        self._tenant_repo = tenant_repository
        self._user_repo = user_repository
        
    async def create_tenant(self, name: str, slug: str) -> Tenant:
        """Onboard a new organization"""
        tenant = Tenant(name=name, slug=slug)
        return await self._tenant_repo.save(tenant)
        
    async def add_user_to_tenant(
        self, 
        tenant_id: UUID, 
        email: str, 
        full_name: str, 
        role: Role = Role.MEMBER
    ) -> User:
        """Add a user to an existing tenant"""
        user = User(
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            role=role
        )
        return await self._user_repo.save(user)
        
    async def get_tenant_quotas(self, tenant_id: UUID) -> Dict[str, Any]:
        """Retrieve current resource limits for a tenant"""
        tenant = await self._tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant not found")
            
        return {
            "max_concurrent_sessions": tenant.max_concurrent_sessions,
            "max_tokens_per_month": tenant.max_tokens_per_month
        }
