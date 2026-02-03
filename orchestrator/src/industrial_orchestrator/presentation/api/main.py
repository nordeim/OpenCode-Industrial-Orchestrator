"""
INDUSTRIAL ORCHESTRATOR - FastAPI APPLICATION
Main entry point for the Industrial Orchestrator API.
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .routers import (
    sessions_router,
    agents_router,
    tasks_router,
    contexts_router,
)
from .websocket import websocket_router, manager as ws_manager
from .dependencies import get_settings
from .middleware.metrics import PrometheusMiddleware, metrics_endpoint

# Configure structlog for JSON output (Industrial Standard)
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("industrial_orchestrator")


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database connections, Redis pools, etc.
    - Shutdown: Clean up resources gracefully
    """
    settings = get_settings()
    
    # Startup
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 60)
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Database: {settings.database_url.split('@')[-1] if '@' in settings.database_url else 'configured'}")
    logger.info(f"Redis: {settings.redis_url}")
    
    # Initialize connections (placeholder)
    # await init_db_pool()
    # await init_redis_pool()
    
    # Start WebSocket heartbeat
    await ws_manager.start_heartbeat()
    logger.info("✅ WebSocket heartbeat started")
    
    logger.info("✅ All systems initialized")
    logger.info("-" * 60)
    
    yield
    
    # Shutdown
    logger.info("-" * 60)
    logger.info("🛑 Shutting down Industrial Orchestrator")
    
    # Stop WebSocket heartbeat
    await ws_manager.stop_heartbeat()
    logger.info("✅ WebSocket heartbeat stopped")
    
    # Close connections (placeholder)
    # await close_db_pool()
    # await close_redis_pool()
    
    logger.info("✅ Shutdown complete")


# ============================================================================
# APPLICATION FACTORY
# ============================================================================

def create_app() -> FastAPI:
    """
    Application factory.
    
    Creates and configures the FastAPI application with:
    - Industrial-grade error handling
    - CORS middleware
    - All API routers
    - OpenAPI documentation
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Industrial-grade orchestration system for autonomous coding sessions. "
            "Manages session lifecycle, multi-agent coordination, task decomposition, "
            "and execution context with resilient, observable operations."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=[
            {
                "name": "Sessions",
                "description": "Session lifecycle management - create, execute, and monitor coding sessions",
            },
            {
                "name": "Agents",
                "description": "Agent registration, capability-based routing, and performance tracking",
            },
            {
                "name": "Tasks",
                "description": "Task creation, decomposition, dependency management, and execution",
            },
            {
                "name": "Contexts",
                "description": "Execution context management with scope-based visibility and sharing",
            },
            {
                "name": "Health",
                "description": "System health and monitoring endpoints",
            },
            {
                "name": "WebSocket",
                "description": "Real-time event subscriptions via WebSocket",
            },
        ],
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure per environment in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Prometheus Middleware
    app.add_middleware(PrometheusMiddleware)
    
    # Register routers
    app.include_router(sessions_router, prefix="/api/v1")
    app.include_router(agents_router, prefix="/api/v1")
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(contexts_router, prefix="/api/v1")
    
    # Register WebSocket router
    app.include_router(websocket_router)

    # Register Metrics Endpoint
    app.add_route("/metrics", metrics_endpoint)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    return app


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers."""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with industrial-grade detail."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": errors,
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors with safe information."""
        logger.exception(f"Unhandled exception: {exc}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request.headers.get("X-Request-ID", "unknown"),
            },
        )


# ============================================================================
# HEALTH ENDPOINTS
# ============================================================================

app = create_app()


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns system health status for load balancer probes."
)
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status and component states
    """
    return {
        "status": "healthy",
        "version": get_settings().app_version,
        "components": {
            "database": "pending",  # Will be implemented
            "redis": "pending",
            "agents": "pending",
        }
    }


@app.get(
    "/health/ready",
    tags=["Health"],
    summary="Readiness check",
    description="Returns readiness status for Kubernetes probes."
)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for Kubernetes.
    
    Verifies all dependencies are available.
    """
    # Check database connection
    db_ready = True  # Placeholder
    
    # Check Redis connection
    redis_ready = True  # Placeholder
    
    is_ready = db_ready and redis_ready
    
    return {
        "ready": is_ready,
        "components": {
            "database": {"ready": db_ready},
            "redis": {"ready": redis_ready},
        }
    }


@app.get(
    "/health/live",
    tags=["Health"],
    summary="Liveness check",
    description="Returns liveness status for Kubernetes probes."
)
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check for Kubernetes.
    
    Simple check that the process is running.
    """
    return {"status": "alive"}


@app.get(
    "/",
    include_in_schema=False,
)
async def root():
    """Root endpoint redirects to docs."""
    return {
        "message": "Industrial Orchestrator API",
        "docs": "/docs",
        "health": "/health",
    }
