# Industrial Orchestrator API Documentation

> Version: 1.0.0 | Base URL: `/api/v1`

## Overview

The Industrial Orchestrator API provides programmatic access to manage autonomous coding sessions, agents, and tasks. All endpoints return JSON and follow RESTful conventions.

---

## Authentication

> **Note**: Authentication is optional in development mode. Production deployments should enable JWT authentication.

```http
Authorization: Bearer <jwt_token>
```

---

## Endpoints

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health status |
| GET | `/ready` | Readiness check (for K8s) |

---

### Sessions

#### List Sessions

```http
GET /api/v1/sessions
```

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `status` | string | Filter by status (PENDING, RUNNING, COMPLETED, FAILED) |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "Session-Alpha-001",
      "status": "RUNNING",
      "type": "CODING",
      "priority": "HIGH",
      "created_at": "2026-02-03T10:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

#### Create Session

```http
POST /api/v1/sessions
```

**Request Body:**
```json
{
  "title": "Session-Alpha-001",
  "type": "CODING",
  "priority": "HIGH",
  "initial_prompt": "Implement user authentication"
}
```

#### Get Session

```http
GET /api/v1/sessions/{id}
```

#### Session Actions

```http
POST /api/v1/sessions/{id}/start
POST /api/v1/sessions/{id}/pause
POST /api/v1/sessions/{id}/resume
POST /api/v1/sessions/{id}/cancel
POST /api/v1/sessions/{id}/complete
```

---

### Agents

#### List Agents

```http
GET /api/v1/agents
```

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `capability` | string | Filter by capability |
| `available_only` | bool | Only return available agents |

#### Register Agent

```http
POST /api/v1/agents/register
```

**Request Body:**
```json
{
  "name": "AGENT-BACKEND-001",
  "type": "BACKEND",
  "capabilities": ["CODE_GENERATION", "DEBUGGING"],
  "max_concurrent_tasks": 5
}
```

#### Agent Heartbeat

```http
POST /api/v1/agents/{id}/heartbeat
```

**Request Body:**
```json
{
  "current_load": 65
}
```

---

### Tasks

#### List Tasks

```http
GET /api/v1/tasks
```

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `session_id` | uuid | Filter by session |
| `status` | string | Filter by status |
| `parent_only` | bool | Only return root tasks |

#### Create Task

```http
POST /api/v1/tasks
```

**Request Body:**
```json
{
  "session_id": "uuid",
  "title": "Implement login endpoint",
  "description": "Create POST /auth/login",
  "complexity": "MEDIUM"
}
```

#### Decompose Task

```http
POST /api/v1/tasks/{id}/decompose
```

**Request Body:**
```json
{
  "template": "MICROSERVICE"
}
```

---

## WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/sessions/{id}` | Session-specific events |
| `/ws/sessions` | All session events |
| `/ws/agents/{id}` | Agent-specific events |
| `/ws/agents` | All agent events |
| `/ws/system` | System health events |

**Message Format:**
```json
{
  "type": "session.status_changed",
  "payload": { "session_id": "uuid", "status": "RUNNING" },
  "timestamp": "2026-02-03T10:00:00Z"
}
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `SESSION_NOT_FOUND` | 404 | Session does not exist |
| `INVALID_TRANSITION` | 400 | Invalid status transition |
| `AGENT_UNAVAILABLE` | 503 | No agents available |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

**Error Response:**
```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session with ID xyz not found",
    "request_id": "abc123"
  }
}
```

---

## Rate Limits

- **Standard**: 60 requests/minute
- **WebSocket**: 5 connections/client

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `API_SECRET_KEY` | Yes | API signing key |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
