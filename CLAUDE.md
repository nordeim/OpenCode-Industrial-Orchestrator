# CLAUDE.md — Agent Briefing Document

> **Single Source of Truth** for AI coding agents and human developers
> **Last Updated:** February 3, 2026  
> **Status:** Phase 2.2 Complete, Phase 2.3 In Progress

---

## 🎯 Project Overview

The **OpenCode Industrial Orchestrator** is a production-grade system for managing autonomous coding sessions. It uses **Hexagonal Architecture** (Ports & Adapters) to ensure domain isolation, testability, and resilience.

**Design Philosophy:** "Industrial Cybernetics" — Ruthless efficiency, visibility ("Glass Box"), graceful degradation.

---

## 📊 Current Progress

| Phase | Description | Status | Tests |
|:------|:------------|:------:|:-----:|
| 2.1 | Foundation & Core Orchestrator | ✅ Complete | — |
| 2.2 | Multi-Agent Intelligence | ✅ Complete | 212 |
| 2.3 | Dashboard & Visualization | 🔄 In Progress | — |
| 2.4 | Production Hardening | 🔲 Planned | — |

---

## 🏗️ Tech Stack

| Layer | Technology |
|:------|:-----------|
| Language | Python 3.11+ |
| Framework | FastAPI (uvicorn) |
| Database | PostgreSQL 15 (AsyncPG + SQLAlchemy 2.0) |
| Cache/Lock | Redis 7 |
| Migrations | Alembic |
| Testing | Pytest + Factory Boy |
| Frontend | Next.js 14 + Tailwind CSS 4.0 |

---

## 📂 Project Structure

```
orchestrator/src/industrial_orchestrator/
├── domain/                           # 🧠 PURE BUSINESS LOGIC
│   ├── entities/
│   │   ├── session.py               # SessionEntity (254 lines)
│   │   ├── agent.py                 # AgentEntity (766 lines)
│   │   ├── task.py                  # TaskEntity (721 lines)
│   │   ├── context.py               # ContextEntity (433 lines)
│   │   └── registry.py              # AgentRegistry (500+ lines)
│   ├── value_objects/
│   │   ├── session_status.py        # 12 states, state machine
│   │   └── execution_metrics.py     # Performance telemetry
│   └── exceptions/
│       ├── session_exceptions.py
│       ├── agent_exceptions.py
│       ├── task_exceptions.py
│       └── context_exceptions.py
│
├── application/                      # ⚙️ ORCHESTRATION LOGIC
│   ├── services/
│   │   ├── session_service.py       # 638 lines, lifecycle management
│   │   ├── agent_management_service.py  # Agent routing/registration
│   │   ├── context_service.py       # Context sharing/merging
│   │   └── task_decomposition_service.py  # 684 lines, templates
│   ├── ports/
│   │   ├── repository_ports.py      # Repository ABCs
│   │   └── service_ports.py         # External service ABCs
│   └── dtos/
│       ├── session_dtos.py          # Request/Response DTOs
│       ├── agent_dtos.py
│       └── task_dtos.py
│
├── infrastructure/                   # 🔌 ADAPTERS
│   ├── repositories/
│   │   ├── session_repository.py    # PostgreSQL persistence
│   │   ├── agent_repository.py      # Redis agent storage
│   │   └── context_repository.py    # Hybrid storage
│   ├── locking/
│   │   └── distributed_lock.py      # Redis fair locking
│   ├── adapters/
│   │   └── opencode_client.py       # OpenCode API client
│   └── database/
│       └── models.py                # SQLAlchemy models
│
└── presentation/                     # 🖥️ ENTRY POINTS
    └── api/
        ├── main.py                   # FastAPI app factory
        ├── dependencies.py           # DI configuration
        ├── routers/
        │   ├── sessions.py           # /api/v1/sessions
        │   ├── agents.py             # /api/v1/agents
        │   ├── tasks.py              # /api/v1/tasks
        │   └── contexts.py           # /api/v1/contexts
        └── websocket/
            ├── connection_manager.py # WebSocket pool
            └── session_events.py     # Real-time updates

dashboard/                            # Next.js Frontend
└── src/                              # React components (in progress)
```

---

## 🧠 Domain Entities (Core Business Logic)

### SessionEntity
**Location:** `domain/entities/session.py`

```python
class SessionEntity(BaseModel):
    id: UUID
    title: str                        # Industrial naming (IND-*)
    status: SessionStatus             # 12 possible states
    session_type: SessionType         # PLANNING, EXECUTION, REVIEW, DEBUG
    priority: SessionPriority         # CRITICAL (0) to DEFERRED (4)
    initial_prompt: str
    checkpoints: List[Dict]           # Recovery points
    metrics: ExecutionMetrics         # Performance data
```

