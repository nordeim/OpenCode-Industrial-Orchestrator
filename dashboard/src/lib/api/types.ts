/**
 * INDUSTRIAL API TYPES
 * 
 * TypeScript types matching backend DTOs.
 */

// ============================================================================
// SESSION TYPES
// ============================================================================

export type SessionStatus =
    | "PENDING"
    | "QUEUED"
    | "RUNNING"
    | "PAUSED"
    | "COMPLETED"
    | "FAILED"
    | "CANCELLED";

export type SessionType = "CODING" | "DEBUGGING" | "REFACTORING" | "TESTING" | "DOCUMENTATION";

export type SessionPriority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export interface Session {
    id: string;
    title: string;
    status: SessionStatus;
    type: SessionType;
    priority: SessionPriority;
    initial_prompt?: string;
    parent_session_id?: string;
    created_at: string;
    updated_at: string;
    started_at?: string;
    completed_at?: string;
    metrics?: ExecutionMetrics;
}

export interface ExecutionMetrics {
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    execution_time_ms: number;
    tokens_used: number;
}

export interface CreateSessionRequest {
    title: string;
    type?: SessionType;
    priority?: SessionPriority;
    initial_prompt?: string;
    parent_session_id?: string;
}

export interface SessionListResponse {
    items: Session[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

export interface SessionStatistics {
    total: number;
    by_status: Record<SessionStatus, number>;
    avg_completion_time_ms: number;
    success_rate: number;
}

// ============================================================================
// AGENT TYPES
// ============================================================================

export type AgentType = "BACKEND" | "FRONTEND" | "FULLSTACK" | "DEVOPS" | "QA" | "SECURITY";

export type AgentStatus = "ACTIVE" | "IDLE" | "BUSY" | "DEGRADED" | "OFFLINE";

export type AgentCapability =
    | "CODE_GENERATION"
    | "CODE_REVIEW"
    | "DEBUGGING"
    | "REFACTORING"
    | "TESTING"
    | "DOCUMENTATION"
    | "SECURITY_AUDIT"
    | "PERFORMANCE_OPTIMIZATION";

export type PerformanceTier = "ELITE" | "STANDARD" | "PROBATION";

export interface Agent {
    id: string;
    name: string;
    type: AgentType;
    status: AgentStatus;
    capabilities: AgentCapability[];
    tier: PerformanceTier;
    current_load: number;
    max_concurrent_tasks: number;
    tasks_completed: number;
    success_rate: number;
    registered_at: string;
    last_heartbeat: string;
}

export interface RegisterAgentRequest {
    name: string;
    type: AgentType;
    capabilities: AgentCapability[];
    max_concurrent_tasks?: number;
}

export interface EAPRegistrationRequest {
    protocol_version: string;
    name: string;
    version: string;
    agent_type: string;
    capabilities: string[];
    endpoint_url?: string;
    metadata: Record<string, unknown>;
}

export interface EAPRegistrationResponse {
    agent_id: string;
    status: string;
    auth_token: string;
    heartbeat_interval_seconds: number;
}

export interface AgentListResponse {
    items: Agent[];
    total: number;
}

export interface AgentPerformanceSummary {
    total_agents: number;
    active_agents: number;
    avg_success_rate: number;
    total_tasks_completed: number;
    by_tier: Record<PerformanceTier, number>;
}

// ============================================================================
// TASK TYPES
// ============================================================================

export type TaskStatus =
    | "PENDING"
    | "QUEUED"
    | "IN_PROGRESS"
    | "COMPLETED"
    | "FAILED"
    | "CANCELLED"
    | "BLOCKED";

export type TaskComplexity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface Task {
    id: string;
    session_id: string;
    parent_task_id?: string;
    title: string;
    description?: string;
    status: TaskStatus;
    complexity: TaskComplexity;
    assigned_agent_id?: string;
    subtask_count: number;
    completed_subtasks: number;
    created_at: string;
    started_at?: string;
    completed_at?: string;
}

export interface CreateTaskRequest {
    session_id: string;
    title: string;
    description?: string;
    complexity?: TaskComplexity;
    parent_task_id?: string;
}

export interface TaskListResponse {
    items: Task[];
    total: number;
}

export interface TaskDecompositionResult {
    parent_task_id: string;
    subtasks: Task[];
    template_used: string;
}

// ============================================================================
// CONTEXT TYPES
// ============================================================================

export type ContextScope = "SESSION" | "TASK" | "AGENT" | "GLOBAL";

export interface Context {
    id: string;
    name: string;
    scope: ContextScope;
    owner_id: string;
    data: Record<string, unknown>;
    version: number;
    created_at: string;
    updated_at: string;
}

// ============================================================================
// HEALTH TYPES
// ============================================================================

export interface HealthStatus {
    status: "healthy" | "degraded" | "unhealthy";
    version: string;
    components: {
        database: string;
        redis: string;
        agents: string;
    };
}

export interface ReadinessStatus {
    ready: boolean;
    components: {
        database: { ready: boolean };
        redis: { ready: boolean };
    };
}
