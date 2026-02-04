# OpenCode Industrial Orchestrator — Agent Briefing Document

> **Single Source of Truth** for AI coding agents and human developers working on the OpenCode Industrial Orchestrator.  
> **Last Updated:** February 4, 2026  
> **Status:** Phase 2.4 Complete — Production Ready

---

## 1. Project Overview

The **OpenCode Industrial Orchestrator** is a production-grade system designed to manage, monitor, and orchestrate autonomous coding sessions. It serves as a "control plane" for AI agents, providing state management, task decomposition, and real-time observability ("Glass Box" monitoring).

**Core Philosophy:** "Industrial Cybernetics" — Prioritizing efficiency, visibility, and graceful degradation.

### Key Capabilities

| Feature | Description |
|:--------|:------------|
| **Multi-Agent Intelligence** | Dynamic agent registration with capability-based routing and load balancing |
| **Task Decomposition** | Intelligent task breakdown using templates (Microservice, CRUD, Security) |
| **Context Management** | Shared execution context with conflict detection and version control |
| **Distributed Locking** | Redis-based fair locking for parallel session coordination |
| **Glass Box Monitoring** | Real-time WebSocket updates, Prometheus metrics, structured JSON logging |

### Current Status

| Phase | Description | Status | Tests |
|:------|:------------|:------:|:------|
| 2.1 | Foundation & Core Orchestrator | ✅ Complete | — |
| 2.2 | Multi-Agent Intelligence | ✅ Complete | 212 |
| 2.3 | Dashboard & Visualization | ✅ Complete | — |
| 2.4 | Production Hardening | ✅ Complete | 109 |
| **Total** | | | **321** |

---

## 2. Technology Stack

### Backend (Orchestrator)

| Layer | Technology | Version |
|:------|:-----------|:--------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.104.1 |
| Server | Uvicorn | 0.24.0 |
| ORM | SQLAlchemy | 2.0.23 |
| Database Driver | AsyncPG | 0.29.0 |
| Cache/Lock | Redis | 5.0.1 |
| Validation | Pydantic | 2.5.0 |
| Migrations | Alembic | 1.12.1 |
| Auth | python-jose + passlib | 3.3.0 / 1.7.4 |
| Logging | structlog | 24.1.0 |
| Metrics | prometheus-client | 0.19.0 |
| HTTP Client | httpx | 0.25.1 |
| Retry Logic | tenacity | 8.2.3 |
| Graph Processing | networkx | 3.2+ |

### Frontend (Dashboard)

| Layer | Technology | Version |
|:------|:-----------|:--------|
| Framework | Next.js | 16.1.6 |
| Language | TypeScript | 5.x |
| React | React | 19.2.3 |
| Styling | Tailwind CSS | 4.x |
| CSS Processing | @tailwindcss/postcss | 4.x |
| Data Fetching | TanStack Query | 5.90.20 |
| Linting | ESLint | 9.x |

### Infrastructure

| Service | Technology |
|:--------|:-----------|
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Container | Docker & Docker Compose |
| Orchestration | Kubernetes |
| Monitoring | Prometheus + Grafana |
| CI/CD | GitHub Actions |

---

## 3. Architecture

### Hexagonal Architecture (Ports & Adapters)

The system strictly follows Hexagonal Architecture with clear dependency direction:

```
┌─────────────────────────────────────────────────────────────────┐
│  Presentation Layer (API, WebSocket, CLI)                       │
│  ├── FastAPI routers (sessions, agents, tasks, contexts)        │
│  ├── WebSocket connection manager                               │
│  └── Middleware (CORS, metrics, error handling)                 │
├─────────────────────────────────────────────────────────────────┤
│  Application Layer (Services)                                   │
│  ├── SessionService — Session lifecycle management              │
│  ├── AgentManagementService — Registration & routing            │
│  ├── TaskDecompositionService — Task breakdown & templates      │
│  └── ContextService — Context creation & sharing                │
├─────────────────────────────────────────────────────────────────┤
│  Domain Layer (Pure Business Logic)                             │
│  ├── Entities: SessionEntity, AgentEntity, TaskEntity, Context  │
│  ├── Value Objects: SessionStatus, ExecutionMetrics             │
│  ├── Events: SessionCreated, SessionStatusChanged               │
│  └── Exceptions: Domain-specific errors                         │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure Layer (Adapters)                                │
│  ├── Repositories: PostgreSQL (sessions), Redis (agents)        │
│  ├── Locking: Redis-based distributed locks                     │
│  └── Adapters: OpenCode client with circuit breaker             │
└─────────────────────────────────────────────────────────────────┘
```

