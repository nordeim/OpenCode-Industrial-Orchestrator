"""
PROMETHEUS METRICS MIDDLEWARE

Industrial-grade metrics collection for the orchestrator API.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    multiprocess,
)
from starlette.responses import Response as StarletteResponse

# Create a custom registry (optional, for multiprocess mode)
REGISTRY = CollectorRegistry()

# ============================================================================
# METRICS DEFINITIONS
# ============================================================================

# Request metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_REQUEST_SIZE_BYTES = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000),
)

HTTP_RESPONSE_SIZE_BYTES = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000),
)

# Business metrics
ACTIVE_SESSIONS = Gauge(
    "orchestrator_active_sessions",
    "Number of currently active sessions",
)

ACTIVE_AGENTS = Gauge(
    "orchestrator_active_agents",
    "Number of currently active agents",
)

WEBSOCKET_CONNECTIONS = Gauge(
    "orchestrator_websocket_connections",
    "Number of active WebSocket connections",
)

TASKS_TOTAL = Counter(
    "orchestrator_tasks_total",
    "Total number of tasks processed",
    ["status"],
)

SESSION_DURATION_SECONDS = Histogram(
    "orchestrator_session_duration_seconds",
    "Session duration in seconds",
    ["status"],
    buckets=(60, 300, 600, 1800, 3600, 7200, 14400),
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for collecting Prometheus metrics.
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Extract endpoint (normalize path parameters)
        endpoint = self._normalize_path(request.url.path)
        method = request.method

        # Record request size
        request_size = int(request.headers.get("content-length", 0))
        HTTP_REQUEST_SIZE_BYTES.labels(method=method, endpoint=endpoint).observe(
            request_size
        )

        # Time the request
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            status = response.status_code
        except Exception:
            status = 500
            raise
        finally:
            # Record metrics
            duration = time.perf_counter() - start_time

            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=endpoint, status=status
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

        # Record response size
        response_size = int(response.headers.get("content-length", 0))
        HTTP_RESPONSE_SIZE_BYTES.labels(method=method, endpoint=endpoint).observe(
            response_size
        )

        return response

    def _normalize_path(self, path: str) -> str:
        """
        Normalize path by replacing dynamic segments with placeholders.
        E.g., /api/v1/sessions/abc123 -> /api/v1/sessions/{id}
        """
        import re

        # UUID pattern
        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{id}",
            path,
        )
        # Numeric IDs
        path = re.sub(r"/\d+", "/{id}", path)

        return path


# ============================================================================
# METRICS ENDPOINT
# ============================================================================

async def metrics_endpoint(request: Request) -> StarletteResponse:
    """
    Expose Prometheus metrics endpoint.
    """
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def update_active_sessions(count: int) -> None:
    """Update the active sessions gauge."""
    ACTIVE_SESSIONS.set(count)


def update_active_agents(count: int) -> None:
    """Update the active agents gauge."""
    ACTIVE_AGENTS.set(count)


def update_websocket_connections(count: int) -> None:
    """Update the WebSocket connections gauge."""
    WEBSOCKET_CONNECTIONS.set(count)


def record_task_completion(status: str) -> None:
    """Record a task completion."""
    TASKS_TOTAL.labels(status=status).inc()


def record_session_duration(duration_seconds: float, status: str) -> None:
    """Record a session duration."""
    SESSION_DURATION_SECONDS.labels(status=status).observe(duration_seconds)
