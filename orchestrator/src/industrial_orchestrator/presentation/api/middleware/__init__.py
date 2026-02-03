"""
Middleware package for the Industrial Orchestrator API.
"""

from .metrics import (
    PrometheusMiddleware,
    metrics_endpoint,
    update_active_sessions,
    update_active_agents,
    update_websocket_connections,
    record_task_completion,
    record_session_duration,
)

__all__ = [
    "PrometheusMiddleware",
    "metrics_endpoint",
    "update_active_sessions",
    "update_active_agents",
    "update_websocket_connections",
    "record_task_completion",
    "record_session_duration",
]
