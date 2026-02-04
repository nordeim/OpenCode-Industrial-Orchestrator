"""
USER & ROLE ENTITIES
Defines identity and access control for multi-tenant isolation.
"""

from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import Field, EmailStr
from .base import DomainEntity

class Role(str, Enum):
    """Access control roles"""
    ADMIN = "admin"      # System-wide access
    LEAD = "lead"        # Tenant-wide management
    MEMBER = "member"    # Standard tenant access
    VIEWER = "viewer"    # Read-only access

class User(DomainEntity):
    """
    Represents an individual user within the system.
    """
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID = Field(...)
    email: EmailStr
    full_name: str
    role: Role = Field(default=Role.MEMBER)
    is_active: bool = Field(default=True)
    
    def has_permission(self, required_role: Role) -> bool:
        """Check if user has sufficient role level"""
        hierarchy = {
            Role.ADMIN: 4,
            Role.LEAD: 3,
            Role.MEMBER: 2,
            Role.VIEWER: 1
        }
        return hierarchy.get(self.role, 0) >= hierarchy.get(required_role, 0)
