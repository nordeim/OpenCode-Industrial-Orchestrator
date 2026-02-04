# OpenCode Industrial Orchestrator - Project Context

## Project Overview

The **OpenCode Industrial Orchestrator** is a production-grade system designed to manage, monitor, and orchestrate autonomous coding sessions. It serves as a "control plane" for AI agents, providing state management, task decomposition, and real-time observability ("Glass Box" monitoring).

**Key Philosophy:** "Industrial Cybernetics" — Prioritizing efficiency, visibility, and graceful degradation.

### Architecture
The system follows a strict **Hexagonal Architecture (Ports & Adapters)** to ensure isolation of the core domain logic from infrastructure concerns.

*   **Domain (`domain/`)**: Pure business logic (Entities, Value Objects, Events). Zero external dependencies.
*   **Application (`application/`)**: Orchestration logic (Services, Use Cases).
*   **Infrastructure (`infrastructure/`)**: Adapters for databases (PostgreSQL), caching (Redis), and external APIs.
*   **Presentation (`presentation/`)**: Entry points (FastAPI routers, WebSocket handlers).

### Technology Stack
*   **Backend**: Python 3.11+, FastAPI, Uvicorn.
*   **Data**: PostgreSQL 15 (AsyncPG + SQLAlchemy 2.0), Redis 7.
*   **Frontend**: Next.js 16, Tailwind CSS 4.0, shadcn/ui.
*   **Infrastructure**: Docker, Kubernetes, Helm, Prometheus, Grafana.
*   **Testing**: Pytest, Factory Boy.

---

## Building and Running

### Prerequisites
*   Docker & Docker Compose
*   Python 3.11+ & Poetry
*   Node.js 18.17+ & npm

### Infrastructure
Start the required services (PostgreSQL, Redis, OpenCode Mock Server):
```bash
docker-compose up -d postgres redis opencode-server
```

### Backend (`orchestrator/`)
1.  **Install Dependencies:**
    ```bash
    cd orchestrator
    poetry install
    ```
2.  **Run Migrations:**
    ```bash
    poetry run alembic upgrade head
    ```
3.  **Start API Server:**
    ```bash
    poetry run uvicorn src.industrial_orchestrator.presentation.api.main:app --reload
    ```
    *   API Docs: `http://localhost:8000/docs`
    *   Health Check: `http://localhost:8000/health`

### Frontend (`dashboard/`)
1.  **Install Dependencies:**
    ```bash
    cd dashboard
    npm install
    ```
2.  **Start Development Server:**
    ```bash
    npm run dev
    ```
    *   Dashboard: `http://localhost:3000`
3.  **Production Build:**
    *   **Note:** Keep `NODE_ENV` commented out in `.env` to avoid build conflicts.
    ```bash
    export NODE_ENV=production
    npm run build
    ```

---

## Testing & Quality

**Test-Driven Development (TDD) is mandatory.**

### Backend Tests
The project has a comprehensive test suite (321+ tests) covering unit and integration scenarios.

*   **Run All Tests:**
    ```bash
    cd orchestrator
    poetry run pytest
    ```
*   **Run Unit Tests Only:**
    ```bash
    poetry run pytest tests/unit
    ```
*   **Run Integration Tests:**
    ```bash
    poetry run pytest tests/integration
    ```

### Code Style
*   **Python:** Adheres to `black`, `isort`, and `flake8` standards. Checked via CI.
*   **Frontend:** Standard ESLint + Prettier configuration.

---

## Development Conventions

1.  **Hexagonal Rules:**
    *   **Dependencies point inward.** Domain layer must NEVER import from Application or Infrastructure.
    *   Infrastructure adapters implement interfaces defined in Application ports.
2.  **Pydantic V2:** Use `ConfigDict` and `@field_validator` (V2 style). Avoid deprecated V1 methods.
3.  **Naming:**
    *   Sessions: `IND-*`
    *   Agents: `AGENT-*`
4.  **State Management:** Strict state machine enforcement for Sessions and Tasks (12 states).

---

## Status & Roadmap

**Current Status:** Phase 2.4 (Production Hardening) is **COMPLETE**. The core system is production-ready.

**Next Steps (Phase 3.0):**
1.  **Agent Marketplace:** External agent integration (JSON/gRPC).
2.  **LLM Fine-Tuning:** Feedback loops for model improvement.
3.  **Multi-Tenancy:** RBAC and tenant isolation.