**Critical Rule:** Dependencies point INWARD only. Domain layer NEVER imports from Application or Infrastructure.

### Project Structure

```
opencode-industrial-orchestrator/
├── orchestrator/                     # Python Backend
│   ├── src/industrial_orchestrator/
│   │   ├── domain/                   # 🧠 Pure business logic
│   │   │   ├── entities/             # Session, Agent, Task, Context, Registry
│   │   │   ├── value_objects/        # SessionStatus, ExecutionMetrics
│   │   │   ├── events/               # Domain events
│   │   │   └── exceptions/           # Domain errors
│   │   ├── application/              # ⚙️ Orchestration services
│   │   │   ├── services/             # Session, Agent, Context, Task services
│   │   │   ├── ports/                # Repository & service interfaces (ABCs)
│   │   │   └── dtos/                 # Request/Response DTOs
│   │   ├── infrastructure/           # 🔌 Adapters
│   │   │   ├── repositories/         # PostgreSQL, Redis storage
│   │   │   ├── locking/              # Distributed locks
│   │   │   ├── adapters/             # OpenCode client
│   │   │   ├── database/             # SQLAlchemy models
│   │   │   └── config/               # Database & Redis config
│   │   └── presentation/             # 🖥️ Entry points
│   │       ├── api/                  # FastAPI app, routers, middleware
│   │       └── websocket/            # WebSocket handlers
│   ├── tests/                        # 321 tests (unit/integration/acceptance)
│   ├── alembic/                      # Database migrations
│   ├── pyproject.toml                # Poetry dependencies
│   └── Dockerfile                    # Multi-stage production build
│
├── dashboard/                        # Next.js Frontend
│   ├── src/
│   │   ├── app/                      # Next.js App Router
│   │   │   ├── page.tsx              # Dashboard home
│   │   │   ├── sessions/             # Session list & detail
│   │   │   ├── agents/               # Agent registry view
│   │   │   ├── tasks/                # Task management
│   │   │   ├── layout.tsx            # Root layout
│   │   │   └── globals.css           # Tailwind v4 configuration
│   │   ├── components/               # React components
│   │   │   ├── ui/                   # Reusable UI components
│   │   │   ├── layout/               # Layout components (sidebar)
│   │   │   └── session/              # Session-specific components
│   │   └── lib/                      # Utilities & API clients
│   │       ├── api/                  # REST API clients
│   │       └── websocket/            # WebSocket provider
│   ├── package.json
│   └── Dockerfile
│
├── infrastructure/                   # Kubernetes & Monitoring
│   ├── kubernetes/                   # K8s manifests
│   └── monitoring/                   # Prometheus & Grafana configs
│
├── docker-compose.yml                # Minimal infra (postgres, redis, opencode)
├── docker-compose.dev.yml            # Full dev environment with monitoring
└── .github/workflows/                # CI/CD pipelines
    ├── ci.yaml                       # Lint, test, build
    └── cd.yaml                       # Deploy
```

---

## 4. Build & Development Commands

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Poetry (`pip install poetry`)
- Node.js 18.17+ & npm

### Infrastructure Setup

```bash
# Start core infrastructure (PostgreSQL, Redis, OpenCode server)
docker-compose up -d postgres redis opencode-server

# Start full development environment (includes monitoring)
docker-compose -f docker-compose.dev.yml up -d
```

### Backend (Orchestrator)

