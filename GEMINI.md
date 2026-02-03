# OpenCode Industrial Orchestrator

> **"Industrial Cybernetics"** — A utilitarian, transparent orchestration interface prioritizing ruthless efficiency, visibility ("Glass Box"), and graceful degradation.

This `GEMINI.md` serves as the instructional context for AI agents working on the OpenCode Industrial Orchestrator. It summarizes the project's purpose, architecture, and operational procedures.

## 1. Project Overview

The **OpenCode Industrial Orchestrator** is a production-grade system designed to manage, monitor, and orchestrate autonomous coding sessions. Unlike generic agent frameworks, this system is built on **Hexagonal Architecture (Ports & Adapters)** principles to ensure strict domain isolation, high testability, and infrastructure resilience.

### Core Objectives
*   **Resilient State Management:** 99.9% session persistence through server restarts.
*   **Multi-Agent Intelligence:** Capability-based routing and task decomposition.
*   **Distributed Coordination:** Fair locking and deadlock prevention for parallel execution.
*   **Glass Box Monitoring:** Comprehensive metrics for every transition and operation.

### Tech Stack

| Layer | Technology | Key Libraries |
|:------|:-----------|:--------------|
| **Backend** | Python 3.11+ | FastAPI, SQLAlchemy (Async), Redis, Pydantic, Structlog, Prometheus Client |
| **Frontend** | TypeScript / React | Next.js 14 (App Router), Tailwind CSS 4.0, TanStack Query, WebSocket |
| **Data** | PostgreSQL 15 | AsyncPG, Alembic |
| **Cache/Lock** | Redis 7 | Distributed Locking |
| **Infra** | Kubernetes | Helm, Docker, Prometheus, Grafana, GitHub Actions |

## 2. Architecture & Design

The system follows a strict **Hexagonal Architecture**:

*   **`domain/` (The Hexagon):** Pure business logic. Zero external dependencies. Contains Entities (`Session`, `Agent`, `Task`), Value Objects, and Domain Events.
*   **`application/` (The Ports):** Orchestration logic and use cases. Defines interfaces (`Ports`) for repositories and external services.
*   **`infrastructure/` (The Adapters):** Concrete implementations of ports. Database repositories, Redis locking, OpenCode API clients.
*   **`presentation/` (The Entry Points):** FastAPI routers, WebSocket handlers, and CLI commands.

**Crucial Rule:** Dependencies point **inward**. `infrastructure` depends on `domain`. `domain` depends on nothing.

## 3. Building and Running

### Prerequisites
*   Docker & Docker Compose
*   Python 3.11+ & Poetry (`pip install poetry`)
*   Node.js 18+ & npm

### Backend (`orchestrator/`)

```bash
# 1. Start Infrastructure (Postgres, Redis)
docker-compose up -d postgres redis opencode-server

# 2. Install Dependencies
cd orchestrator
poetry install

# 3. Run Migrations
poetry run alembic upgrade head

# 4. Start API Server
poetry run uvicorn src.industrial_orchestrator.presentation.api.main:app --reload
# Server runs at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend (`dashboard/`)

```bash
cd dashboard

# 1. Install Dependencies
npm install

# 2. Start Development Server
npm run dev
# Dashboard runs at http://localhost:3000
```

### Testing

**TDD is mandatory.** Write tests before implementation.

```bash
# Backend Tests
cd orchestrator
poetry run pytest                  # Run all tests
poetry run pytest tests/unit       # Run unit tests (fast)
poetry run pytest tests/integration # Run integration tests (requires DB/Redis)

# Frontend Linting
cd dashboard
npm run lint
```

## 4. Operational Procedures

### Phase Completion Status
*   **Phase 2.1: Foundation & Core:** ✅ Complete
*   **Phase 2.2: Multi-Agent Intelligence:** ✅ Complete
*   **Phase 2.3: Dashboard & Visualization:** ✅ Complete
*   **Phase 2.4: Production Hardening:** ✅ Complete

### Code Style & Quality
*   **Python:** Strict adherence to `black`, `isort`, and `flake8`. All code must be typed (`mypy`).
*   **Logging:** Use `structlog` for structured JSON logging. Do not use standard `logging`.
*   **Metrics:** Register metrics via `PrometheusMiddleware` in `presentation/api/middleware/metrics.py`.

### Deployment
*   **CI/CD:** GitHub Actions workflows (`.github/workflows/`) handle testing, linting, and multi-stage deployment (Staging -> Production).
*   **Kubernetes:** Manifests located in `infrastructure/kubernetes/`. Use `kustomize` for environment overlays.
*   **Observability:** Prometheus metrics exposed at `/metrics`. Grafana dashboard template at `infrastructure/monitoring/grafana/dashboards/orchestrator.json`.

## 5. Directory Map

*   `orchestrator/`: Python backend application.
*   `dashboard/`: Next.js frontend application.
*   `infrastructure/`: Kubernetes manifests, Docker configs, and monitoring setups.
*   `docs/`: Architecture Decision Records (ADRs) and API documentation.
*   `.github/`: CI/CD workflow definitions.
