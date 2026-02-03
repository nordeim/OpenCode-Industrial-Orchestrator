# MASTER EXECUTION PLAN — OpenCode Industrial Orchestrator

> **Document Version**: 1.0  
> **Created**: 2026-02-03  
> **Status**: Comprehensive reference for codebase completion

---

## Executive Summary

This document provides a **complete, actionable execution plan** to finish the OpenCode Industrial Orchestrator. The work is organized into **independent phases**, each containing detailed file specifications with features, interfaces, and validation checklists.

### Current Progress

| Phase | Status | Completion |
|:------|:------:|:----------:|
| 2.1 Foundation & Core Orchestrator | ✅ Complete | 100% |
| 2.2 Multi-Agent Intelligence | 🔄 Partial | ~50% |
| 2.3 Dashboard & Visualization | 🔲 Not Started | 0% |
| 2.4 Production Hardening | 🔲 Not Started | 0% |

### Remaining Work Summary

```text
Phase 2.2 (Remaining):  ~15 files,  ~3,000 lines of code
Phase 2.3:              ~20 files,  ~4,000 lines of code
Phase 2.4:              ~10 files,  ~1,500 lines of code
─────────────────────────────────────────────────────────
Total Estimated:        ~45 files,  ~8,500 lines of code
```

---

## Phase 2.2: Multi-Agent Intelligence Completion

> **Goal**: Complete the "brain" of the orchestrator — dynamic agent management, context sharing, and external API exposure.

### 2.2.A — Port Interfaces & DTOs (Foundation)

Define abstract interfaces following Hexagonal Architecture principles. This enables dependency injection and testability.

---

#### [NEW] `application/ports/repository_ports.py`

**Purpose**: Abstract interfaces for all persistence operations.

**Features**:
- `SessionRepositoryPort` — abstract CRUD for sessions
- `AgentRepositoryPort` — abstract agent persistence
- `ContextRepositoryPort` — abstract context storage

**Interface Specification**:
```python
class SessionRepositoryPort(ABC):
    async def get_by_id(id: UUID) -> Optional[SessionEntity]
    async def save(entity: SessionEntity) -> SessionEntity
    async def delete(id: UUID) -> bool
    async def find_by_status(status: SessionStatus) -> List[SessionEntity]

class AgentRepositoryPort(ABC):
    async def register(agent: AgentEntity) -> AgentEntity
    async def deregister(agent_id: UUID) -> bool
    async def find_available(capability: AgentCapability) -> List[AgentEntity]
    async def update_metrics(agent_id: UUID, metrics: AgentPerformanceMetrics) -> None

class ContextRepositoryPort(ABC):
    async def store(context: ContextEntity) -> ContextEntity
    async def retrieve(context_id: UUID) -> Optional[ContextEntity]
    async def merge(source_ids: List[UUID], target_id: UUID) -> ContextEntity
```

**Checklist**:
- [ ] Define `SessionRepositoryPort` ABC
- [ ] Define `AgentRepositoryPort` ABC
- [ ] Define `ContextRepositoryPort` ABC
- [ ] Add type hints for all methods
- [ ] Document docstrings with industrial standards
- [ ] Unit test: verify interfaces are properly abstract

---

#### [NEW] `application/ports/service_ports.py`

**Purpose**: Abstract interfaces for external service integrations.

**Features**:
- `OpenCodeClientPort` — abstract API client
- `DistributedLockPort` — abstract locking mechanism
- `MessageBusPort` — abstract event publishing

**Interface Specification**:
```python
class OpenCodeClientPort(ABC):
    async def execute_prompt(prompt: str, config: Dict) -> ExecutionResult
    async def get_status() -> ServiceHealth

class DistributedLockPort(ABC):
    async def acquire(resource: str, timeout: float) -> bool
    async def release(resource: str) -> bool
    async def is_locked(resource: str) -> bool

class MessageBusPort(ABC):
    async def publish(event: DomainEvent) -> None
    async def subscribe(event_type: Type, handler: Callable) -> None
```

**Checklist**:
- [ ] Define `OpenCodeClientPort` ABC
- [ ] Define `DistributedLockPort` ABC
- [ ] Define `MessageBusPort` ABC
- [ ] Ensure ports have no infrastructure dependencies
- [ ] Document async context manager support where applicable

---

#### [NEW] `application/dtos/session_dtos.py`

**Purpose**: Data transfer objects for Session API layer.

**Features**:
- Request DTOs with Pydantic validation
- Response DTOs with serialization
- Error response DTOs

**Interface Specification**:
```python
class CreateSessionRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    initial_prompt: str
    session_type: SessionType = SessionType.EXECUTION
    priority: SessionPriority = SessionPriority.MEDIUM
    agent_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class SessionResponse(BaseModel):
    id: UUID
    title: str
    status: str
    session_type: str
    created_at: datetime
    health_score: Optional[float] = None
    
    class Config:
        from_attributes = True

class SessionListResponse(BaseModel):
    items: List[SessionResponse]
    total: int
    page: int
    page_size: int
```

