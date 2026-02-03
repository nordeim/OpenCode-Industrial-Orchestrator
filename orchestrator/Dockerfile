# ============================================================================
# INDUSTRIAL ORCHESTRATOR — PRODUCTION DOCKERFILE
# Multi-stage build optimized for production deployment
# ============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder — Install dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Industrial labeling
LABEL maintainer="Industrial Orchestrator Team"
LABEL stage="builder"

# Set build-time environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /build

# Copy dependency files first (layer caching)
COPY pyproject.toml poetry.lock* ./

# Install production dependencies only (no dev deps)
RUN poetry install --no-root --only main && \
    rm -rf /root/.cache/pypoetry

# Copy source code
COPY src/ ./src/

# -----------------------------------------------------------------------------
# Stage 2: Runtime — Minimal production image
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Industrial labeling
LABEL maintainer="Industrial Orchestrator Team"
LABEL version="1.0.0"
LABEL description="Industrial-grade OpenCode Orchestrator"

# Runtime environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    APP_ENV=production \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 industrial && \
    useradd --uid 1000 --gid industrial --shell /bin/bash --create-home industrial

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

# Copy source code
COPY --from=builder /build/src /app/src

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R industrial:industrial /app

# Switch to non-root user
USER industrial

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production entrypoint
ENTRYPOINT ["python", "-m", "uvicorn"]

# Default command with production settings
CMD ["src.industrial_orchestrator.presentation.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools"]
