# OpenCode Industrial Orchestrator

## Project Overview

The **OpenCode Industrial Orchestrator** is a sophisticated, industrial-grade system designed to manage and orchestrate autonomous coding sessions. It leverages a **Hexagonal Architecture** (Ports & Adapters) to ensure domain isolation, testability, and resilience.

**Design Philosophy:** "Industrial Cybernetics" — A utilitarian, transparent orchestration interface that prioritizes ruthless efficiency, visibility ("Glass Box"), and graceful degradation.
**Aesthetic:** "Brutalist Minimalism" — Raw elements, stark contrasts, and utilitarian typography.

## Progress & Status

### ✅ Phase 2.1: Foundation & Core Orchestrator (Completed)
Established the robust backbone of the system with strict adherence to industrial standards.
*   **Domain Layer:** Implemented `SessionEntity` with state machine validation, `SessionStatus` and `ExecutionMetrics` value objects.
*   **Infrastructure:**
    *   **PostgreSQL:** Schema designed with Alembic migrations, soft deletion, and optimistic locking.
    *   **Redis:** Distributed locking with fair queuing, circuit breakers, and connection pooling.
    *   **OpenCode API:** Resilient client adapter with retry logic and rate limiting.
    *   **Repositories:** Unit of Work pattern implemented for `SessionRepository`.
*   **Application Layer:** `SessionService` orchestrates session lifecycles, integrating persistence and distributed locking.
*   **Quality Assurance:** TDD workflow established with comprehensive unit and integration tests (Pytest + Factory Boy).

### ✅ Phase 2.2: Multi-Agent Intelligence Layer (Completed)
Implemented the "brain" of the orchestrator to handle complex task delegation.
*   **Agent Specialization:** Defined `AgentEntity` with capability-based routing, performance tracking (`AgentPerformanceMetrics`), and load balancing.
*   **Agent Registry:** `AgentRegistry` for dynamic agent registration, discovery, and capability-based indexing.
*   **Task Decomposition:** Implemented `TaskEntity` with recursive subtasking and `TaskDecompositionService` for breaking down complex requirements using templates (Microservice, CRUD, Security) and heuristics.
*   **Context Management:** `ContextEntity` for execution context sharing between sessions/agents with scope-based access control and conflict detection.
*   **Application Services:**
    *   `AgentManagementService` — Agent lifecycle and capability routing
    *   `ContextService` — Context creation, sharing, and lifecycle
*   **API Layer:** FastAPI routers for Sessions, Agents, Tasks, and Contexts with request validation and DTOs.
*   **WebSocket Support:** Real-time session event broadcasting via `ConnectionManager`.
*   **Unit Tests:** 212 passing tests covering domain entities and application services.

### 🔄 Phase 2.3: Dashboard & Visualization (In Progress)
Building the "Glass Box" interface for real-time monitoring.
*   **Next.js Frontend:** Initialized in `/dashboard` with Tailwind CSS.
*   **WebSocket Backend:** Connection manager and session events implemented.
*   **Remaining:** Dashboard UI components (Session Monitor, Task Graph, Agent Status).

### 🔲 Phase 2.4: Production Hardening (Planned)
*   Kubernetes manifests and Helm charts
*   CI/CD pipelines (GitHub Actions)
*   Prometheus/Grafana monitoring dashboards

## Tech Stack

### Backend (`/orchestrator`)
*   **Language:** Python 3.11+
*   **Framework:** FastAPI (`uvicorn`)
*   **Database:** PostgreSQL 15 (AsyncPG + SQLAlchemy 2.0)
*   **Caching & Locking:** Redis 7
*   **Dependency Management:** Poetry
*   **Migrations:** Alembic
*   **Testing:** Pytest, Factory Boy, Tenacity

### Frontend (`/dashboard`)
*   **Framework:** Next.js 14 (App Router)
*   **Styling:** Tailwind CSS 4.0
*   **UI Components:** Shadcn UI (customized for Brutalist aesthetic)

### Infrastructure
*   **Containerization:** Docker & Docker Compose
*   **Monitoring:** Prometheus & Grafana (Planned)

## Architecture

The backend follows a strict **Hexagonal Architecture**:

*   **`domain/`**: Pure business logic.
    *   **Entities:** `SessionEntity`, `AgentEntity`, `TaskEntity`, `ContextEntity`, `AgentRegistry`.
    *   **Value Objects:** `SessionStatus`, `AgentCapability`, `TaskComplexity`, `ContextScope`.
    *   **Events:** Domain events for state changes.
*   **`application/`**: Orchestration logic.
    *   **Services:** `SessionService` (Lifecycle), `AgentManagementService` (Agents), `ContextService` (Context), `TaskDecompositionService` (Planning).
    *   **Ports:** Abstract interfaces for dependency injection.
    *   **DTOs:** Request/Response data transfer objects.
*   **`infrastructure/`**: Adapters and implementations.
    *   **Persistence:** `SessionRepository` (PostgreSQL), `RedisAgentRepository` (Redis).
    *   **Locking:** `IndustrialDistributedLock` (Redis).
    *   **External:** `IndustrialOpenCodeClient`.
*   **`presentation/`**: Entry points (API, WebSocket, CLI).
    *   **Routers:** /api/v1/sessions, /api/v1/agents, /api/v1/tasks, /api/v1/contexts
    *   **WebSocket:** /ws/sessions for real-time updates

## Building and Running

### Prerequisites
*   Docker & Docker Compose
*   Python 3.11+
*   Poetry (`pip install poetry`)
*   Node.js 18+ (for dashboard)

### Development Environment

1.  **Start Infrastructure:**
    ```bash
    docker-compose up -d postgres redis opencode-server
    ```

2.  **Install Backend Dependencies:**
    ```bash
    cd orchestrator
    poetry install
    ```

3.  **Run Migrations:**
    ```bash
    cd orchestrator
    poetry run alembic upgrade head
    ```

4.  **Run Backend API:**
    ```bash
    cd orchestrator
    poetry run uvicorn src.industrial_orchestrator.presentation.api.main:app --reload
    ```

5.  **Run Tests:**
    ```bash
    cd orchestrator
    poetry run pytest  # 212 tests
    ```

6.  **Run Dashboard (Frontend):**
    ```bash
    cd dashboard
    npm install
    npm run dev
    ```

## Development Conventions

*   **Code Style:** Strict adherence to `black`, `isort`, and `flake8` for Python.
*   **Testing:** **TDD (Test-Driven Development)** is mandatory. Write tests *before* implementation. Use the provided Factory factories (`tests/unit/domain/factories`) for test data.
*   **Database:** Use **Alembic** for all schema changes. Never modify the database schema manually.
*   **Imports:** Follow the hexagonal dependency rule: Inner layers (Domain) *never* import from outer layers (Infrastructure/Presentation).

## Key Directories

*   `orchestrator/src/industrial_orchestrator/domain/`: Core business entities (Session, Agent, Task, Context, Registry).
*   `orchestrator/src/industrial_orchestrator/application/services/`: Business logic services (Session, Agent, Context, Task).
*   `orchestrator/src/industrial_orchestrator/infrastructure/`: Repositories and adapters.
*   `orchestrator/src/industrial_orchestrator/presentation/api/`: FastAPI routers and WebSocket handlers.
*   `orchestrator/tests/unit/`: 212 comprehensive unit tests.
*   `dashboard/`: Next.js frontend application.
*   `infrastructure/`: Docker and monitoring configuration.
*   `docs/`: Documentation and Architecture Decision Records (ADRs).