**Checklist**:
- [ ] Create `CreateSessionRequest` with validation
- [ ] Create `UpdateSessionRequest` with partial updates
- [ ] Create `SessionResponse` with serialization config
- [ ] Create `SessionListResponse` with pagination
- [ ] Create `SessionErrorResponse` with error codes
- [ ] Add example values for OpenAPI documentation

---

#### [NEW] `application/dtos/agent_dtos.py`

**Purpose**: Data transfer objects for Agent API layer.

**Features**:
- Agent registration request/response
- Capability routing request
- Performance summary response

**Interface Specification**:
```python
class RegisterAgentRequest(BaseModel):
    name: str = Field(..., pattern=r"^AGENT-[A-Z0-9-]+$")
    agent_type: AgentType
    capabilities: List[AgentCapability]
    max_concurrent_capacity: int = Field(default=5, ge=1, le=50)

class AgentResponse(BaseModel):
    id: UUID
    name: str
    agent_type: str
    capabilities: List[str]
    performance_tier: str
    load_level: str
    is_available: bool

class RouteTaskRequest(BaseModel):
    task_description: str
    required_capabilities: List[AgentCapability]
    preferred_agent_type: Optional[AgentType] = None
```

**Checklist**:
- [ ] Create `RegisterAgentRequest` with naming validation
- [ ] Create `DeregisterAgentRequest` 
- [ ] Create `AgentResponse` with computed fields
- [ ] Create `RouteTaskRequest` for capability matching
- [ ] Create `AgentPerformanceSummary` response

---

#### [NEW] `application/dtos/task_dtos.py`

**Purpose**: Data transfer objects for Task API layer.

**Features**:
- Task creation request
- Decomposition request/response
- Dependency graph response

**Interface Specification**:
```python
class CreateTaskRequest(BaseModel):
    title: str
    description: str
    session_id: UUID
    parent_task_id: Optional[UUID] = None
    priority: TaskPriority = TaskPriority.NORMAL
    required_capabilities: Optional[List[AgentCapability]] = None

class DecomposeTaskRequest(BaseModel):
    task_id: UUID
    apply_templates: bool = True
    max_depth: int = Field(default=3, ge=1, le=5)

class TaskResponse(BaseModel):
    id: UUID
    title: str
    status: str
    complexity_level: str
    estimated_hours: Optional[float]
    subtasks: Optional[List["TaskResponse"]] = None
```

**Checklist**:
- [ ] Create `CreateTaskRequest` with validation
- [ ] Create `DecomposeTaskRequest` with depth limits
- [ ] Create `TaskResponse` with recursive subtasks
- [ ] Create `TaskDependencyGraphResponse` for DAG visualization
- [ ] Add Pydantic forward reference resolution

---

### 2.2.B — Agent Management System

Implement dynamic agent registration, discovery, and performance tracking.

---

#### [NEW] `domain/entities/registry.py`

**Purpose**: Domain entity for agent registry state management.

**Features**:
- In-memory agent collection
- Capability indexing
- Availability tracking

**Interface Specification**:
```python
class AgentRegistry:
    def register(agent: AgentEntity) -> bool
    def deregister(agent_id: UUID) -> bool
    def find_by_capability(capability: AgentCapability) -> List[AgentEntity]
    def find_available() -> List[AgentEntity]
    def get_agent(agent_id: UUID) -> Optional[AgentEntity]
    def update_agent(agent: AgentEntity) -> None
    def get_statistics() -> RegistryStatistics
```

**Checklist**:
- [ ] Define `AgentRegistry` class
- [ ] Implement capability-based indexing
- [ ] Add thread-safe operations (for concurrent access)
- [ ] Implement `RegistryStatistics` value object
- [ ] Unit tests for all registry operations

---

#### [NEW] `infrastructure/repositories/agent_repository.py`

**Purpose**: Redis-backed agent registry for distributed deployments.

**Features**:
- Redis hash-based storage
- Capability set indexing
- TTL-based heartbeat/health check
- Implements `AgentRepositoryPort`

**Interface Specification**:
```python
class RedisAgentRepository(AgentRepositoryPort):
    def __init__(redis_client: IndustrialRedisClient)
    async def register(agent: AgentEntity) -> AgentEntity
    async def deregister(agent_id: UUID) -> bool
    async def find_available(capability: AgentCapability) -> List[AgentEntity]
    async def update_metrics(agent_id: UUID, metrics: AgentPerformanceMetrics) -> None
    async def heartbeat(agent_id: UUID) -> None
    async def cleanup_stale_agents(max_age_seconds: int) -> int
```

