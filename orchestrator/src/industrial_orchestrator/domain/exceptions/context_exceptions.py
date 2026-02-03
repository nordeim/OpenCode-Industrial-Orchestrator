"""
INDUSTRIAL CONTEXT EXCEPTIONS
Domain exceptions for context management operations.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID


class ContextError(Exception):
    """Base exception for context operations."""
    
    def __init__(
        self,
        message: str,
        context_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.context_id = context_id
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception to dictionary."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context_id": str(self.context_id) if self.context_id else None,
            "details": self.details,
        }


class ContextNotFoundError(ContextError):
    """
    Raised when a context cannot be found.
    
    Industrial Guidance:
    - Check if context was garbage collected (scope TTL)
    - Verify session/agent association
    - Consider creating new context
    """
    
    def __init__(
        self,
        context_id: UUID,
        message: Optional[str] = None,
        search_criteria: Optional[Dict[str, Any]] = None
    ):
        msg = message or f"Context not found: {context_id}"
        super().__init__(
            message=msg,
            context_id=context_id,
            details={"search_criteria": search_criteria}
        )
        self.search_criteria = search_criteria


class ContextConflictError(ContextError):
    """
    Raised when context update conflicts with current version.
    
    Industrial Features:
    - Provides expected vs actual version
    - Lists conflicting keys
    - Suggests resolution actions
    
    Resolution Guidance:
    1. Reload context with current version
    2. Re-apply changes
    3. Use merge strategy for non-critical updates
    """
    
    def __init__(
        self,
        context_id: UUID,
        expected_version: int,
        actual_version: int,
        conflicting_keys: Optional[List[str]] = None,
        message: Optional[str] = None
    ):
        msg = message or (
            f"Context version conflict for {context_id}: "
            f"expected version {expected_version}, found {actual_version}"
        )
        super().__init__(
            message=msg,
            context_id=context_id,
            details={
                "expected_version": expected_version,
                "actual_version": actual_version,
                "conflicting_keys": conflicting_keys or [],
            }
        )
        self.expected_version = expected_version
        self.actual_version = actual_version
        self.conflicting_keys = conflicting_keys or []
    
    @property
    def retry_hint(self) -> str:
        """Get retry guidance."""
        return (
            f"Fetch context version {self.actual_version}, "
            "review conflicting keys, and retry with updated version"
        )


class ContextScopeMismatchError(ContextError):
    """
    Raised when context scope doesn't match expected scope.
    
    Industrial Scenarios:
    - Trying to share SESSION context as GLOBAL
    - Agent context accessed from wrong agent
    - Temporary context promoted without permission
    
    Resolution Guidance:
    1. Clone context to new scope if permitted
    2. Request scope promotion
    3. Use context with correct scope
    """
    
    def __init__(
        self,
        context_id: UUID,
        expected_scope: str,
        actual_scope: str,
        operation: Optional[str] = None,
        message: Optional[str] = None
    ):
        msg = message or (
            f"Context scope mismatch for {context_id}: "
            f"expected {expected_scope}, found {actual_scope}"
        )
        super().__init__(
            message=msg,
            context_id=context_id,
            details={
                "expected_scope": expected_scope,
                "actual_scope": actual_scope,
                "operation": operation,
            }
        )
        self.expected_scope = expected_scope
        self.actual_scope = actual_scope
        self.operation = operation
    
    @property
    def retry_hint(self) -> str:
        """Get retry guidance."""
        return f"Clone context to {self.expected_scope} scope or use context with correct scope"


class ContextMergeError(ContextError):
    """
    Raised when context merge fails.
    
    Industrial Scenarios:
    - Incompatible data types at same key
    - Circular references detected
    - Maximum merge depth exceeded
    
    Resolution Guidance:
    1. Use more aggressive merge strategy
    2. Manually resolve conflicts before merge
    3. Split contexts and merge incrementally
    """
    
    def __init__(
        self,
        source_ids: List[UUID],
        conflicting_keys: List[str],
        merge_strategy: str,
        message: Optional[str] = None
    ):
        msg = message or (
            f"Failed to merge contexts {source_ids}: "
            f"conflicts at {conflicting_keys}"
        )
        super().__init__(
            message=msg,
            details={
                "source_ids": [str(id) for id in source_ids],
                "conflicting_keys": conflicting_keys,
                "merge_strategy": merge_strategy,
            }
        )
        self.source_ids = source_ids
        self.conflicting_keys = conflicting_keys
        self.merge_strategy = merge_strategy


class ContextAccessDeniedError(ContextError):
    """
    Raised when access to context is denied.
    
    Industrial Scenarios:
    - Wrong session trying to access session-scoped context
    - Agent context accessed by different agent
    - Insufficient permissions for global context
    
    Resolution Guidance:
    1. Verify caller identity
    2. Request access from context owner
    3. Use shared/global context instead
    """
    
    def __init__(
        self,
        context_id: UUID,
        accessor_id: str,
        required_permission: str,
        message: Optional[str] = None
    ):
        msg = message or (
            f"Access denied to context {context_id} for {accessor_id}: "
            f"requires {required_permission} permission"
        )
        super().__init__(
            message=msg,
            context_id=context_id,
            details={
                "accessor_id": accessor_id,
                "required_permission": required_permission,
            }
        )
        self.accessor_id = accessor_id
        self.required_permission = required_permission


class ContextValidationError(ContextError):
    """
    Raised when context data fails validation.
    
    Industrial Scenarios:
    - Required keys missing
    - Invalid data types
    - Data exceeds size limits
    """
    
    def __init__(
        self,
        context_id: Optional[UUID],
        validation_errors: List[Dict[str, Any]],
        message: Optional[str] = None
    ):
        msg = message or f"Context validation failed: {len(validation_errors)} error(s)"
        super().__init__(
            message=msg,
            context_id=context_id,
            details={"validation_errors": validation_errors}
        )
        self.validation_errors = validation_errors
