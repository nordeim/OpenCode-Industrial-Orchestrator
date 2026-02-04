"""
APPLICATION CONTEXT
Manages request-scoped data like current tenant ID.
"""

import contextvars
from uuid import UUID
from typing import Optional

# Context variable for current tenant ID
_current_tenant_id: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar(
    "current_tenant_id", default=None
)

def get_current_tenant_id() -> Optional[UUID]:
    """Get the tenant ID for the current request context."""
    return _current_tenant_id.get()

def set_current_tenant_id(tenant_id: Optional[UUID]) -> None:
    """Set the tenant ID for the current request context."""
    _current_tenant_id.set(tenant_id)