**Checklist**:
- [ ] Create `RedisAgentRepository` implementing port
- [ ] Implement Redis HSET/HGET for agent storage
- [ ] Add Redis SET for capability indexing
- [ ] Implement TTL-based heartbeat mechanism
- [ ] Add stale agent cleanup
- [ ] Integration tests with Redis testcontainer

---

#### [NEW] `application/services/agent_management_service.py`

**Purpose**: Orchestrate agent lifecycle and capability routing.

**Features**:
- Agent registration workflow
- Capability-based task routing
- Performance tier calculation
- Load balancing

**Interface Specification**:
```python
class AgentManagementService:
    def __init__(agent_repository: AgentRepositoryPort, lock_manager: DistributedLockPort)
    
    async def register_agent(request: RegisterAgentRequest) -> AgentResponse
    async def deregister_agent(agent_id: UUID) -> bool
    async def route_task(request: RouteTaskRequest) -> AgentEntity
    async def update_agent_performance(agent_id: UUID, result: TaskExecutionResult) -> None
    async def get_agent_summary(agent_id: UUID) -> AgentPerformanceSummary
    async def rebalance_workload() -> RebalanceResult
```

**Checklist**:
- [ ] Create `AgentManagementService` class
- [ ] Implement agent registration with validation
- [ ] Implement capability-based routing algorithm
- [ ] Add weighted routing based on performance tier
- [ ] Implement load balancing across agents
- [ ] Add circuit breaker for degraded agents
- [ ] Unit tests with mocked repository

---

### 2.2.C — Context Management System

Enable context sharing between sessions and agents.

---

#### [NEW] `domain/entities/context.py`

**Purpose**: Domain entity for execution context (files, variables, knowledge).

**Features**:
- Context containment hierarchy
- Scope-based access control
- Conflict detection for concurrent modifications

**Interface Specification**:
```python
class ContextScope(Enum):
    SESSION = "session"
    AGENT = "agent"
    GLOBAL = "global"
    TEMPORARY = "temporary"

class ContextEntity(BaseModel):
    id: UUID
    session_id: Optional[UUID]
    agent_id: Optional[UUID]
    scope: ContextScope
    data: Dict[str, Any]
    version: int
    created_at: datetime
    updated_at: datetime
    
    def get(key: str) -> Any
    def set(key: str, value: Any) -> None
    def merge(other: "ContextEntity") -> "ContextEntity"
    def diff(other: "ContextEntity") -> ContextDiff
```

**Checklist**:
- [ ] Define `ContextScope` enum
- [ ] Define `ContextEntity` with Pydantic
- [ ] Implement version tracking for optimistic locking
- [ ] Add `ContextDiff` value object
- [ ] Implement `merge()` with conflict resolution
- [ ] Unit tests for context operations

---

#### [NEW] `domain/exceptions/context_exceptions.py`

**Purpose**: Context-specific domain exceptions.

**Features**:
- `ContextNotFoundError`
- `ContextConflictError`
- `ContextScopeMismatchError`

**Checklist**:
- [ ] Define `ContextNotFoundError`
- [ ] Define `ContextConflictError` with conflict details
- [ ] Define `ContextScopeMismatchError`
- [ ] Include retry hints in exception metadata

---

#### [NEW] `infrastructure/repositories/context_repository.py`

**Purpose**: Storage adapter for context persistence.

**Features**:
- Redis for hot context (session/agent scope)
- PostgreSQL for cold context (global scope)
- Tiered storage with promotion/demotion

**Interface Specification**:
```python
class HybridContextRepository(ContextRepositoryPort):
    def __init__(redis_client: IndustrialRedisClient, db_session: AsyncSession)
    
    async def store(context: ContextEntity) -> ContextEntity
    async def retrieve(context_id: UUID) -> Optional[ContextEntity]
    async def retrieve_by_session(session_id: UUID) -> List[ContextEntity]
    async def merge(source_ids: List[UUID], strategy: MergeStrategy) -> ContextEntity
    async def promote_to_global(context_id: UUID) -> ContextEntity
    async def cleanup_temporary(max_age_seconds: int) -> int
```

**Checklist**:
- [ ] Create `HybridContextRepository` class
- [ ] Implement Redis storage for hot contexts
- [ ] Implement PostgreSQL storage for global contexts
- [ ] Add automatic tier promotion logic
- [ ] Implement merge strategies (LAST_WRITE_WINS, DEEP_MERGE)
- [ ] Integration tests with both Redis and PostgreSQL

---

#### [NEW] `application/services/context_service.py`

**Purpose**: Orchestrate context creation, sharing, and lifecycle.

**Features**:
- Context creation from session
- Cross-session context sharing
- Conflict resolution workflows

**Interface Specification**:
```python
class ContextService:
    def __init__(context_repository: ContextRepositoryPort, session_service: SessionService)
    
    async def create_context(session_id: UUID, initial_data: Dict) -> ContextEntity
    async def get_context(context_id: UUID) -> ContextEntity
    async def update_context(context_id: UUID, updates: Dict) -> ContextEntity
    async def share_context(source_session_id: UUID, target_session_id: UUID) -> ContextEntity
    async def merge_contexts(context_ids: List[UUID]) -> ContextEntity
```