**Key Methods:**
- `transition_to(new_status)` — Validated state transition
- `start_execution()` — PENDING → RUNNING
- `complete_with_result(result)` — Mark complete with data
- `fail_with_error(error)` — Mark failed with context
- `add_checkpoint(data)` — Save recovery point
- `calculate_health_score()` → float (0.0 to 1.0)

### AgentEntity
**Location:** `domain/entities/agent.py`

```python
class AgentEntity(BaseModel):
    id: UUID
    name: str                         # Pattern: AGENT-[A-Z0-9-]+
    agent_type: AgentType             # ARCHITECT, IMPLEMENTER, REVIEWER, DEBUGGER, etc.
    capabilities: List[AgentCapability]  # 20+ capability types
    performance: AgentPerformanceMetrics
    load: AgentLoadMetrics
```

**Agent Types:** `ARCHITECT`, `IMPLEMENTER`, `REVIEWER`, `DEBUGGER`, `INTEGRATOR`, `ORCHESTRATOR`, `ANALYST`, `OPTIMIZER`

**Capabilities:** `REQUIREMENTS_ANALYSIS`, `SYSTEM_DESIGN`, `CODE_GENERATION`, `CODE_REVIEW`, `DEBUGGING`, `TESTING`, `DOCUMENTATION`, `SECURITY_AUDIT`, etc.

### TaskEntity
**Location:** `domain/entities/task.py`

```python
class TaskEntity(BaseModel):
    id: UUID
    title: str
    description: str
    status: TaskStatus                # PENDING → READY → IN_PROGRESS → COMPLETED
    complexity_level: TaskComplexityLevel
    priority: TaskPriority
    subtasks: List[TaskEntity]        # Recursive decomposition
    dependencies: List[TaskDependency]
    estimated: TaskEstimate           # PERT estimates
```

**Key Methods:**
- `decompose(strategy, max_depth)` — Break into subtasks
- `add_dependency(task_id, type)` — Add dependency
- `get_dependency_graph()` → NetworkX DiGraph
- `can_start()` → bool (dependencies satisfied?)

### ContextEntity
**Location:** `domain/entities/context.py`

```python
class ContextEntity:
    id: UUID
    scope: ContextScope               # SESSION, AGENT, GLOBAL, TEMPORARY
    data: Dict[str, Any]              # Key-value storage
    version: int                      # Optimistic locking
    history: List[ContextChange]      # Audit trail
```

**Key Methods:**
- `get(key, default)` — Dot notation support (e.g., "config.model")
- `set(key, value, changed_by)` — Versioned update
- `diff(other)` → ContextDiff
- `merge(other, strategy)` → ContextEntity

---

## ⚙️ Application Services

### SessionService
**Location:** `application/services/session_service.py`

| Method | Description |
|:-------|:------------|
| `create_session(title, prompt, ...)` | Create new session |
| `get_session(id)` | Retrieve session |
| `start_session(id)` | Begin execution |
| `complete_session(id, result)` | Mark complete |
| `fail_session(id, error)` | Mark failed |
| `retry_session(id)` | Retry if recoverable |
| `add_checkpoint(id, data)` | Save recovery point |
| `execute_with_opencode(id)` | Execute via OpenCode API |

### TaskDecompositionService
**Location:** `application/services/task_decomposition_service.py`

**Templates:**
- `microservice` — API layer, service layer, data layer, shared components
- `crud` — Create, Read, Update, Delete, Validate, Authorize
- `security` — Threat modeling, identity, access control, encryption, audit
- `ui_component` — Components, state, styles, tests

**Method:**
```python
analyze_and_decompose(
    task: TaskEntity,
    auto_estimate: bool = True,
    apply_templates: bool = True,
    max_depth: int = 3
) -> TaskEntity
```

### AgentManagementService
**Location:** `application/services/agent_management_service.py`

| Method | Description |
|:-------|:------------|
| `register_agent(request)` | Register new agent |
| `deregister_agent(id)` | Remove agent |
| `route_task(request)` | Find best agent for task |
| `update_agent_performance(id, result)` | Record metrics |

### ContextService
**Location:** `application/services/context_service.py`

| Method | Description |
|:-------|:------------|
| `create_context(session_id, data)` | Create new context |
| `get_context(id)` | Retrieve context |
| `update_context(id, updates)` | Update with versioning |
| `share_context(source, target)` | Share between sessions |
| `merge_contexts(ids)` | Merge multiple contexts |

---

## 🔌 API Endpoints

### REST API