```bash
cd orchestrator

# Install dependencies
poetry install

# Run database migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn src.industrial_orchestrator.presentation.api.main:app --reload

# API will be available at:
# - API Docs: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
# - Metrics: http://localhost:8000/metrics
```

### Frontend (Dashboard)

```bash
cd dashboard

# Install dependencies
npm install

# Start development server
npm run dev

# Dashboard will be available at:
# - http://localhost:3000

# Production build
# Note: Keep NODE_ENV commented out in .env to avoid build conflicts
export NODE_ENV=production
npm run build
```

---

## 5. Testing

**Test-Driven Development (TDD) is mandatory.**

### Test Structure

```
tests/
├── unit/                    # Fast, isolated tests with mocked dependencies
│   ├── domain/             # Entity tests (Session, Agent, Task, Context)
│   │   └── factories/      # Factory Boy factories for test data
│   └── application/        # Service tests with mock repositories
│       └── mocks/          # Mock ports and repositories
├── integration/            # Tests with real PostgreSQL & Redis
│   ├── repositories/       # Repository integration tests
│   ├── infrastructure/     # Database & Redis integration
│   └── locking/            # Distributed lock tests
└── acceptance/             # End-to-end API tests
```

### Running Tests

```bash
cd orchestrator

# Run all tests
poetry run pytest

# Run unit tests only
poetry run pytest tests/unit -v

# Run integration tests
poetry run pytest tests/integration -v

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/unit/domain/test_session_entity.py -v
```

### Test Coverage Summary

| Component | Tests |
|:----------|------:|
| Session Entity | 42 |
| Agent Entity | 54 |
| Task Entity | 53 |
| Context Entity | 39 |
| Task Decomposition Service | 24 |
| Integration & Infrastructure | ~109 |
| **Total** | **321** |

### Test Factories

Use Factory Boy for test data generation:

```python
from tests.unit.domain.factories.session_factory import (
    SessionEntityFactory,
    create_session_with_dependencies,
)

# Create a session
session = SessionEntityFactory()

# Create with specific attributes
session = SessionEntityFactory(title="IND-Test-001", status=SessionStatus.RUNNING)
```

---

## 6. Code Style Guidelines

### Python (Backend)

**Tools:** `black`, `isort`, `flake8`, `mypy`

```bash
# Format code
poetry run black .
poetry run isort .

# Lint
poetry run flake8 src tests

# Type check
poetry run mypy src
```

**Key Conventions:**

1. **Hexagonal Import Rules:**
   ```python
   # ✅ CORRECT: Domain never imports from Infrastructure
   from domain.entities.session import SessionEntity
   from application.services.session_service import SessionService
   
   # ❌ WRONG: Domain importing from outside
   from infrastructure.repositories.session_repository import SessionRepository  # NEVER
   ```

2. **Pydantic V2 Style:**
   ```python
   from pydantic import BaseModel, Field, field_validator, ConfigDict
   
   class MyEntity(BaseModel):
       model_config = ConfigDict(validate_assignment=True)
       
       @field_validator('field_name')
       @classmethod
       def validate_field(cls, v: str) -> str:
           return v.strip()
   ```

3. **Naming Conventions:**
   - Sessions: `IND-*` pattern (e.g., `IND-Session-001`)
   - Agents: `AGENT-*` pattern (e.g., `AGENT-ARCHITECT-001`)
   - Entities: PascalCase (e.g., `SessionEntity`)
   - Services: PascalCase + Service suffix (e.g., `SessionService`)

4. **State Management:**
   ```python
   # Use validated state transitions
   session.transition_to(SessionStatus.RUNNING)
   
   # Never set status directly
   session.status = SessionStatus.RUNNING  # ❌ Wrong
   ```

### TypeScript (Frontend)

**Tools:** ESLint, TypeScript strict mode

```bash
cd dashboard

# Lint
npm run lint

# Type check
npx tsc --noEmit
```

**Key Conventions:**