**Checklist**:
- [ ] Create `ContextService` class
- [ ] Implement context creation from session
- [ ] Add context sharing with scope validation
- [ ] Implement conflict detection and resolution
- [ ] Add context lifecycle (cleanup temporary)
- [ ] Unit tests with mocked repository

---

### 2.2.D — FastAPI Presentation Layer

Expose all services via REST API with industrial-grade middleware.

---

#### [NEW] `presentation/api/main.py`

**Purpose**: FastAPI application entry point with middleware configuration.

**Features**:
- Application factory pattern
- CORS middleware
- Error handling middleware
- Request ID injection
- Structured logging
- Health check endpoint

**Interface Specification**:
```python
def create_app() -> FastAPI:
    """Application factory for testability"""

app = create_app()

# Middleware stack:
# - RequestIDMiddleware (inject X-Request-ID)
# - ErrorHandlerMiddleware (catch and format exceptions)
# - LoggingMiddleware (structured request/response logging)
# - CORSMiddleware (configurable origins)

@app.get("/health")
async def health_check() -> HealthResponse

@app.get("/ready")
async def readiness_check() -> ReadinessResponse
```

**Checklist**:
- [ ] Create `create_app()` application factory
- [ ] Add `RequestIDMiddleware` for tracing
- [ ] Add `ErrorHandlerMiddleware` with industrial error codes
- [ ] Configure CORS from environment
- [ ] Implement `/health` endpoint
- [ ] Implement `/ready` endpoint (checks DB + Redis)
- [ ] Add OpenAPI metadata (title, version, description)
- [ ] Integration test: verify app startup

---

#### [NEW] `presentation/api/routers/sessions.py`

**Purpose**: Session management REST endpoints.

**Features**:
- Full CRUD operations
- Bulk operations
- Filtering and pagination
- Action endpoints (start, complete, fail)

**Interface Specification**:
```python
router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])

@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(request: CreateSessionRequest) -> SessionResponse

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID) -> SessionResponse

@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> SessionListResponse

@router.post("/{session_id}/start", response_model=SessionResponse)
async def start_session(session_id: UUID) -> SessionResponse

@router.post("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(session_id: UUID, result: CompleteSessionRequest) -> SessionResponse

@router.post("/{session_id}/fail", response_model=SessionResponse)
async def fail_session(session_id: UUID, error: FailSessionRequest) -> SessionResponse

@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: UUID) -> None
```

**Checklist**:
- [ ] Create router with `/api/v1/sessions` prefix
- [ ] Implement `POST /` for session creation
- [ ] Implement `GET /{id}` with optional includes
- [ ] Implement `GET /` with filtering and pagination
- [ ] Implement `POST /{id}/start` action
- [ ] Implement `POST /{id}/complete` action
- [ ] Implement `POST /{id}/fail` action
- [ ] Implement `DELETE /{id}` for soft delete
- [ ] Add dependency injection for `SessionService`
- [ ] Integration tests for all endpoints

---

#### [NEW] `presentation/api/routers/agents.py`

**Purpose**: Agent management REST endpoints.

**Features**:
- Agent registration/deregistration
- Capability queries
- Performance metrics
- Task routing

**Interface Specification**:
```python
router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])

@router.post("/", response_model=AgentResponse, status_code=201)
async def register_agent(request: RegisterAgentRequest) -> AgentResponse

@router.delete("/{agent_id}", status_code=204)
async def deregister_agent(agent_id: UUID) -> None

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: UUID) -> AgentResponse

@router.get("/", response_model=AgentListResponse)
async def list_agents(capability: Optional[str] = None) -> AgentListResponse

@router.post("/route", response_model=AgentResponse)
async def route_task(request: RouteTaskRequest) -> AgentResponse

@router.get("/{agent_id}/performance", response_model=AgentPerformanceSummary)
async def get_agent_performance(agent_id: UUID) -> AgentPerformanceSummary

@router.post("/{agent_id}/heartbeat", status_code=204)
async def agent_heartbeat(agent_id: UUID) -> None
```

**Checklist**:
- [ ] Create router with `/api/v1/agents` prefix
- [ ] Implement `POST /` for registration
- [ ] Implement `DELETE /{id}` for deregistration
- [ ] Implement `GET /{id}` for agent details
- [ ] Implement `GET /` with capability filtering
- [ ] Implement `POST /route` for task routing
- [ ] Implement `GET /{id}/performance` summary
- [ ] Implement `POST /{id}/heartbeat` keep-alive
- [ ] Integration tests for agent lifecycle

---

#### [NEW] `presentation/api/routers/tasks.py`

**Purpose**: Task management and decomposition REST endpoints.

