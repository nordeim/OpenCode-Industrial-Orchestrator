/**
 * API MODULE INDEX
 * 
 * Exports all API client utilities and hooks.
 */

// Client
export { api, ApiError, API_BASE_URL } from "./client";

// Types
export type * from "./types";

// Hooks - Sessions
export {
    sessionKeys,
    useSessions,
    useSession,
    useSessionStatistics,
    useCreateSession,
    useStartSession,
    usePauseSession,
    useResumeSession,
    useCancelSession,
    useCompleteSession,
    type SessionFilters,
} from "./sessions";

// Hooks - Agents
export {
    agentKeys,
    useAgents,
    useAgent,
    useAgentPerformance,
    useRegisterAgent,
    useDeregisterAgent,
    useAgentHeartbeat,
    type AgentFilters,
} from "./agents";

// Hooks - Tasks
export {
    taskKeys,
    useTasks,
    useTask,
    useTasksBySession,
    useCreateTask,
    useUpdateTaskStatus,
    useDecomposeTask,
    useAssignTask,
    type TaskFilters,
} from "./tasks";