1. **Prefer `interface` over `type`** (except unions/intersections):
   ```typescript
   // ✅ Preferred
   interface Session {
     id: string;
     title: string;
   }
   
   // For unions
   type Status = 'pending' | 'running' | 'completed';
   ```

2. **No `any` — use `unknown` instead:**
   ```typescript
   // ✅ Correct
   function process(data: unknown): void {
     if (typeof data === 'string') {
       // ...
     }
   }
   ```

3. **Tailwind CSS v4:**
   ```css
   /* globals.css - CSS-first configuration */
   @import "tailwindcss";
   
   @theme {
     --color-brand-500: oklch(0.84 0.18 117.33);
   }
   ```

---

## 7. Database & Migrations

### Alembic Commands

```bash
cd orchestrator

# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Run migrations
poetry run alembic upgrade head

# Downgrade
poetry run alembic downgrade -1

# View current version
poetry run alembic current
```

### Database Configuration

Environment variables (from `.env`):

```bash
DB_HOST=postgres
DB_PORT=5432
DB_NAME=orchestration
DB_USER=cybernetics
DB_PASSWORD=industrial_secure_001
```

Connection string format:
```
postgresql://cybernetics:industrial_secure_001@postgres:5432/orchestration
```

---

## 8. API Reference

### REST Endpoints

```
Sessions:
  POST   /api/v1/sessions              Create session
  GET    /api/v1/sessions              List sessions (paginated)
  GET    /api/v1/sessions/{id}         Get session details
  POST   /api/v1/sessions/{id}/start   Start execution
  POST   /api/v1/sessions/{id}/complete Mark complete
  POST   /api/v1/sessions/{id}/fail    Mark failed
  DELETE /api/v1/sessions/{id}         Soft delete

Agents:
  POST   /api/v1/agents                Register agent
  GET    /api/v1/agents                List agents
  GET    /api/v1/agents/{id}           Get agent details
  DELETE /api/v1/agents/{id}           Deregister
  POST   /api/v1/agents/route          Route task to best agent
  POST   /api/v1/agents/{id}/heartbeat Keep-alive

Tasks:
  POST   /api/v1/tasks                 Create task
  GET    /api/v1/tasks/{id}            Get task details
  POST   /api/v1/tasks/{id}/decompose  Decompose into subtasks
  GET    /api/v1/tasks/{id}/dependencies Get dependency graph

Contexts:
  POST   /api/v1/contexts              Create context
  GET    /api/v1/contexts/{id}         Get context
  PATCH  /api/v1/contexts/{id}         Update context
  POST   /api/v1/contexts/merge        Merge contexts

Health:
  GET    /health                       Health check
  GET    /health/ready                 Readiness (DB + Redis)
  GET    /health/live                  Liveness
  GET    /metrics                      Prometheus metrics
```

### WebSocket Endpoints

```
WS     /ws/sessions                  All session events
WS     /ws/sessions/{id}             Specific session events
```

---

## 9. Domain Entities

### SessionEntity

**States:** PENDING → QUEUED → RUNNING → COMPLETED

```
Valid Transitions:
  PENDING → RUNNING, QUEUED, CANCELLED
  QUEUED → RUNNING, CANCELLED
  RUNNING → COMPLETED, FAILED, PAUSED, TIMEOUT
  PAUSED → RUNNING, CANCELLED
  FAILED → PENDING (retry)
```

**Key Methods:**
- `transition_to(new_status)` — Validated state transition
- `start_execution()` — PENDING → RUNNING
- `complete_with_result(result)` — Mark complete
- `fail_with_error(error)` — Mark failed with context
- `add_checkpoint(data)` — Save recovery point
- `calculate_health_score()` → float (0.0 to 1.0)

### AgentEntity

**Types:** `ARCHITECT`, `IMPLEMENTER`, `REVIEWER`, `DEBUGGER`, `INTEGRATOR`, `ORCHESTRATOR`, `ANALYST`, `OPTIMIZER`

**Capabilities:** `REQUIREMENTS_ANALYSIS`, `SYSTEM_DESIGN`, `CODE_GENERATION`, `CODE_REVIEW`, `DEBUGGING`, `TESTING`, `DOCUMENTATION`, `SECURITY_AUDIT`, etc.