**Features**:
- Task CRUD
- Decomposition trigger
- Dependency graph queries

**Interface Specification**:
```python
router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(request: CreateTaskRequest) -> TaskResponse

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, include_subtasks: bool = False) -> TaskResponse

@router.post("/{task_id}/decompose", response_model=TaskResponse)
async def decompose_task(task_id: UUID, request: DecomposeTaskRequest) -> TaskResponse

@router.get("/{task_id}/dependencies", response_model=DependencyGraphResponse)
async def get_task_dependencies(task_id: UUID) -> DependencyGraphResponse

@router.post("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(task_id: UUID, status: UpdateTaskStatusRequest) -> TaskResponse
```

**Checklist**:
- [ ] Create router with `/api/v1/tasks` prefix
- [ ] Implement `POST /` for task creation
- [ ] Implement `GET /{id}` with subtask expansion
- [ ] Implement `POST /{id}/decompose` trigger
- [ ] Implement `GET /{id}/dependencies` DAG query
- [ ] Implement `POST /{id}/status` updates
- [ ] Integration tests for decomposition

---

#### [NEW] `presentation/api/routers/context.py`

**Purpose**: Context management REST endpoints.

**Interface Specification**:
```python
router = APIRouter(prefix="/api/v1/contexts", tags=["Context"])

@router.post("/", response_model=ContextResponse, status_code=201)
async def create_context(request: CreateContextRequest) -> ContextResponse

@router.get("/{context_id}", response_model=ContextResponse)
async def get_context(context_id: UUID) -> ContextResponse

@router.patch("/{context_id}", response_model=ContextResponse)
async def update_context(context_id: UUID, updates: UpdateContextRequest) -> ContextResponse

@router.post("/merge", response_model=ContextResponse)
async def merge_contexts(request: MergeContextsRequest) -> ContextResponse
```

**Checklist**:
- [ ] Create router with `/api/v1/contexts` prefix
- [ ] Implement context CRUD operations
- [ ] Implement context merge endpoint
- [ ] Add scope validation middleware
- [ ] Integration tests for context operations

---

#### [NEW] `presentation/api/dependencies.py`

**Purpose**: FastAPI dependency injection configuration.

**Features**:
- Database session provider
- Redis client provider
- Service factory providers
- Current user (future auth)

**Interface Specification**:
```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield database session for request scope"""

async def get_redis_client() -> IndustrialRedisClient:
    """Get Redis client singleton"""

async def get_session_service(
    db: AsyncSession = Depends(get_db_session),
    redis: IndustrialRedisClient = Depends(get_redis_client)
) -> SessionService:
    """Factory for SessionService"""

async def get_agent_service(...) -> AgentManagementService
async def get_context_service(...) -> ContextService
```

**Checklist**:
- [ ] Create database session dependency
- [ ] Create Redis client dependency
- [ ] Create service factory dependencies
- [ ] Add request-scoped cleanup
- [ ] Document dependency graph

---

### 2.2.E — Missing Infrastructure

---

#### [MODIFY] `pyproject.toml`

**Purpose**: Add missing dependency.

**Changes**:
- Add `networkx = "^3.2"` to dependencies

**Checklist**:
- [ ] Add networkx dependency
- [ ] Run `poetry lock`
- [ ] Verify import in `task.py` works

---

#### [NEW] `infrastructure/database/models_agent.py`

**Purpose**: Database models for Agent entity persistence (optional for Redis-primary).

**Checklist**:
- [ ] Create `AgentModel` if PostgreSQL fallback needed
- [ ] Add Alembic migration for agent table

---

#### [NEW] `infrastructure/database/models_context.py`

**Purpose**: Database models for Context entity persistence.

**Checklist**:
- [ ] Create `ContextModel` for global scope storage
- [ ] Add Alembic migration for context table

---

### 2.2.F — Tests

---

#### [NEW] `tests/unit/domain/test_agent_entity.py`

**Checklist**:
- [ ] Test agent creation with valid config
- [ ] Test capability validation
- [ ] Test performance tier calculation
- [ ] Test load level transitions

---

#### [NEW] `tests/unit/domain/test_task_entity.py`

**Checklist**:
- [ ] Test task creation
- [ ] Test dependency management
- [ ] Test cycle detection
- [ ] Test subtask hierarchy

---

#### [NEW] `tests/unit/domain/test_context_entity.py`

**Checklist**:
- [ ] Test context creation
- [ ] Test merge operations
- [ ] Test conflict detection

---

#### [NEW] `tests/unit/application/test_session_service.py`

**Checklist**:
- [ ] Test create session flow
- [ ] Test start/complete/fail transitions
- [ ] Test checkpoint management

---

#### [NEW] `tests/unit/application/test_agent_management_service.py`

**Checklist**:
- [ ] Test agent registration
- [ ] Test capability routing
- [ ] Test performance updates

---

