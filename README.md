<img width="1352" height="686" alt="image" src="https://github.com/user-attachments/assets/d89018ed-4619-48a1-8880-da5161c817f1" />

<p align="center">
  <img src="https://img.shields.io/badge/🔧-INDUSTRIAL_ORCHESTRATOR-000000?style=for-the-badge&labelColor=FFFFFF" alt="Industrial Orchestrator"/>
</p>

<p align="center">
  <strong>"Industrial Cybernetics"</strong> — A utilitarian, transparent orchestration interface<br/>prioritizing ruthless efficiency, visibility, and graceful degradation.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Phase_2.4_Complete-brightgreen?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/Tests-321_Passing-success?style=flat-square" alt="Tests"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Architecture-Hexagonal-7B4EA8?style=flat-square" alt="Architecture"/>
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License"/>
</p>

---

## 🎯 Why This Project?

Modern AI agents can write code, but **who orchestrates the agents?**

The **OpenCode Industrial Orchestrator** is the missing control plane for autonomous development. It provides:

| Challenge | Solution |
|:----------|:---------|
| **Agent Chaos** | Centralized registry with capability-based routing |
| **Lost Context** | Shared execution context with conflict detection |
| **Task Complexity** | Intelligent decomposition using proven templates |
| **Blind Debugging** | "Glass Box" monitoring with real-time WebSocket updates |
| **Infrastructure Fragility** | Distributed locking, circuit breakers, graceful degradation |

---

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🧠 Multi-Agent Intelligence
- **Agent Registry** — Dynamic registration and discovery
- **Capability Routing** — Match tasks to specialist agents
- **Performance Tiers** — Promote/demote based on success
- **Load Balancing** — Prevent overloading any single agent

</td>
<td width="50%">

### 📋 Task Decomposition
- **Heuristic Analysis** — Estimate complexity from requirements
- **Templates** — Microservice, CRUD, Security patterns
- **Dependency DAG** — Topological ordering with cycle detection
- **Critical Path** — Identify bottlenecks automatically

</td>
</tr>
<tr>
<td width="50%">

### 🔒 Industrial Resilience
- **Distributed Locking** — Fair queues with TTL
- **Circuit Breakers** — Fail fast, recover smart
- **Optimistic Locking** — Concurrent session safety
- **Soft Deletion** — Recovery from accidents

</td>
<td width="50%">

### 👁️ Glass Box Monitoring
- **Session State Machine** — Rigid, validated transitions
- **Real-time WebSocket** — Subscribe to session events
- **Execution Metrics** — Track duration, tokens, quality
- **Checkpoint Recovery** — Resume from last known state

</td>
</tr>
</table>

---

## 🏗️ Architecture

The system follows **Hexagonal Architecture** (Ports & Adapters) for maximum testability and domain isolation.

```mermaid
graph LR
    User[👨‍💻 Developer] -->|REST/WS| API[Orchestrator API]
    
    subgraph "Core Domain"
        API --> Services[Services Layer]
        Services --> Entities[Domain Entities]
    end
    
    subgraph "Infrastructure"
        Services -->|Persist| PG[(PostgreSQL)]
        Services -->|Coordinate| Redis[(Redis)]
        Services -->|Delegate| OpenCode[OpenCode API]
    end
    
    OpenCode --> Agents[🤖 Specialized Agents]
    
    style User fill:#fff,stroke:#333,stroke-width:2px
    style PG fill:#336791,stroke:#333,color:#fff
    style Redis fill:#D82C20,stroke:#333,color:#fff
```

### Layer Responsibilities

| Layer | Purpose | Examples |
|:------|:--------|:---------|
| **Domain** | Pure business logic, no I/O | `SessionEntity`, `TaskEntity`, `AgentRegistry` |
| **Application** | Orchestration, use cases | `SessionService`, `TaskDecompositionService` |
| **Infrastructure** | External adapters | `SessionRepository`, `DistributedLock` |
| **Presentation** | Entry points | REST API, WebSocket, CLI |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Poetry (`pip install poetry`)
- Node.js 18.17+ (for dashboard)

### 1. Start Infrastructure
```bash
docker-compose up -d postgres redis opencode-server
```

