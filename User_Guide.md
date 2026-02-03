# User Guide — OpenCode Industrial Orchestrator

> **"Industrial Cybernetics"** — A manual for the operation, monitoring, and control of the OpenCode Orchestration System.

---

## 1. Introduction

The **OpenCode Industrial Orchestrator** is a production-grade control plane for autonomous AI coding agents. Unlike chat-based interfaces or fragile scripts, this system treats code generation as an **industrial process**:

*   **Deterministic:** Defined states (`PENDING` → `RUNNING` → `COMPLETED`).
*   **Resilient:** Distributed locking and automatic checkpointing.
*   **Observable:** A "Glass Box" dashboard providing real-time telemetry into agent thought processes.

This guide covers the installation, usage, and operational monitoring of the system.

---

## 2. Quick Start

### Prerequisites
*   **Docker** & **Docker Compose** (Recommended)
*   *Alternatively:* Python 3.11+, Node.js 18+, PostgreSQL 15, Redis 7

### Installation & Startup

The fastest way to spin up the entire stack (Orchestrator, Dashboard, Database, Cache) is via Docker Compose.

```bash
# 1. Clone the repository
git clone https://github.com/your-org/opencode-industrial-orchestrator.git
cd opencode-industrial-orchestrator

# 2. Start the infrastructure
docker-compose up -d

# 3. Access the interfaces
# Dashboard: http://localhost:3000
# API Docs:  http://localhost:8000/docs
```

---

## 3. The "Glass Box" Dashboard

The Dashboard is your primary interface for command and control. It utilizes a **Brutalist / Industrial** aesthetic designed for high information density and low cognitive load.

### A. System Overview (`/`)
The landing page provides a high-level situational report (SITREP) of the orchestration cluster.
*   **Session Metrics:** Real-time counters for Running, Pending, Completed, and Failed sessions.
*   **Agent Status:** Gauge showing total vs. active agents to identify capacity bottlenecks.
*   **Recent Activity:** A quick-access log of the latest session state changes.

### B. Session Management (`/sessions`)
The central command list for all coding tasks.
*   **Filtering:** Use the status chips (`RUNNING`, `FAILED`, etc.) to filter the view.
*   **Pagination:** Navigate through historical session data.
*   **Creation:** Click **+ NEW SESSION** to dispatch a new coding task. You will provide:
    *   **Title:** A human-readable identifier (e.g., "Refactor Auth Middleware").
    *   **Initial Prompt:** The high-level instruction for the Architect Agent.
    *   **Priority:** `LOW` to `CRITICAL`.

### C. The Session Detail View (`/sessions/[id]`)
This is the core "Glass Box" interface. It provides total transparency into a running session.

| Component | Function |
|:----------|:---------|
| **Header Controls** | **Start**, **Stop**, and **Retry** buttons. Status badges update in real-time. |
| **Live Terminal** | A raw, scrolling feed of agent logs, internal monologues, and tool outputs via WebSocket. |
| **Telemetry** | Live gauges for **Tokens Used**, **Success Rate**, and **Duration**. |
| **Checkpoint Timeline** | A vertical history of state saves. Shows exactly when and why the system saved its state (e.g., "After Tool Use", "Periodic"). |

### D. Agent Fleet (`/agents`)
Monitor the workforce.
*   **Load Gauges:** Visual representation of each agent's current load (0-100%).
*   **Performance Tiers:** Agents are classified as `ELITE`, `STANDARD`, or `PROBATION` based on their success rates.
*   **Capabilities:** View which agents handle `CODE_GENERATION` vs. `SECURITY_AUDIT`.

### E. Task Decomposition (`/tasks`)
Visualize the work breakdown structure.
*   **Task Tree:** Recursive visualization of how the Orchestrator broke down a high-level prompt into atomic subtasks.
*   **Status Tracking:** See which specific subtask is blocking progress.

---

## 4. Operational Concepts

### Sessions
A **Session** is the fundamental unit of work. It represents a single goal (e.g., "Build a Login Page").
*   **State Machine:** Sessions move through a rigid state machine. They cannot be "Stopped" if they are already "Completed".
*   **Persistence:** If the server crashes, the session resumes from the last **Checkpoint** automatically.

### Agents
**Agents** are specialized workers registered in the system.
*   **Routing:** The system automatically routes tasks to the best available agent based on **Capabilities** and **Load**.
*   **Heartbeats:** Agents must send periodic heartbeats. If an agent goes silent, it is marked `OFFLINE` and its tasks are re-queued.

### Context
**Context** is the shared memory between agents.
*   **Scopes:** Data can be scoped to a `SESSION`, a specific `TASK`, or `GLOBAL` (system-wide).
*   **Conflict Resolution:** The system handles merging data when multiple agents update context simultaneously.

---

## 5. API Interaction

For automated workflows or CI/CD integration, use the REST API.

**Base URL:** `http://localhost:8000/api/v1`

### Key Endpoints

*   **Create Session:** `POST /sessions`
*   **Start Session:** `POST /sessions/{id}/start`
*   **Get Session Status:** `GET /sessions/{id}`
*   **Register Agent:** `POST /agents`

Full Swagger documentation is available at `http://localhost:8000/docs`.

---

## 6. Observability & Monitoring

For production environments, we expose industry-standard metrics.

### Prometheus Metrics
The API exposes a `/metrics` endpoint for scraping.
*   `orchestrator_active_sessions`: Gauge of concurrent sessions.
*   `orchestrator_tasks_total`: Counter of tasks processed.
*   `http_request_duration_seconds`: API latency histograms.

### Logging
All logs are emitted in **Structured JSON** format to stdout, making them ready for ingestion by log aggregators (Elasticsearch, Datadog, Splunk).

```json
{
  "timestamp": "2024-02-03T12:00:00Z",
  "level": "info",
  "event": "session_started",
  "session_id": "1234-5678",
  "logger": "industrial_orchestrator.services.session"
}
```

---

## 7. Troubleshooting

**Issue: Dashboard shows "Uplink Failed"**
*   **Check:** Is the backend API running? (`docker ps`)
*   **Check:** Are you on the same network? The dashboard attempts to connect to `ws://localhost:8000`.

**Issue: Session stuck in `PENDING`**
*   **Check:** Did you click "Start Execution"? Sessions are created in a paused state by default.
*   **Check:** Are there available agents with the required capabilities?

**Issue: Agents not appearing**
*   **Check:** Verify Redis connection. The Agent Registry relies on Redis for discovery.