#### [NEW] `tests/integration/api/test_sessions_api.py`

**Checklist**:
- [ ] Test POST /sessions
- [ ] Test GET /sessions/{id}
- [ ] Test session lifecycle actions
- [ ] Test error responses

---

#### [NEW] `tests/integration/api/test_agents_api.py`

**Checklist**:
- [ ] Test agent registration flow
- [ ] Test task routing
- [ ] Test heartbeat mechanism

---

## Phase 2.3: Dashboard & Visualization

> **Goal**: Provide a "Glass Box" interface for users to monitor orchestration in real-time.

### 2.3.A — Backend WebSocket Support

---

#### [NEW] `presentation/api/websocket/connection_manager.py`

**Purpose**: Manage WebSocket connections for real-time updates.

**Features**:
- Connection pool management
- Room/channel support
- Broadcast messaging
- Heartbeat/ping-pong

**Interface Specification**:
```python
class ConnectionManager:
    async def connect(websocket: WebSocket, client_id: str) -> None
    async def disconnect(client_id: str) -> None
    async def broadcast(message: Dict, room: Optional[str] = None) -> None
    async def send_personal(client_id: str, message: Dict) -> None
```

**Checklist**:
- [ ] Create `ConnectionManager` class
- [ ] Implement connection/disconnection handling
- [ ] Add room-based broadcasting
- [ ] Add heartbeat mechanism
- [ ] Unit tests for connection management

---

#### [NEW] `presentation/api/websocket/session_events.py`

**Purpose**: WebSocket endpoint for session state changes.

**Interface Specification**:
```python
@router.websocket("/ws/sessions/{session_id}")
async def session_events(websocket: WebSocket, session_id: UUID)

@router.websocket("/ws/sessions")
async def all_session_events(websocket: WebSocket)
```

**Checklist**:
- [ ] Create WebSocket router
- [ ] Implement session-specific subscriptions
- [ ] Implement all-sessions broadcast
- [ ] Add authentication (token-based)
- [ ] Integration test with async client

---

### 2.3.B — Next.js Frontend Foundation

---

#### [NEW] `dashboard/package.json`

**Purpose**: Next.js project configuration.

**Dependencies**:
- Next.js 14
- React 18
- Tailwind CSS 4.0
- shadcn/ui
- @tanstack/react-query
- socket.io-client

**Checklist**:
- [ ] Initialize Next.js project
- [ ] Configure Tailwind CSS
- [ ] Install shadcn/ui CLI
- [ ] Add API client dependencies

---

#### [NEW] `dashboard/tailwind.config.ts`

**Purpose**: Brutalist theme configuration.

**Features**:
- Industrial color palette (black, white, high contrast)
- Sharp corners (no rounded)
- Bold typography tokens
- Custom shadow utilities

**Checklist**:
- [ ] Define brutalist color scheme
- [ ] Configure typography scale
- [ ] Add industrial shadow utilities
- [ ] Configure dark mode

---

#### [NEW] `dashboard/src/app/layout.tsx`

**Purpose**: Root layout with providers.

**Checklist**:
- [ ] Configure QueryClientProvider
- [ ] Add WebSocket context provider
- [ ] Configure font loading (industrial fonts)
- [ ] Add global styles

---

#### [NEW] `dashboard/src/components/ui/` (shadcn primitives)

**Components to install and customize**:
- Button (brutalist styling)
- Card (sharp edges, bold borders)
- Table (industrial styling)
- Badge (status indicators)
- Sheet (mobile sidebar)
- Dialog (confirmations)

**Checklist**:
- [ ] Run `npx shadcn-ui@latest add button card table badge sheet dialog`
- [ ] Customize each for brutalist aesthetic
- [ ] Remove all rounded corners
- [ ] Add industrial shadow effects

---

### 2.3.C — Dashboard Pages

---

#### [NEW] `dashboard/src/app/page.tsx`

**Purpose**: Main dashboard overview.

**Features**:
- Session statistics cards
- Active sessions list
- Recent activity feed
- System health indicator

**Checklist**:
- [ ] Create statistics cards component
- [ ] Create active sessions table
- [ ] Create activity timeline
- [ ] Add real-time updates via WebSocket

---

#### [NEW] `dashboard/src/app/sessions/page.tsx`

**Purpose**: Session list and management.

**Features**:
- Filterable session table
- Status filtering
- Bulk actions
- Session creation modal

**Checklist**:
- [ ] Create session table with sorting
- [ ] Add status filter chips
- [ ] Add search functionality
- [ ] Create session dialog
- [ ] Add pagination

---

#### [NEW] `dashboard/src/app/sessions/[id]/page.tsx`

**Purpose**: Session detail view.

**Features**:
- Session metadata display
- Live status updates
- Checkpoint timeline
- Action buttons (start, stop, retry)

**Checklist**:
- [ ] Create session header with actions
- [ ] Create checkpoint timeline component
- [ ] Add live log viewer
- [ ] Add metrics visualization

