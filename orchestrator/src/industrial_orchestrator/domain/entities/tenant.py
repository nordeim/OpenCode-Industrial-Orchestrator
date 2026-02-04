"""
TENANT ENTITY
Core entity for multi-tenant isolation and resource management.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from pydantic import Field
from .base import DomainEntity

class Tenant(DomainEntity):
    """
    Represents an organization or team using the orchestrator.
    """
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$")
    
    # Quotas
    max_concurrent_sessions: int = Field(default=10, ge=1)
    max_tokens_per_month: int = Field(default=1000000, ge=0)
    
    # Operational state
    is_active: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)