### TaskEntity

**Key Methods:**
- `decompose(strategy, max_depth)` — Break into subtasks
- `add_dependency(task_id, type)` — Add dependency
- `get_dependency_graph()` → NetworkX DiGraph
- `can_start()` → bool (dependencies satisfied?)

---

## 10. CI/CD Pipeline

### GitHub Actions Workflows

**CI Pipeline (`.github/workflows/ci.yaml`):**

1. **Lint Backend:** black, isort, flake8, mypy
2. **Lint Frontend:** ESLint, TypeScript check
3. **Test Backend:** Unit + Integration tests with coverage
4. **Build Docker Images:** Multi-stage builds for API and Dashboard

**CD Pipeline (`.github/workflows/cd.yaml`):**

- Deploy to Kubernetes cluster
- Rolling updates with health checks

### Docker Images

```bash
# Build API image
docker build -t orchestrator-api ./orchestrator

# Build Dashboard image
docker build -t orchestrator-dashboard ./dashboard
```

---

## 11. Configuration & Environment

### Environment Variables (`.env`)

```bash
# Application
NODE_ENV=development
PYTHONPATH=/app
LOG_LEVEL=INFO
DEBUG=true

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=orchestration
DB_USER=cybernetics
DB_PASSWORD=industrial_secure_001

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# OpenCode Server
OPENCODE_HOST=opencode-server
OPENCODE_PORT=4096
OPENCODE_PASSWORD=industrial_secure

# Orchestrator Settings
MAX_CONCURRENT_SESSIONS=25
SESSION_TIMEOUT_SECONDS=3600
CHECKPOINT_INTERVAL_SECONDS=300
MAX_RETRY_ATTEMPTS=3

# Security
JWT_SECRET_KEY=industrial_cybernetics_secret_key_001
ENCRYPTION_KEY=32_byte_secure_key_for_aes_256
```

---

## 12. Known Issues & Gotchas

### Python

1. **Pydantic V2 Validators:** Use `@field_validator` (not `@validator`)
2. **State Transitions:** PENDING → RUNNING is valid for immediate execution
3. **Checkpoint Sequence:** Increments from last checkpoint, not list length
4. **Factory Faker:** Use `random.choice()` not `factory.Faker().generate()` in hooks

### Frontend

1. **Tailwind v4:** Uses `@import "tailwindcss"` not `@tailwind` directives
2. **Node ENV:** Keep `NODE_ENV` commented out in `.env` for dev builds
3. **WebSocket:** Connection auto-reconnects with exponential backoff

### General

1. **Hexagonal Imports:** Always check dependency direction
2. **Database Migrations:** Never modify schema manually — use Alembic
3. **Redis Keys:** Use prefixes for namespacing (`session:*`, `agent:*`)

---

## 13. Security Considerations

- All containers run as non-root users
- Secrets managed via environment variables (never committed)
- JWT tokens for authentication
- Distributed locking prevents race conditions
- Soft deletion for audit trails
- Circuit breakers on external API calls

---

## 14. Future Roadmap (Phase 3.0)

- [ ] **Agent Marketplace:** External agent integration (JSON/gRPC)
- [ ] **LLM Fine-Tuning:** Feedback loops for model improvement
- [ ] **Multi-Tenancy:** RBAC and tenant isolation

---

## 15. Key Documentation References

| Document | Purpose |
|:---------|:--------|
| `README.md` | Project overview for users/contributors |
| `CLAUDE.md` | Detailed agent briefing |
| `Project_Architecture_Document.md` | Technical architecture reference |
| `MASTER_EXECUTION_PLAN.md` | Implementation roadmap |
| `User_Guide.md` | End-user documentation |
| `docs/API.md` | API documentation |
| `docs/adr/` | Architecture Decision Records |

---

> **Remember:** This is an industrial-grade system. Every state transition is validated, every error is logged, and every metric is tracked. Build with resilience in mind.