---

#### [NEW] `dashboard/src/app/agents/page.tsx`

**Purpose**: Agent monitoring dashboard.

**Features**:
- Agent grid/list view
- Performance metrics cards
- Load visualization
- Registration management

**Checklist**:
- [ ] Create agent card component
- [ ] Add load gauge visualization
- [ ] Create performance sparklines
- [ ] Add register/deregister actions

---

#### [NEW] `dashboard/src/app/tasks/page.tsx`

**Purpose**: Task decomposition visualization.

**Features**:
- Interactive task DAG
- Task detail panel
- Decomposition trigger

**Checklist**:
- [ ] Integrate ReactFlow for DAG
- [ ] Create task node component
- [ ] Add zoom/pan controls
- [ ] Create detail sidebar

---

### 2.3.D — Frontend Services

---

#### [NEW] `dashboard/src/lib/api/client.ts`

**Purpose**: API client for backend communication.

**Checklist**:
- [ ] Create axios/fetch wrapper
- [ ] Add base URL configuration
- [ ] Add request/response interceptors
- [ ] Add error handling

---

#### [NEW] `dashboard/src/lib/api/sessions.ts`

**Purpose**: Session API hooks.

**Checklist**:
- [ ] Create `useSession` hook
- [ ] Create `useSessions` list hook
- [ ] Create mutation hooks
- [ ] Add optimistic updates

---

#### [NEW] `dashboard/src/lib/websocket/useWebSocket.ts`

**Purpose**: WebSocket hook for real-time updates.

**Checklist**:
- [ ] Create connection hook
- [ ] Add reconnection logic
- [ ] Add message parsing
- [ ] Add error handling

---

## Phase 2.4: Production Hardening

> **Goal**: Prepare the system for deployment in a real-world environment.

### 2.4.A — Container Optimization

---

#### [MODIFY] `orchestrator/Dockerfile.dev` → [NEW] `orchestrator/Dockerfile`

**Purpose**: Production-optimized Docker image.

**Features**:
- Multi-stage build
- Non-root user
- Minimal runtime image
- Health check

**Checklist**:
- [ ] Create builder stage for dependencies
- [ ] Create runtime stage with minimal image
- [ ] Add non-root user configuration
- [ ] Add HEALTHCHECK instruction
- [ ] Optimize layer caching

---

#### [NEW] `dashboard/Dockerfile`

**Purpose**: Production frontend Docker image.

**Checklist**:
- [ ] Create build stage with Node
- [ ] Create runtime stage with nginx/node
- [ ] Configure static file serving
- [ ] Add HEALTHCHECK

---

### 2.4.B — Kubernetes Deployment

---

#### [NEW] `infrastructure/kubernetes/namespace.yaml`

**Checklist**:
- [ ] Define namespace with labels
- [ ] Add resource quotas

---

#### [NEW] `infrastructure/kubernetes/orchestrator/deployment.yaml`

**Checklist**:
- [ ] Create Deployment with replicas
- [ ] Add readiness/liveness probes
- [ ] Configure resource limits
- [ ] Add environment variables from ConfigMap/Secret

---

#### [NEW] `infrastructure/kubernetes/orchestrator/service.yaml`

**Checklist**:
- [ ] Create ClusterIP service
- [ ] Expose ports 8000 (HTTP) and 8001 (WS)

---

#### [NEW] `infrastructure/kubernetes/orchestrator/configmap.yaml`

**Checklist**:
- [ ] Add non-sensitive configuration
- [ ] Add feature flags

---

#### [NEW] `infrastructure/kubernetes/orchestrator/secret.yaml`

**Checklist**:
- [ ] Template for DB credentials
- [ ] Template for Redis credentials

---

#### [NEW] `infrastructure/kubernetes/ingress.yaml`

**Checklist**:
- [ ] Configure ingress controller rules
- [ ] Add TLS configuration
- [ ] Add rate limiting annotations

---

### 2.4.C — Observability

---

#### [NEW] `presentation/api/middleware/metrics.py`

**Purpose**: Prometheus metrics middleware.

**Features**:
- Request count/duration histograms
- Error rate counters
- Custom business metrics

**Checklist**:
- [ ] Create Prometheus middleware
- [ ] Add request duration histogram
- [ ] Add request count counter
- [ ] Add `/metrics` endpoint

---

#### [NEW] `infrastructure/monitoring/grafana/dashboards/orchestrator.json`

**Purpose**: Pre-built Grafana dashboard.

**Checklist**:
- [ ] Create session overview panel
- [ ] Create API performance panel
- [ ] Create error rate panel
- [ ] Create resource utilization panel

---

#### [MODIFY] `presentation/api/main.py`

**Purpose**: Add structured logging.

**Checklist**:
- [ ] Configure structlog for JSON output
- [ ] Add request ID correlation
- [ ] Add log level configuration

