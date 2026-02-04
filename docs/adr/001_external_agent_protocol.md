# ADR 001: External Agent Protocol (EAP) v1.0

## Status
Accepted

## Date
2026-02-04

## Context
The OpenCode Industrial Orchestrator currently manages internal agents via the `AgentManagementService`. To scale the ecosystem (Phase 3.0), we need to support **External Agents**—autonomous agents running outside the orchestrator's process boundary (e.g., as microservices, Lambda functions, or sidecars) or installed as plugins.

We need a standardized, language-agnostic protocol to allow these agents to:
1.  Register their capabilities.
2.  Receive task assignments.
3.  Report execution results and metrics.
4.  Maintain heartbeat/health status.

## Decision
We will implement the **External Agent Protocol (EAP)**, a JSON-over-HTTP (REST webhook) and/or WebSocket-based standard.

### Core Principles
1.  **Agent-Initiated Registration**: Agents "phone home" to register.
2.  **Pull-Based Tasking** (or Push via WebSocket): Agents request work or receive events.
3.  **Schema Enforcement**: Strict Pydantic/JSON Schema validation for all payloads.
4.  **Stateless Interaction**: The orchestrator holds the state; the agent is an execution unit.

### Protocol Specification

#### 1. Registration (`POST /api/v1/agents/external/register`)
Payload:
```json
{
  "protocol_version": "1.0",
  "name": "AGENT-EXT-PYTHON-01",
  "version": "1.2.0",
  "capabilities": ["code_generation", "python_expert"],
  "endpoint_url": "http://agent-service:8080",  // For webhooks
  "metadata": {
    "maintainer": "OpenCode Team",
    "runtime": "python:3.11"
  }
}
```

#### 2. Heartbeat (`POST /api/v1/agents/external/{id}/heartbeat`)
Payload:
```json
{
  "status": "healthy", // or "degraded", "busy"
  "current_load": 0.5,
  "metrics": {
    "memory_usage": 128,
    "uptime_seconds": 3600
  }
}
```

#### 3. Task Assignment (Orchestrator -> Agent)
Payload:
```json
{
  "task_id": "uuid",
  "context": { ... },
  "input": "Write a FastAPI router...",
  "requirements": ["fastapi", "pydantic"]
}
```

#### 4. Task Result (Agent -> Orchestrator)
Payload:
```json
{
  "task_id": "uuid",
  "status": "completed", // "failed"
  "artifacts": [
    {"path": "router.py", "content": "..."}
  ],
  "metrics": {
    "execution_time_ms": 1500,
    "tokens_used": 450
  }
}
```

## Consequences
### Positive
- **Decoupling**: Agents can be written in any language (Rust, Go, JS) as long as they speak EAP.
- **Scalability**: Agents can scale independently of the orchestrator.
- **Resilience**: A crashing external agent does not bring down the orchestrator.

### Negative
- **Network Latency**: Introduces HTTP/WS overhead compared to in-process calls.
- **Complexity**: Requires authentication and failure handling for network requests.

## Implementation Plan
1.  Define Pydantic models for EAP payloads.
2.  Implement `ExternalAgentRepository` adapter.
3.  Expose API endpoints for external registration.
