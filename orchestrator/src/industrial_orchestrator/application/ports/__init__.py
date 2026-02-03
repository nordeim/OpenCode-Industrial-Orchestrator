"""
APPLICATION PORTS PACKAGE
Exports all port interfaces for dependency injection.
"""

from .repository_ports import (
    IndustrialRepositoryPort,
    SessionRepositoryPort,
    AgentRepositoryPort,
    ContextRepositoryPort,
    TaskRepositoryPort,
)

from .service_ports import (
    ServiceHealth,
    ExecutionResult,
    HealthCheckResult,
    OpenCodeClientPort,
    DistributedLockPort,
    MessageBusPort,
    CachePort,
    MetricsPort,
)

__all__ = [
    # Repository Ports
    "IndustrialRepositoryPort",
    "SessionRepositoryPort",
    "AgentRepositoryPort",
    "ContextRepositoryPort",
    "TaskRepositoryPort",
    # Service Ports
    "ServiceHealth",
    "ExecutionResult",
    "HealthCheckResult",
    "OpenCodeClientPort",
    "DistributedLockPort",
    "MessageBusPort",
    "CachePort",
    "MetricsPort",
]
