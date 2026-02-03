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

### 🔄 Phase 2.2: Multi-Agent Intelligence Layer (In Progress)
Implementing the "brain" of the orchestrator to handle complex task delegation.
*   **Agent Specialization:** Defined `AgentEntity` with capability-based routing and performance tracking (`AgentPerformanceMetrics`).
*   **Task Decomposition:** Implemented `TaskEntity` with recursive subtasking and `TaskDecompositionService` for breaking down complex requirements using templates (Microservice, CRUD, Security) and heuristics.

## Tech Stack

### Backend (`/orchestrator`)
*   **Language:** Python 3.11+
*   **Framework:** FastAPI (`uvicorn`)
*   **Database:** PostgreSQL 15 (AsyncPG + SQLAlchemy 2.0)
*   **Caching & Locking:** Redis 7
*   **Dependency Management:** Poetry
*   **Migrations:** Alembic
*   **Testing:** Pytest, Factory Boy, Tenacity

### Frontend (Planned - `/dashboard`)
*   **Framework:** Next.js 14 (App Router)
*   **Styling:** Tailwind CSS 4.0
*   **UI Components:** Shadcn UI (customized for Brutalist aesthetic)

### Infrastructure
*   **Containerization:** Docker & Docker Compose
*   **Monitoring:** Prometheus & Grafana (Planned/In-progress)

## Architecture

The backend follows a strict **Hexagonal Architecture**:

*   **`domain/`**: Pure business logic.
    *   **Entities:** `SessionEntity`, `AgentEntity`, `TaskEntity`.
    *   **Value Objects:** `SessionStatus`, `AgentCapability`, `TaskComplexity`.
    *   **Events:** Domain events for state changes.
*   **`application/`**: Orchestration logic.
    *   **Services:** `SessionService` (Lifecycle), `TaskDecompositionService` (Planning).
*   **`infrastructure/`**: Adapters and implementations.
    *   **Persistence:** `SessionRepository` (PostgreSQL).
    *   **Locking:** `IndustrialDistributedLock` (Redis).
    *   **External:** `IndustrialOpenCodeClient`.
*   **`presentation/`**: Entry points (API, CLI).

## Building and Running

### Prerequisites
*   Docker & Docker Compose
*   Python 3.11+
*   Poetry (`pip install poetry`)

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
    poetry run pytest
    ```

## Development Conventions

*   **Code Style:** Strict adherence to `black`, `isort`, and `flake8` for Python.
*   **Testing:** **TDD (Test-Driven Development)** is mandatory. Write tests *before* implementation. Use the provided Factory factories (`tests/unit/domain/factories`) for test data.
*   **Database:** Use **Alembic** for all schema changes. Never modify the database schema manually.
*   **Imports:** Follow the hexagonal dependency rule: Inner layers (Domain) *never* import from outer layers (Infrastructure/Presentation).

## Key Directories

*   `orchestrator/src/industrial_orchestrator/domain/`: Core business entities (Session, Agent, Task).
*   `orchestrator/src/industrial_orchestrator/application/services/`: Business logic services.
*   `orchestrator/src/industrial_orchestrator/infrastructure/`: Repositories and adapters.
*   `infrastructure/`: Docker and monitoring configuration.
*   `docs/`: Documentation and Architecture Decision Records (ADRs).