---

### 2.4.D — CI/CD Pipeline

---

#### [NEW] `.github/workflows/ci.yaml`

**Purpose**: Continuous integration workflow.

**Stages**:
1. Lint (black, isort, flake8)
2. Type check (mypy)
3. Unit tests
4. Integration tests
5. Build Docker images

**Checklist**:
- [ ] Create lint job
- [ ] Create test job matrix
- [ ] Create build job
- [ ] Add caching for dependencies
- [ ] Add coverage reporting

---

#### [NEW] `.github/workflows/cd.yaml`

**Purpose**: Continuous deployment workflow.

**Stages**:
1. Build and push images
2. Deploy to staging
3. Run acceptance tests
4. Deploy to production (manual gate)

**Checklist**:
- [ ] Create image build/push job
- [ ] Create staging deployment job
- [ ] Create production deployment job
- [ ] Add approval requirement

---

### 2.4.E — Security & Documentation

---

#### [NEW] `docs/API.md`

**Purpose**: API documentation for developers.

**Checklist**:
- [ ] Document authentication
- [ ] Document all endpoints
- [ ] Add example requests/responses
- [ ] Add error code reference

---

#### [MODIFY] `README.md`

**Purpose**: Update with production deployment instructions.

**Checklist**:
- [ ] Add Kubernetes deployment section
- [ ] Add environment variable reference
- [ ] Add troubleshooting section

---

## Verification Plan

### Automated Tests (CI)

| Test Suite | Command | Purpose |
|:-----------|:--------|:--------|
| Unit Tests | `poetry run pytest tests/unit -v` | Domain/Application logic |
| Integration Tests | `poetry run pytest tests/integration -v` | DB/Redis/API integration |
| Lint | `poetry run black --check . && poetry run isort --check .` | Code style |
| Type Check | `poetry run mypy src` | Type safety |

### Manual Verification

1. **API Smoke Test**:
   ```bash
   # Start infrastructure
   docker-compose up -d postgres redis
   
   # Run migrations
   cd orchestrator && poetry run alembic upgrade head
   
   # Start API
   poetry run uvicorn src.industrial_orchestrator.presentation.api.main:app --reload
   
   # Test health endpoint
   curl http://localhost:8000/health
   ```

2. **Session Lifecycle Test**:
   ```bash
   # Create session
   curl -X POST http://localhost:8000/api/v1/sessions \
     -H "Content-Type: application/json" \
     -d '{"title": "TEST-Session-001", "initial_prompt": "Test task"}'
   
   # Start session
   curl -X POST http://localhost:8000/api/v1/sessions/{id}/start
   
   # Complete session
   curl -X POST http://localhost:8000/api/v1/sessions/{id}/complete \
     -d '{"result": {"success": true}}'
   ```

3. **Dashboard Verification**:
   ```bash
   cd dashboard
   npm run dev
   # Open http://localhost:3000 and verify:
   # - Dashboard loads
   # - Sessions table renders
   # - Real-time updates work
   ```

---

## File Summary

### Phase 2.2 Files (15 files)

| Path | Type | Priority |
|:-----|:-----|:--------:|
| `application/ports/repository_ports.py` | New | P1 |
| `application/ports/service_ports.py` | New | P1 |
| `application/dtos/session_dtos.py` | New | P1 |
| `application/dtos/agent_dtos.py` | New | P1 |
| `application/dtos/task_dtos.py` | New | P1 |
| `domain/entities/context.py` | New | P2 |
| `domain/exceptions/context_exceptions.py` | New | P2 |
| `infrastructure/repositories/agent_repository.py` | New | P1 |
| `infrastructure/repositories/context_repository.py` | New | P2 |
| `application/services/agent_management_service.py` | New | P1 |
| `application/services/context_service.py` | New | P2 |
| `presentation/api/main.py` | New | P1 |
| `presentation/api/routers/sessions.py` | New | P1 |
| `presentation/api/routers/agents.py` | New | P1 |
| `presentation/api/routers/tasks.py` | New | P1 |
| `presentation/api/dependencies.py` | New | P1 |

### Phase 2.3 Files (20+ files)

Dashboard initialization and components (see detailed breakdown above).

### Phase 2.4 Files (10 files)

Kubernetes, CI/CD, and observability (see detailed breakdown above).

---

## Execution Timeline (Recommended)

| Week | Phase | Focus |
|:----:|:------|:------|
| 2 | 2.2.A-B | Ports, DTOs, API scaffolding, Session endpoints |
| 3 | 2.2.C-E | Agent/Context services, remaining endpoints, tests |
| 4 | 2.3.A-B | WebSocket backend, Next.js foundation |
| 5 | 2.3.C-D | Dashboard pages and real-time integration |
| 6 | 2.4 | Production hardening, CI/CD, documentation |

---

*Document generated based on codebase analysis and validation report from 2026-02-03.*
