# CLAUDE.md — Agent Briefing Document

> **Single Source of Truth** for AI coding agents and human developers
> **Last Updated:** February 4, 2026  
> **Status:** Phase 3.3 Complete (Multi-Tenant Enterprise Platform)

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
| 2.3 | Dashboard & Visualization | ✅ Complete | — |
| 2.4 | Production Hardening | ✅ Complete | 109 |
| 3.1 | Agent Marketplace (EAP Integration) | ✅ Complete | 8 |
| 3.2 | LLM Fine-Tuning Pipeline | ✅ Complete | 6 |
| 3.3 | Multi-Tenant Isolation | ✅ Complete | 2 |

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
| Frontend | Next.js 16 + Tailwind CSS 4.0 |

---

## 📂 Project Structure

```
orchestrator/src/industrial_orchestrator/
├── domain/                           # 🧠 PURE BUSINESS LOGIC
│   ├── entities/
│   │   ├── session.py               # SessionEntity (tenant isolated)
│   │   ├── agent.py                 # AgentEntity (tenant isolated)
│   │   ├── fine_tuning.py           # FineTuningJob (lifecycle tracking)
│   │   ├── tenant.py                # Tenant (quotas & settings)
│   │   └── user.py                  # User (RBAC & identity)
│   ├── value_objects/
│   │   ├── session_status.py        # 12 states, state machine
│   │   └── model_version.py         # Semantic versioning
│   └── exceptions/
│       ├── session_exceptions.py
│       ├── tenant_exceptions.py     # Quota exceeded errors
│       └── fine_tuning_exceptions.py
│
├── application/                      # ⚙️ ORCHESTRATION LOGIC
│   ├── services/
│   │   ├── session_service.py       # Quota enforcement & dispatch
│   │   ├── fine_tuning_service.py   # Training orchestration
│   │   ├── dataset_curator_service.py # Log extraction (JSONL)
│   │   └── tenant_service.py        # Onboarding & RBAC
│   ├── ports/
│   │   ├── repository_ports.py      # Repository ABCs
│   │   └── service_ports.py         # TrainingProviderPort, ExternalAgentPort
│   └── dtos/
│       ├── session_dtos.py          # Request/Response DTOs
│       ├── fine_tuning_dtos.py      # Job creation & results
│       └── external_agent_protocol.py
│
├── infrastructure/                       # 🔌 ADAPTERS
│   ├── repositories/
│   │   ├── session_repository.py    # Auto-tenant filtering
│   │   ├── fine_tuning_repository.py # Job persistence
│   │   └── base.py                  # Generic Unit of Work
│   ├── locking/
│   │   └── distributed_lock.py      # Redis fair locking
│   ├── adapters/
│   │   ├── eap_agent_adapter.py     # Outbound EAP HTTP
│   │   └── simulated_training_provider.py # Async training simulation
│   └── database/
│       └── models.py                # Multi-tenant schema
│
└── presentation/                     # 🖥️ ENTRY POINTS
    └── api/
        ├── main.py                   # FastAPI app factory
        ├── middleware/
        │   └── tenant.py             # X-Tenant-ID context provider
        ├── routers/
        │   ├── sessions.py
        │   ├── fine_tuning.py        # /api/v1/fine-tuning
        │   └── external_agents.py
        └── websocket/
            ├── connection_manager.py
            └── session_events.py

dashboard/                            # Next.js Frontend
└── src/                              # Marketplace & Model Registry UI
```

---

## 🧠 Domain Entities (Core Business Logic)

### SessionEntity
**Location:** `domain/entities/session.py`

```python
class SessionEntity(BaseModel):
    id: UUID
    tenant_id: UUID                   # Mandatory isolation
    title: str                        # Industrial naming (IND-*)
    status: SessionStatus             # 12 possible states
    priority: SessionPriority         # CRITICAL (0) to DEFERRED (4)
```

**Key Methods:**
- `transition_to(new_status)` — Validated state transition
- `start_execution()` — PENDING → RUNNING
- `is_recoverable()` — Check if retry is possible

### Tenant & User
**Location:** `domain/entities/tenant.py`, `user.py`

```python
class Tenant(BaseModel):
    id: UUID
    slug: str                         # unique identifier for URL/headers
    max_concurrent_sessions: int      # Active quota enforcement

class User(BaseModel):
    id: UUID
    tenant_id: UUID
    role: Role                        # ADMIN, LEAD, MEMBER, VIEWER
```

### FineTuningJob
**Location:** `domain/entities/fine_tuning.py`

```python
class FineTuningJob(BaseModel):
    id: UUID
    status: FineTuningStatus          # PENDING, QUEUED, RUNNING, COMPLETED...
    base_model: str
    target_model_name: str
    version: ModelVersion             # semantic versioning
    parameters: TrainingParameters    # LoRA rank, alpha, etc.
```

---

## ⚙️ Application Services

### SessionService
**Location:** `application/services/session_service.py`

| Method | Description |
|:-------|:------------|
| `create_session(...)` | Create with **Quota Enforcement** |
| `execute_session(id)` | Dispatch to **Internal or External** agent |
| `fail_session(id, error)` | Mark failed with audit trail |

### FineTuningService
**Location:** `application/services/fine_tuning_service.py`

| Method | Description |
|:-------|:------------|
| `start_pipeline(job_id)` | Curate dataset -> Submit training |
| `poll_jobs()` | Sync state with training provider |

---

## 🔌 API Endpoints

### REST API

```
POST   /api/v1/sessions              Create (X-Tenant-ID required)
POST   /api/v1/sessions/{id}/start   Execute workflow

POST   /api/v1/agents/external/register Register via EAP
POST   /api/v1/agents/external/{id}/heartbeat Sync load status

POST   /api/v1/fine-tuning/jobs      Configure training
POST   /api/v1/fine-tuning/jobs/poll Trigger status sync

GET    /health                       System pulse
GET    /ready                        Readiness (Postgres + Redis)
```

### WebSocket

```
WS     /ws/sessions                  Real-time activity stream
```

---

## 🧪 Testing

### Test Statistics
- **Total Tests:** 337
- **Architecture Score:** 10/10 (Zero Hexagonal Violations)
- **Coverage:** High across domain logic and infrastructure adapters.

### Commands
```bash
# All tests
poetry run pytest

# With Tenant Context (Manual test)
curl -H "X-Tenant-ID: <uuid>" http://localhost:8000/api/v1/sessions
```

---

## 🚧 Remaining Work

### Future Roadmap (Phase 4.0)
- [ ] Automated A/B Testing for fine-tuned models
- [ ] Billing & Usage Metering
- [ ] Advanced Topology Visualization (Recursive tasks)

---

## ⚠️ Known Issues & Gotchas

1. **Tenant ID:** All creation requests MUST include a valid `X-Tenant-ID` UUID header.
2. **LoRA Defaults:** Fine-tuning defaults to Rank 8 unless specified in `TrainingParameters`.
3. **Async Collection:** Pytest collection requires `email-validator` for `User` entity schemas.

---

## 📚 Key Documentation

| Document | Purpose |
|:---------|:--------|
| `README.md` | Project overview & feature set |
| `Project_Architecture_Document.md` | Detailed Hexagonal map & flow diagrams |
| `MASTER_EXECUTION_PLAN.md` | Phase-by-phase roadmap |

---

> **Remember:** This is an industrial-grade enterprise system. Isolation is absolute, performance is tracked, and every model improvement is versioned. Build for scale.