### 2. Install & Run Backend
```bash
cd orchestrator
poetry install
poetry run alembic upgrade head
poetry run uvicorn src.industrial_orchestrator.presentation.api.main:app --reload
```

### 3. Run Tests
```bash
poetry run pytest  # 321 tests
```

### 4. Start Dashboard (Optional)
```bash
cd dashboard
npm install
npm run dev
```

---

## 📡 API Reference

### REST Endpoints

```
POST   /api/v1/sessions              Create session
GET    /api/v1/sessions              List sessions
GET    /api/v1/sessions/{id}         Get session
POST   /api/v1/sessions/{id}/start   Start execution
POST   /api/v1/sessions/{id}/complete Mark complete

POST   /api/v1/agents                Register agent
GET    /api/v1/agents                List agents
POST   /api/v1/agents/route          Route task to agent

POST   /api/v1/tasks                 Create task
POST   /api/v1/tasks/{id}/decompose  Decompose into subtasks

POST   /api/v1/contexts              Create context
POST   /api/v1/contexts/merge        Merge contexts
```

### WebSocket Endpoints

```
WS     /ws/sessions                  All session events
WS     /ws/sessions/{id}             Specific session events
```

---

## 📂 Project Structure

```
opencode-industrial-orchestrator/
├── orchestrator/                     # Python Backend
│   ├── src/industrial_orchestrator/
│   │   ├── domain/                   # 🧠 Business Logic
│   │   │   ├── entities/             # Session, Agent, Task, Context
│   │   │   ├── value_objects/        # Status, Metrics
│   │   │   └── exceptions/           # Domain errors
│   │   ├── application/              # ⚙️ Services
│   │   │   ├── services/             # Session, Agent, Context, Task
│   │   │   ├── ports/                # Abstract interfaces
│   │   │   └── dtos/                 # Request/Response objects
│   │   ├── infrastructure/           # 🔌 Adapters
│   │   │   ├── repositories/         # PostgreSQL, Redis
│   │   │   └── locking/              # Distributed locks
│   │   └── presentation/             # 🖥️ Entry Points
│   │       ├── api/                  # FastAPI routers
│   │       └── websocket/            # Real-time events
│   ├── tests/                        # 321 unit & integration tests
│   └── alembic/                      # Database migrations
│
├── dashboard/                        # Next.js Frontend
│   └── src/                          # React components
│
└── infrastructure/                   # Docker & Monitoring
```

---

## 🧪 Testing

We practice **Test-Driven Development (TDD)** religiously.

| Component | Tests |
|:----------|------:|
| Session Entity | 42 |
| Agent Entity | 54 |
| Task Entity | 53 |
| Context Entity | 39 |
| Task Decomposition Service | 24 |
| Integration & Infrastructure | ~109 |
| **Total** | **321** |

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Run specific test file
poetry run pytest tests/unit/domain/test_session_entity.py
```

---

## ⚙️ Configuration

| Variable | Description | Default |
|:---------|:------------|:--------|
| `DB_HOST` | PostgreSQL host | `postgres` |
| `REDIS_HOST` | Redis host | `redis` |
| `OPENCODE_HOST` | OpenCode API host | `opencode-server` |
| `MAX_CONCURRENT_SESSIONS` | Parallel execution limit | `25` |
| `SESSION_TIMEOUT_SECONDS` | Hard timeout per session | `3600` |

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **TDD is mandatory** — Write tests before implementation
2. **Hexagonal imports** — Domain never imports from Infrastructure
3. **Code style** — Run `black`, `isort`, and `flake8`
4. **Database changes** — Always use Alembic migrations

### Development Workflow
```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Write tests first
poetry run pytest tests/unit/your_test.py

# 3. Implement
# ... write code ...

# 4. Verify all tests pass
poetry run pytest

# 5. Submit PR
```

---

## 📋 Roadmap

- [x] **Phase 2.1** — Foundation & Core Orchestrator
- [x] **Phase 2.2** — Multi-Agent Intelligence (212 tests ✅)
- [x] **Phase 2.3** — Dashboard & Visualization ("Glass Box" Interface ✅)
- [x] **Phase 2.4** — Production Hardening (Kubernetes, CI/CD, Observability ✅)

---

## 📜 License

MIT License — See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with 🔧 industrial-grade precision</sub>
</p>