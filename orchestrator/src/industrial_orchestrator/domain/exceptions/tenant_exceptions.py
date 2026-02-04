"""
TENANT DOMAIN EXCEPTIONS
"""

class TenantError(Exception):
    """Base exception for tenant-related errors"""
    pass

class QuotaExceededError(TenantError):
    """Raised when a tenant exceeds their resource limits"""
    def __init__(self, resource: str, limit: int):
        self.resource = resource
        self.limit = limit
        super().__init__(f"Quota exceeded for {resource}: limit is {limit}")

class TenantNotFoundError(TenantError):
    """Raised when a tenant does not exist"""
    pass
