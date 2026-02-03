"""
DOMAIN EXCEPTIONS PACKAGE
Exports all domain-level exceptions.
"""

from .context_exceptions import (
    ContextError,
    ContextNotFoundError,
    ContextConflictError,
    ContextScopeMismatchError,
    ContextMergeError,
    ContextAccessDeniedError,
    ContextValidationError,
)

__all__ = [
    "ContextError",
    "ContextNotFoundError",
    "ContextConflictError",
    "ContextScopeMismatchError",
    "ContextMergeError",
    "ContextAccessDeniedError",
    "ContextValidationError",
]