```
POST   /api/v1/sessions              Create session
GET    /api/v1/sessions              List sessions (paginated)
GET    /api/v1/sessions/{id}         Get session by ID
POST   /api/v1/sessions/{id}/start   Start execution
POST   /api/v1/sessions/{id}/complete Mark complete
POST   /api/v1/sessions/{id}/fail    Mark failed
DELETE /api/v1/sessions/{id}         Soft delete

POST   /api/v1/agents                Register agent
GET    /api/v1/agents                List agents
GET    /api/v1/agents/{id}           Get agent
DELETE /api/v1/agents/{id}           Deregister
POST   /api/v1/agents/route          Route task to best agent
POST   /api/v1/agents/{id}/heartbeat Keep-alive

POST   /api/v1/tasks                 Create task
GET    /api/v1/tasks/{id}            Get task
POST   /api/v1/tasks/{id}/decompose  Decompose into subtasks
GET    /api/v1/tasks/{id}/dependencies Get dependency graph

POST   /api/v1/contexts              Create context
GET    /api/v1/contexts/{id}         Get context
PATCH  /api/v1/contexts/{id}         Update context
POST   /api/v1/contexts/merge        Merge contexts

GET    /health                       Health check
GET    /ready                        Readiness check (DB + Redis)
GET    /live                         Liveness check
```

### WebSocket

```
WS     /ws/sessions                  All session events
WS     /ws/sessions/{id}             Specific session events
```

---

## 🧪 Testing

### Test Files
| File | Tests | Entity |
|:-----|------:|:-------|
| `test_session_entity.py` | 42 | SessionEntity |
| `test_agent_entity.py` | 54 | AgentEntity |
| `test_task_entity.py` | 53 | TaskEntity |
| `test_context_entity.py` | 39 | ContextEntity |
| `test_task_decomposition_service.py` | 24 | TaskDecompositionService |
| **Total** | **212** | |

### Factories
**Location:** `tests/unit/domain/factories/`

```python
from tests.unit.domain.factories.session_factory import (
    SessionEntityFactory,
    create_session_with_dependencies,
    create_session_batch
)
```

### Commands
```bash
# All tests
poetry run pytest

# Unit tests only
poetry run pytest tests/unit

# Specific file
poetry run pytest tests/unit/domain/test_session_entity.py -v

# With coverage
poetry run pytest --cov=src
```

---

## 💻 Development Commands

```bash
# Start infrastructure
docker-compose up -d postgres redis opencode-server

# Install dependencies
cd orchestrator && poetry install

# Run migrations
poetry run alembic upgrade head

# Start API server
poetry run uvicorn src.industrial_orchestrator.presentation.api.main:app --reload

# Start dashboard
cd dashboard && npm install && npm run dev
```

---

## 📋 Development Conventions

### Code Style
- **Python:** `black`, `isort`, `flake8`
- **TypeScript:** ESLint + Prettier

### Architecture Rules
1. **Domain never imports from Infrastructure/Presentation**
2. **Pydantic models for all domain entities**
3. **Factories for test data generation**
4. **TDD mandatory — write tests first**

### Naming Conventions
- Sessions: `IND-*` pattern (e.g., `IND-Session-001`)
- Agents: `AGENT-*` pattern (e.g., `AGENT-ARCHITECT-001`)
- Tasks: Descriptive action phrases

### State Transitions
```
PENDING → QUEUED → RUNNING → COMPLETED
                ↘ PAUSED ↗
                → FAILED
                → TIMEOUT
                → STOPPED
```

Valid transitions are enforced by `SessionStatus.can_transition_to()`.

---

## 🚧 Remaining Work

### Phase 2.3: Dashboard (In Progress)
- [ ] SessionMonitor component
- [ ] TaskGraph visualization
- [ ] AgentStatus panel
- [ ] Real-time WebSocket integration

### Phase 2.4: Production Hardening (Planned)
- [ ] Kubernetes manifests & Helm charts
- [ ] CI/CD pipelines (GitHub Actions)
- [ ] Prometheus/Grafana dashboards

---

## ⚠️ Known Issues & Gotchas

1. **Pydantic V2:** Entity validators use `@field_validator` (not `@validator`)
2. **State Transitions:** PENDING → RUNNING is valid for immediate execution
3. **Checkpoint Sequence:** Increments from last checkpoint, not list length
4. **Metrics Sync:** `add_checkpoint()` syncs `metrics.checkpoint_count`
5. **Factory Faker:** Use `random.choice()` not `factory.Faker().generate()` in hooks

---

## 📚 Key Documentation

| Document | Purpose |
|:---------|:--------|
| `README.md` | Project overview for users/contributors |
| `GEMINI.md` | Project memory for AI agents |
| `Project_Architecture_Document.md` | Technical architecture reference |
| `MASTER_EXECUTION_PLAN.md` | Detailed implementation roadmap |

---

> **Remember:** This is an industrial-grade system. Every state transition is validated, every error is logged, and every metric is tracked. Build with resilience in mind.
